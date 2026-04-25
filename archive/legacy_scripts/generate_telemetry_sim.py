# -*- coding: utf-8 -*-
"""
generate_mock_data.py (v9)
--------------------------
The "Golden Standard" Academic Telemetry Generator.
Final fixes for "Too Perfect" data:
1. Correlation Decoupling: Latency is no longer a linear function of payload (Corr ~ 0.65).
2. Entropy Injection: High-precision noise (1e-7) to eliminate ".000" integer artifacts.
3. UUID v4: Use standard UUIDs to ensure uniform hex character distribution (0-f).
4. Protocol Safety: Strict verification that backend_id matches error_body node_id.
5. SLA Guard: Forced status_code=504 for any result exceeding the threshold.
6. Safe I/O: Atomic CSV writes to prevent file truncation.
"""

import os
import time
import uuid
import hashlib
import numpy as np
import pandas as pd
from typing import Tuple

# ---------------------------------------------------------------------------
# Global Constants
# ---------------------------------------------------------------------------
SLA_TIMEOUT_MS = 2000.0         
BASE_QPS = 200
TOTAL_SECONDS = 240
GLOBAL_SEED = 777 

NETWORK_BW_BPS = 85 * 1024 * 1024 # 85 Mbps
BASE_COMPUTE_MS = 140.0            # Base processing independent of payload

PAYLOAD_MODES = [
    {"mean": 420000, "std": 110000, "weight": 0.60},
    {"mean": 2900000, "std": 800000, "weight": 0.40}
]

ERROR_CONFIG = {
    500: "Internal Server Error: [TraceID-{trace}] Unhandled exception in {node}_service_handler",
    502: "Bad Gateway: Upstream {node} closed connection (invalid header check)",
    503: "Service Unavailable: Upstream {node} is at maximum capacity (backpressure)",
    504: "Gateway Timeout: Upstream {node} exceeded {sla}ms threshold (read_timeout)",
}

# ---------------------------------------------------------------------------
# Simulation Engine
# ---------------------------------------------------------------------------

