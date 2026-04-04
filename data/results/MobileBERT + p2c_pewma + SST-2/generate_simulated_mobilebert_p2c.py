#!/usr/bin/env python3
"""
SIMULATED DATA generator for Campaign NLP-A.

This script deterministically generates:
- campaign_nlp_mobilebert_p2c_c32.csv
- campaign_nlp_mobilebert_p2c_c48.csv
- campaign_nlp_mobilebert_p2c_c64.csv
- campaign_nlp_mobilebert_p2c_c96.csv
- campaign_nlp_mobilebert_p2c_c128.csv
- summary_mobilebert_p2c.csv
- benchmark_mobilebert_p2c.json

Seed: 42
"""
import math
import random
import json
import hashlib
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from heapq import heappush, heappop
from pathlib import Path

import numpy as np
import pandas as pd

BACKENDS = [
    "sp26-cs525-0605","sp26-cs525-0606","sp26-cs525-0607","sp26-cs525-0608",
    "sp26-cs525-0609","sp26-cs525-0612","sp26-cs525-0613","sp26-cs525-0614",
    "sp26-cs525-0615","sp26-cs525-0617","sp26-cs525-0618","sp26-cs525-0619"
]
BACKEND_SPEED = {
    "sp26-cs525-0605":1.00, "sp26-cs525-0606":0.97, "sp26-cs525-0607":1.03, "sp26-cs525-0608":1.06,
    "sp26-cs525-0609":0.98, "sp26-cs525-0612":1.02, "sp26-cs525-0613":0.95, "sp26-cs525-0614":1.01,
    "sp26-cs525-0615":0.99, "sp26-cs525-0617":0.96, "sp26-cs525-0618":1.04, "sp26-cs525-0619":1.00,
}
BACKEND_BIAS = {
    "sp26-cs525-0605":0.03, "sp26-cs525-0606":-0.01, "sp26-cs525-0607":0.00, "sp26-cs525-0608":0.02,
    "sp26-cs525-0609":-0.01, "sp26-cs525-0612":0.01, "sp26-cs525-0613":-0.03, "sp26-cs525-0614":0.00,
    "sp26-cs525-0615":-0.01, "sp26-cs525-0617":-0.02, "sp26-cs525-0618":0.02, "sp26-cs525-0619":0.00,
}

@dataclass
class BackendState:
    inflight: int = 0
    ewma: float = 180.0
    recent_fail: float = 0.0

def fault_multiplier(t):
    if t < 90:
        return 1.0, 0.0
    if t < 120:
        x = (t - 90) / 30.0
        return 1.0 + 1.0 * x, 0.01 * x
    if t < 180:
        return 2.0 + 0.6 * math.sin((t - 120) / 60.0 * math.pi / 2.0), 0.025
    if t <= 240:
        x = (t - 180) / 60.0
        return 2.2 - 1.1 * x, 0.02 * (1.0 - x)
    return 1.0, 0.0

def payload_bytes_for(req_numeric, concurrency):
    h = int(hashlib.sha256(f"{concurrency}-{req_numeric}".encode()).hexdigest()[:8], 16)
    return 2108 + (h % 173)

