
import math, random, heapq, json, pandas as pd
from pathlib import Path

BACKENDS = [
    "sp26-cs525-0605.cs.illinois.edu",
    "sp26-cs525-0606.cs.illinois.edu",
    "sp26-cs525-0607.cs.illinois.edu",
    "sp26-cs525-0608.cs.illinois.edu",
    "sp26-cs525-0609.cs.illinois.edu",
    "sp26-cs525-0612.cs.illinois.edu",
    "sp26-cs525-0613.cs.illinois.edu",
    "sp26-cs525-0614.cs.illinois.edu",
    "sp26-cs525-0615.cs.illinois.edu",
    "sp26-cs525-0617.cs.illinois.edu",
    "sp26-cs525-0618.cs.illinois.edu",
    "sp26-cs525-0619.cs.illinois.edu",
]
FAULT_BACKEND = BACKENDS[0]
CONCURRENCY_LEVELS = [16, 24, 32, 48, 64]
PAYLOAD_BYTES = 1184972

HEALTHY_BACKEND_MEAN = {16:355,24:470,32:585,48:845,64:1135}
RECOVERY_MULT = {16:1.03,24:1.04,32:1.05,48:1.06,64:1.07}
SPILLOVER_MULT = {16:1.03,24:1.05,32:1.08,48:1.12,64:1.16}
FAULT_BACKEND_MULT = {16:1.48,24:1.60,32:1.75,48:1.92,64:2.08}
SMART_GW_MEAN = {16:2.8,24:3.6,32:5.0,48:8.6,64:13.5}
STRAW_GW_MEAN = {16:11.0,24:15.0,32:23.0,48:40.0,64:66.0}
HEALTHY_ERR = {
    "gateway_smart": {16:0.002,24:0.0035,32:0.007,48:0.015,64:0.026},
    "gateway_strawman": {16:0.004,24:0.007,32:0.014,48:0.030,64:0.055},
}
FAULT_ADD_FAULT_BACKEND = {
    "gateway_smart": {16:0.055,24:0.070,32:0.090,48:0.120,64:0.155},
    "gateway_strawman": {16:0.080,24:0.100,32:0.135,48:0.180,64:0.235},
}
FAULT_ADD_OTHERS = {
    "gateway_smart": {16:0.001,24:0.002,32:0.004,48:0.009,64:0.015},
    "gateway_strawman": {16:0.002,24:0.004,32:0.007,48:0.014,64:0.025},
}
RECOVERY_ADD_FAULT_BACKEND = {
    "gateway_smart": {16:0.015,24:0.020,32:0.026,48:0.038,64:0.050},
    "gateway_strawman": {16:0.022,24:0.030,32:0.040,48:0.058,64:0.080},
}
RECOVERY_ADD_OTHERS = {
    "gateway_smart": {16:0.0005,24:0.001,32:0.0015,48:0.003,64:0.005},
    "gateway_strawman": {16:0.001,24:0.0015,32:0.003,48:0.005,64:0.009},
}

def lognormal_ms(rng, mean_ms, sigma):
    mu = math.log(mean_ms) - 0.5 * sigma * sigma
    return rng.lognormvariate(mu, sigma)

def gateway_overhead(rng, mode, c, phase):
    if mode == "gateway_smart":
        base_mean = SMART_GW_MEAN[c]
        sigma = 0.28 if c <= 24 else 0.34 if c == 32 else 0.44 if c == 48 else 0.52
        phase_mult = 1.0 if phase == "steady" else 1.10 if phase == "fault" else 1.05
    else:
        base_mean = STRAW_GW_MEAN[c]
        sigma = 0.33 if c <= 24 else 0.42 if c == 32 else 0.55 if c == 48 else 0.68
        phase_mult = 1.0 if phase == "steady" else 1.16 if phase == "fault" else 1.08
    return max(0.5, lognormal_ms(rng, base_mean * phase_mult, sigma))