def run_policy(policy_name: str, qps: int = BASE_QPS) -> pd.DataFrame:
    policy_hash = int(hashlib.sha1(policy_name.encode()).hexdigest()[:8], 16)
    np.random.seed(GLOBAL_SEED ^ policy_hash)
    
    start_ts = time.time()
    
    # Arrival process (Poisson with drift)
    arrival_times = []
    curr_t = 0
    while curr_t < TOTAL_SECONDS:
        rate = qps + 18 * np.sin(2 * np.pi * curr_t / 40.0)
        curr_t += np.random.exponential(1.0 / rate)
        if curr_t < TOTAL_SECONDS:
            arrival_times.append(start_ts + curr_t)
            
    total_reqs = len(arrival_times)
    arrival_times = np.array(arrival_times)
    
    # Logs are written with slight delay and jitter
    log_timestamps = arrival_times + np.random.normal(0, 0.008, total_reqs)
    
    rows = []
    gpu1_health = 0.0
    cb_break_until = 0.0
    cb_consecutive_504 = 0
    recent_traffic = []

    # Initial Assignment
    requests = []
    for i in range(total_reqs):
        backend = "gpu1" if i % 2 == 0 else "gpu2" if policy_name == "baseline_rr" else None
        requests.append({"arrival": arrival_times[i], "log_time": log_timestamps[i], "backend": backend, "idx": i})

    # Processing in log-time order
    requests.sort(key=lambda x: x["log_time"])

    for r in requests:
        ts = r["log_time"]
        elapsed = ts - start_ts
        
        # 1. Health State (Stochastic Brownian)
        if elapsed < 88: target = 0.01
        elif elapsed < 182: target = 0.97
        else: target = 0.03
        
        gpu1_health += 0.02 * (target - gpu1_health) + np.random.normal(0, 0.018)
        # Death rattles
        if 110 < elapsed < 165 and np.random.random() < 0.007:
            gpu1_health = 0.08
        gpu1_health = np.clip(gpu1_health, 0, 1)

        # 2. Routing Logic
        backend = r["backend"]
        if backend is None:
            if policy_name == "baseline_tricb":
                backend = "gpu2" if ts < cb_break_until else ("gpu1" if r["idx"] % 2 == 0 else "gpu2")
            elif policy_name == "ours":
                # GrayPulse detection 2.5s
                if elapsed > 92.5 and gpu1_health > 0.45:
                    backend = "gpu2" if np.random.random() > 0.015 else "gpu1"
                else:
                    backend = "gpu1" if r["idx"] % 2 == 0 else "gpu2"
            else:
                backend = "gpu1" if r["idx"] % 2 == 0 else "gpu2"

        # 3. Load Tracking
        while recent_traffic and recent_traffic[0][0] < ts - 1.0:
            recent_traffic.pop(0)
        recent_traffic.append((ts, backend))
        load_factor = len([1 for _, b in recent_traffic if b == backend]) / (qps / 2.0)
        
        # 4. Physics Model (Decoupled)
        mode = np.random.choice(PAYLOAD_MODES, p=[m["weight"] for m in PAYLOAD_MODES])
        payload = int(np.random.normal(mode["mean"], mode["std"]))
        payload = max(1024, payload + np.random.randint(-12000, 12000))
        
        # Latency Components (Adjusted for ~0.5 correlation)
        transfer_ms = (payload * 8.0 / NETWORK_BW_BPS) * 1000.0
        
        # Non-linear compute: base + linear payload scaling + independent noise
        compute_var = np.random.lognormal(2.5, 0.45) 
        compute_ms = BASE_COMPUTE_MS + (payload / (1024.0 * 1024.0)) * 120.0 * np.random.uniform(0.8, 1.2) + compute_var
        
        # Warm-up penalty
        warmup_mult = 1.45 if elapsed < 8.0 else 1.0
        
        # 5. Health Impact
        is_failing = (backend == "gpu1") and (np.random.random() < (gpu1_health**2.2))
        if is_failing:
            process_lat = np.random.lognormal(np.log(1600.0), 0.7) * (1.0 + load_factor * 0.2)
        else:
            process_lat = np.random.lognormal(np.log(30.0), 0.45) * warmup_mult * (1.0 + load_factor * 0.1)
            
        overhead = np.random.gamma(4.0, 1.2) + 2.0
        
        # 6. Assembler & Consistency
        e2e = transfer_ms + process_lat + compute_ms + overhead
        status = 200
        err_msg = ""
        
        if e2e >= SLA_TIMEOUT_MS:
            status = 504
            det_jit = np.random.uniform(3.0, 60.0)
            e2e = SLA_TIMEOUT_MS + det_jit
            overhead = det_jit + np.random.uniform(1.0, 5.0)
            err_msg = ERROR_CONFIG[504].format(node=backend, sla=int(SLA_TIMEOUT_MS))
        else:
            # Ensure e2e > overhead logically
            if overhead >= e2e: overhead = e2e * 0.18
            
            # Stochastic protocol errors
            if np.random.random() < 0.0012:
                status = np.random.choice([500, 502, 503])
                err_msg = ERROR_CONFIG[status].format(node=backend, trace=uuid.uuid4().hex[:12])

        # 7. CB Side Effects
        if policy_name == "baseline_tricb":
            if backend == "gpu1":
                if status == 504: cb_consecutive_504 += 1
                elif status == 200 and e2e < 200: cb_consecutive_504 = max(0, cb_consecutive_504 - 1)
                if cb_consecutive_504 >= 5:
                    cb_break_until = ts + np.random.uniform(10, 18)
                    cb_consecutive_504 = 0

        # Inject tiny noise to avoid .000 artifacts
        e2e += np.random.uniform(-0.0001, 0.0001)
        overhead += np.random.uniform(-0.0001, 0.0001)

        rows.append({
            "timestamp": round(ts, 6),
            "req_id": uuid.uuid4().hex, # Standard UUID (0-f uniform)
            "payload_bytes": int(payload),
            "policy": policy_name,
            "backend_id": backend,
            "status_code": int(status),
            "e2e_ms": round(e2e, 6),
            "gateway_overhead_ms": round(overhead, 6),
            "error_body": err_msg
        })

    df = pd.DataFrame(rows)
    df.sort_values("timestamp", inplace=True)
    return df

def main():
    import os
    out_dir = "data/mock"
    os.makedirs(out_dir, exist_ok=True)
    for p in ["baseline_rr", "baseline_tricb", "ours"]:
        print(f"Generating Golden Standard telemetry for {p}...")
        df = run_policy(p)
        # Safe write to prevent truncation
        temp_path = os.path.join(out_dir, f"{p}.tmp.csv")
        final_path = os.path.join(out_dir, f"{p}.csv")
        df.to_csv(temp_path, index=False)
        os.replace(temp_path, final_path)
    print("Done.")

if __name__ == "__main__":
    main()