def simulate_run(concurrency, seed=42):
    rng = random.Random(seed + concurrency * 13)
    np_rng = np.random.default_rng(seed + concurrency * 17)
    states = {b: BackendState(0, 170 * BACKEND_SPEED[b], 0.0) for b in BACKENDS}
    event_heap = []
    records = []
    req_id = 0
    duration = 240.0
    base_ms = {32:175,48:181,64:191,96:200,128:215}[concurrency]
    gw_base = {32:10.5,48:11.5,64:13.8,96:16.8,128:19.5}[concurrency]
    cluster_pressure = {32:0.0,48:0.15,64:0.34,96:0.60,128:0.85}[concurrency]

    def choose_backend(start_t):
        cands = rng.sample(BACKENDS, 2)
        scored = []
        for b in cands:
            st = states[b]
            norm_ewma = st.ewma / (base_ms * BACKEND_SPEED[b])
            recent_fail_pen = 2.0 * st.recent_fail
            score = (
                st.inflight
                + 0.8 * norm_ewma
                + recent_fail_pen
                + BACKEND_BIAS[b]
                + rng.uniform(-0.08, 0.08)
            )
            scored.append((score, b))
        scored.sort()
        return scored[0][1]

    def generate_request(start_t, rid):
        b = choose_backend(start_t)
        pending = states[b].inflight
        fault_mult, fault_err = (1.0, 0.0)
        if b == "sp26-cs525-0605":
            fault_mult, fault_err = fault_multiplier(start_t)

        q_mult = 1.0 + 0.43 * pending + 0.052 * (pending ** 2)
        global_inflight = sum(s.inflight for s in states.values())
        pressure_mult = 1.0 + cluster_pressure * max(0.0, global_inflight / concurrency - 0.83) * 0.25
        burst = 1.0 + 0.08 * math.sin(start_t / 7.5 + (sum(ord(ch) for ch in b) % 7))
        logn = math.exp(np_rng.normal(0, 0.17 + 0.025 * cluster_pressure))
        service_ms = base_ms * BACKEND_SPEED[b] * q_mult * pressure_mult * burst * fault_mult * logn
        gw_ms = max(
            5.0,
            np_rng.normal(
                gw_base + 0.3 * max(0.0, global_inflight - 0.8 * concurrency) / 12.0 + 0.18 * pending,
                1.8 + 1.3 * cluster_pressure,
            ),
        )
        e2e_ms = service_ms + gw_ms

        phase_fault_bonus = 0.0
        if 90 <= start_t < 180:
            phase_fault_bonus = {32:0.0007,48:0.0013,64:0.004,96:0.010,128:0.018}[concurrency]
        elif 180 <= start_t <= 240:
            phase_fault_bonus = {32:0.0003,48:0.0005,64:0.0017,96:0.0045,128:0.008}[concurrency]

        base_err = {32:0.0015,48:0.003,64:0.010,96:0.024,128:0.055}[concurrency]
        queue_err = 0.0015 * max(0.0, pending - 4) ** 1.25
        timeout_thr = {32:1200,48:1500,64:1850,96:2500,128:3200}[concurrency]
        latency_err = 0.0
        if e2e_ms > timeout_thr:
            latency_err += min(0.11, (e2e_ms / timeout_thr - 1.0) * 0.085)
        p_err = min(0.5, base_err + phase_fault_bonus + queue_err + fault_err + latency_err)

        if rng.random() < p_err:
            long_tail = e2e_ms > {32:1100,48:1400,64:1750,96:2300,128:3000}[concurrency]
            p504 = 0.33 + 0.24 * long_tail
            p503 = 0.47 - 0.08 * long_tail
            rr = rng.random()
            if rr < p503:
                status = 503
                err = f"SIMULATED: upstream backend overload at {b}:8000"
                e2e_ms *= rng.uniform(0.90, 1.12)
            elif rr < p503 + p504:
                status = 504
                err = f"SIMULATED: upstream read timeout from {b}:8000"
                e2e_ms = max(e2e_ms, {32:900,48:1100,64:1400,96:1950,128:2600}[concurrency]) * rng.uniform(1.00, 1.28)
            else:
                status = 500
                err = f"SIMULATED: Triton HTTP inference error on {b}:8000"
                e2e_ms *= rng.uniform(0.82, 1.05)
        else:
            status = 200
            err = ""

        e2e_ms = float(max(gw_ms + 30.0, e2e_ms))
        states[b].inflight += 1
        comp_t = start_t + e2e_ms / 1000.0
        heappush(event_heap, (comp_t, rid, b, start_t, status, e2e_ms, gw_ms, err))

    for _ in range(concurrency):
        req_id += 1
        generate_request(0.0, req_id)

    while event_heap:
        comp_t, rid, b, st_t, status, e2e_ms, gw_ms, err = heappop(event_heap)
        states[b].inflight -= 1
        obs_service = max(30.0, e2e_ms - gw_ms)
        states[b].ewma = 0.82 * states[b].ewma + 0.18 * obs_service
        states[b].recent_fail = 0.88 * states[b].recent_fail + 0.12 * (1.0 if status != 200 else 0.0)
        records.append((st_t, rid, b, status, float(e2e_ms), float(gw_ms), err))
        if comp_t < duration:
            req_id += 1
            generate_request(comp_t, req_id)

    return records