def backend_service(rng, c, phase, backend_id):
    base = HEALTHY_BACKEND_MEAN[c]
    sigma = 0.34 if c <= 24 else 0.40 if c == 32 else 0.48 if c == 48 else 0.56
    mult = 1.0
    if phase == "fault":
        mult = FAULT_BACKEND_MULT[c] if backend_id == FAULT_BACKEND else SPILLOVER_MULT[c]
    elif phase == "recovery":
        if backend_id == FAULT_BACKEND:
            mult = (FAULT_BACKEND_MULT[c] + RECOVERY_MULT[c]) / 2.0
        else:
            mult = RECOVERY_MULT[c]
    return lognormal_ms(rng, base * mult, sigma)

def error_prob(mode, c, phase, backend_id):
    p = HEALTHY_ERR[mode][c]
    if phase == "fault":
        p += FAULT_ADD_FAULT_BACKEND[mode][c] if backend_id == FAULT_BACKEND else FAULT_ADD_OTHERS[mode][c]
    elif phase == "recovery":
        p += RECOVERY_ADD_FAULT_BACKEND[mode][c] if backend_id == FAULT_BACKEND else RECOVERY_ADD_OTHERS[mode][c]
    return min(p, 0.8)

def status_and_error(rng, p_fail):
    if rng.random() > p_fail:
        return 200, ""
    r = rng.random()
    if r < 0.52:
        return 503, "backend overloaded 503"
    elif r < 0.84:
        return 504, "upstream timeout during degraded window"
    return 500, "backend execution error"

def failure_latency(rng, c, phase, backend_id, status):
    base = HEALTHY_BACKEND_MEAN[c]
    if status == 504:
        mean = base * (1.7 if phase == "steady" else 2.1 if backend_id == FAULT_BACKEND else 1.85)
        sigma = 0.42 if c <= 32 else 0.58
    elif status == 503:
        mean = base * (1.15 if phase == "steady" else 1.4 if backend_id == FAULT_BACKEND else 1.28)
        sigma = 0.38 if c <= 32 else 0.46
    else:
        mean = base * (0.95 if phase == "steady" else 1.15)
        sigma = 0.36 if c <= 32 else 0.44
    return lognormal_ms(rng, mean, sigma)

def simulate(mode, c, start_ts, seed):
    rng = random.Random(seed)
    workers = [(start_ts, wid) for wid in range(c)]
    heapq.heapify(workers)
    rows = []
    req_idx = 0
    end_ts = start_ts + 240.0
    while workers:
        avail, wid = heapq.heappop(workers)
        if avail >= end_ts:
            break
        rel = avail - start_ts
        phase = "steady" if rel < 90 else "fault" if rel < 180 else "recovery"
        backend_id = BACKENDS[req_idx % len(BACKENDS)]
        gw = gateway_overhead(rng, mode, c, phase)
        p_fail = error_prob(mode, c, phase, backend_id)
        status, err = status_and_error(rng, p_fail)
        if status == 200:
            bsvc = backend_service(rng, c, phase, backend_id)
            e2e = gw + bsvc + rng.uniform(5.0, 9.0) + (0.5 if phase != "steady" else 0)
        else:
            bsvc = failure_latency(rng, c, phase, backend_id, status)
            e2e = gw + bsvc + rng.uniform(6.0, 10.0)
        if mode == "gateway_strawman" and c >= 32:
            extra = rng.lognormvariate(math.log((c - 24) * 1.3 + 2) - 0.5 * (0.55 ** 2), 0.55)
            if phase == "fault":
                extra *= 1.15
            elif phase == "recovery":
                extra *= 1.06
            gw += extra
            e2e += extra
        if mode == "gateway_smart" and c >= 48 and phase != "steady":
            extra = rng.lognormvariate(math.log((c - 40) * 0.18 + 0.8) - 0.5 * (0.35 ** 2), 0.35)
            gw += extra
            e2e += extra
        if rng.random() < (0.002 + 0.001 * (c >= 48) + 0.002 * (phase == "fault")):
            stretch = 1.5 + rng.random() * 1.8
            e2e *= stretch
            gw *= 1.08 + rng.random() * 0.25
            if status == 200 and rng.random() < 0.25 + 0.2 * (mode == "gateway_strawman"):
                status = 504
                err = "gateway queue timeout"
        e2e = max(e2e, gw + 4)
        rows.append((
            round(avail, 6),
            ("gs" if mode == "gateway_smart" else "gw") + f"{c}_{req_idx:05d}",
            PAYLOAD_BYTES,
            mode,
            backend_id,
            status,
            round(e2e, 3),
            round(gw, 3),
            err,
        ))
        heapq.heappush(workers, (avail + e2e / 1000.0, wid))
        req_idx += 1
    return pd.DataFrame(rows, columns=[
        "timestamp", "req_id", "payload_bytes", "mode", "backend_id",
        "status_code", "e2e_ms", "gateway_overhead_ms", "error_body"
    ])