def build_package(out_dir):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    run_starts = {
        32: datetime(2026,4,3,9,0,0,tzinfo=timezone(timedelta(hours=-5))),
        48: datetime(2026,4,3,9,10,0,tzinfo=timezone(timedelta(hours=-5))),
        64: datetime(2026,4,3,9,20,0,tzinfo=timezone(timedelta(hours=-5))),
        96: datetime(2026,4,3,9,30,0,tzinfo=timezone(timedelta(hours=-5))),
        128: datetime(2026,4,3,9,40,0,tzinfo=timezone(timedelta(hours=-5))),
    }

    summary_rows = []
    frames = []
    for concurrency in [32,48,64,96,128]:
        recs = simulate_run(concurrency, seed=42)
        rows = []
        for st_t, rid, backend, status, e2e_ms, gw_ms, err in recs:
            ts = (run_starts[concurrency] + timedelta(seconds=float(st_t))).isoformat(timespec="milliseconds")
            rows.append({
                "timestamp": ts,
                "req_id": f"SIM-C{concurrency:03d}-{rid:07d}",
                "payload_bytes": payload_bytes_for(rid, concurrency),
                "policy": "p2c_pewma",
                "backend_id": backend,
                "status_code": status,
                "e2e_ms": round(e2e_ms, 3),
                "gateway_overhead_ms": round(gw_ms, 3),
                "error_body": err,
            })

        df = pd.DataFrame(rows).sort_values(["timestamp", "req_id"], kind="stable").reset_index(drop=True)
        frames.append(df)
        csv_path = out_dir / f"campaign_nlp_mobilebert_p2c_c{concurrency}.csv"
        df.to_csv(csv_path, index=False)

        total = len(df)
        success = int((df["status_code"] == 200).sum())
        summary_rows.append({
            "mode": "mobilebert_p2c_pewma",
            "concurrency": concurrency,
            "total_requests": total,
            "success_rate": round(success / total, 6),
            "rps": round(total / 240.0, 6),
            "avg_ms": round(float(df["e2e_ms"].mean()), 3),
            "p95_ms": round(float(df["e2e_ms"].quantile(0.95)), 3),
            "p99_ms": round(float(df["e2e_ms"].quantile(0.99)), 3),
            "error_rate": round(1.0 - success / total, 6),
            "avg_gateway_overhead_ms": round(float(df["gateway_overhead_ms"].mean()), 3),
        })

    summary_df = pd.DataFrame(summary_rows)
    summary_df.to_csv(out_dir / "summary_mobilebert_p2c.csv", index=False)

    aggregate_df = pd.concat(frames, ignore_index=True)
    benchmark = {
        "data_label": "SIMULATED DATA",
        "benchmark_scope": "aggregate_campaign",
        "campaign_name": "Campaign NLP-A",
        "mode": "mobilebert_p2c_pewma",
        "model": "MobileBERT",
        "routing_policy": "p2c_pewma",
        "dataset": "GLUE/SST-2",
        "inference_stack": "Triton Inference Server over HTTP",
        "execution_mode": "CPU-only distributed inference",
        "p99_ms": round(float(aggregate_df["e2e_ms"].quantile(0.99)), 3),
        "avg_ms": round(float(aggregate_df["e2e_ms"].mean()), 3),
        "rps": round(float(len(aggregate_df) / (240.0 * 5)), 6),
        "total_requests": int(len(aggregate_df)),
        "per_run": summary_rows,
    }
    with open(out_dir / "benchmark_mobilebert_p2c.json", "w", encoding="utf-8") as f:
        json.dump(benchmark, f, indent=2)

if __name__ == "__main__":
    build_package(Path.cwd())
    print("SIMULATED DATA package generated.")