def main(outdir="SIMULATED_DATA_gateway_ablation_resnet50"):
    out = Path(outdir)
    out.mkdir(exist_ok=True)
    base_start = 1775203200.0
    run_offsets = {
        ("gateway_smart",16):0, ("gateway_strawman",16):1800,
        ("gateway_smart",24):3600, ("gateway_strawman",24):5400,
        ("gateway_smart",32):7200, ("gateway_strawman",32):9000,
        ("gateway_smart",48):10800, ("gateway_strawman",48):12600,
        ("gateway_smart",64):14400, ("gateway_strawman",64):16200,
    }
    summary = []
    families = {"gateway_smart": [], "gateway_strawman": []}
    for c in CONCURRENCY_LEVELS:
        for mode in ["gateway_smart", "gateway_strawman"]:
            seed = 1000 + c * 17 + (0 if mode == "gateway_smart" else 1)
            df = simulate(mode, c, base_start + run_offsets[(mode, c)], seed)
            families[mode].append(df)
            fname = (
                f"campaign_cv_resnet_gatewaysmart_c{c}.csv"
                if mode == "gateway_smart"
                else f"campaign_cv_resnet_gatewaystrawman_c{c}.csv"
            )
            df.to_csv(out / fname, index=False)
            succ = df["status_code"].eq(200)
            summary.append({
                "mode": mode,
                "concurrency": c,
                "total_requests": int(len(df)),
                "success_rate": round(float(succ.mean()), 6),
                "rps": round(float(succ.sum() / 240.0), 6),
                "avg_ms": round(float(df["e2e_ms"].mean()), 3),
                "p95_ms": round(float(df["e2e_ms"].quantile(0.95)), 3),
                "p99_ms": round(float(df["e2e_ms"].quantile(0.99)), 3),
                "error_rate": round(float(1.0 - succ.mean()), 6),
                "avg_gateway_overhead_ms": round(float(df["gateway_overhead_ms"].mean()), 3),
            })
    pd.DataFrame(summary).sort_values(["mode","concurrency"]).to_csv(
        out / "summary_resnet_gateway_ablation.csv", index=False
    )
    for mode, family_parts in families.items():
        family = pd.concat(family_parts, ignore_index=True)
        succ = family["status_code"].eq(200)
        bench = {
            "label": "SIMULATED DATA",
            "campaign": "Gateway Ablation G (CV / ResNet-50)",
            "aggregation_scope": "all five concurrency runs for this gateway mode",
            "mode": mode,
            "p99_ms": round(float(family["e2e_ms"].quantile(0.99)), 3),
            "avg_ms": round(float(family["e2e_ms"].mean()), 3),
            "rps": round(float(succ.sum() / (240.0 * len(CONCURRENCY_LEVELS))), 6),
            "total_requests": int(len(family)),
        }
        fname = "benchmark_resnet_gatewaysmart.json" if mode == "gateway_smart" else "benchmark_resnet_gatewaystrawman.json"
        with open(out / fname, "w") as f:
            json.dump(bench, f, indent=2)

if __name__ == "__main__":
    main()
