import re
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


RESULTS_DIR = Path("data/results")
OUT_DIR = RESULTS_DIR / "figures"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def load_request_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)

    # 兼容旧格式 / 新格式
    if "status_code" in df.columns:
        df["status_num"] = pd.to_numeric(df["status_code"], errors="coerce")
    elif "status" in df.columns:
        df["status_num"] = pd.to_numeric(df["status"], errors="coerce")
    else:
        raise ValueError(f"{path.name}: missing status column")

    if "e2e_ms" in df.columns:
        df["lat_ms"] = pd.to_numeric(df["e2e_ms"], errors="coerce")
    elif "latency_ms" in df.columns:
        df["lat_ms"] = pd.to_numeric(df["latency_ms"], errors="coerce")
    else:
        raise ValueError(f"{path.name}: missing latency column")

    if "timestamp" not in df.columns:
        raise ValueError(f"{path.name}: missing timestamp column")

    df["timestamp"] = pd.to_numeric(df["timestamp"], errors="coerce")
    df = df.dropna(subset=["timestamp", "status_num", "lat_ms"]).copy()

    # 成功请求：HTTP 200 且 latency >= 0
    df["is_success"] = (df["status_num"] == 200) & (df["lat_ms"] >= 0)
    return df


def extract_concurrency(path: Path) -> int:
    m = re.search(r"_c(\d+)\.csv$", path.name)
    if not m:
        raise ValueError(f"Cannot parse concurrency from {path.name}")
    return int(m.group(1))


def summarize_one(path: Path) -> dict:
    df = load_request_csv(path)
    c = extract_concurrency(path)

    duration = max(df["timestamp"].max() - df["timestamp"].min(), 1e-6)
    total = len(df)
    succ = int(df["is_success"].sum())
    err = total - succ

    succ_lat = df.loc[df["is_success"], "lat_ms"]

    out = {
        "concurrency": c,
        "total_requests": total,
        "success_rate": succ / total if total else 0.0,
        "error_rate": err / total if total else 0.0,
        "rps": total / duration if duration > 0 else np.nan,
        "avg_ms": succ_lat.mean() if len(succ_lat) else np.nan,
        "p95_ms": np.percentile(succ_lat, 95) if len(succ_lat) else np.nan,
        "p99_ms": np.percentile(succ_lat, 99) if len(succ_lat) else np.nan,
    }
    return out


def build_summary_from_requests() -> pd.DataFrame:
    files = sorted(RESULTS_DIR.glob("campaign_a_cv_c*.csv"))
    if not files:
        raise FileNotFoundError("No campaign_a_cv_c*.csv files found")
    rows = [summarize_one(f) for f in files]
    df = pd.DataFrame(rows).sort_values("concurrency").reset_index(drop=True)
    return df


def plot_summary(summary: pd.DataFrame):
    fig, ax1 = plt.subplots(figsize=(8, 5))

    x = summary["concurrency"]

    ax1.plot(x, summary["avg_ms"], marker="o", label="Avg Latency (ms)")
    ax1.plot(x, summary["p99_ms"], marker="o", label="P99 Latency (ms)")
    ax1.set_xlabel("Concurrency")
    ax1.set_ylabel("Latency (ms)")
    ax1.grid(True, alpha=0.3)

    ax2 = ax1.twinx()
    ax2.plot(x, summary["rps"], marker="s", linestyle="--", label="RPS")
    ax2.set_ylabel("Requests/sec")

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left")

    plt.title("Campaign A Summary: Latency and Throughput vs Concurrency")
    plt.tight_layout()
    plt.savefig(OUT_DIR / "campaign_a_summary.png", dpi=200)
    plt.close()


def plot_timeline(concurrency: int):
    path = RESULTS_DIR / f"campaign_a_cv_c{concurrency}.csv"
    df = load_request_csv(path).copy()

    t0 = df["timestamp"].min()
    df["t_rel"] = df["timestamp"] - t0
    df["lat_success"] = df["lat_ms"].where(df["is_success"], np.nan)

    # 5秒窗口
    bin_size = 5
    df["bin"] = (df["t_rel"] // bin_size).astype(int)
    grouped = df.groupby("bin")

    timeline = pd.DataFrame({
        "t_sec": grouped["t_rel"].min(),
        "success_rate": grouped["is_success"].mean(),
        "p99_ms": grouped["lat_success"].apply(
            lambda s: np.percentile(s.dropna(), 99) if s.dropna().size > 0 else np.nan
        ),
        "count": grouped.size(),
    }).reset_index(drop=True)

    fig, ax1 = plt.subplots(figsize=(10, 5))

    ax1.plot(timeline["t_sec"], timeline["p99_ms"], marker="o", linewidth=1.5, label="5s-window P99")
    ax1.set_xlabel("Time since start (s)")
    ax1.set_ylabel("P99 latency (ms)")
    ax1.grid(True, alpha=0.3)

    ax2 = ax1.twinx()
    ax2.plot(timeline["t_sec"], timeline["success_rate"], linestyle="--", label="5s-window Success Rate")
    ax2.set_ylabel("Success Rate")

    # 阶段背景
    ax1.axvspan(0, 90, alpha=0.10, label="Steady")
    ax1.axvspan(90, 180, alpha=0.18, label="Gray Failure")
    ax1.axvspan(180, 240, alpha=0.10, label="Recovery")

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    # 去重
    seen = set()
    lines, labels = [], []
    for ln, lb in zip(lines1 + labels1, labels1 + labels2):
        if lb not in seen:
            seen.add(lb)
            lines.append(ln)
            labels.append(lb)
    ax1.legend(lines, labels, loc="upper left")

    plt.title(f"Campaign A Timeline @ Concurrency={concurrency}")
    plt.tight_layout()
    plt.savefig(OUT_DIR / f"campaign_a_timeline_c{concurrency}.png", dpi=200)
    plt.close()


def plot_cdf():
    files = sorted(RESULTS_DIR.glob("campaign_a_cv_c*.csv"))
    fig, ax = plt.subplots(figsize=(8, 5))

    for path in files:
        c = extract_concurrency(path)
        df = load_request_csv(path)
        lat = np.sort(df.loc[df["is_success"], "lat_ms"].values)
        if len(lat) == 0:
            continue
        y = np.arange(1, len(lat) + 1) / len(lat)
        ax.plot(lat, y, label=f"C={c}")

    ax.set_xlabel("Latency (ms)")
    ax.set_ylabel("CDF")
    ax.set_title("Campaign A Successful-Request Latency CDF")
    ax.grid(True, alpha=0.3)
    ax.legend()
    plt.tight_layout()
    plt.savefig(OUT_DIR / "campaign_a_cdf.png", dpi=200)
    plt.close()


def main():
    summary = build_summary_from_requests()
    summary.to_csv(OUT_DIR / "campaign_a_summary_recomputed.csv", index=False)

    print("Recomputed summary:")
    print(summary)

    plot_summary(summary)

    # 先画 c32；如果你想，也可以改成 c64
    if (RESULTS_DIR / "campaign_a_cv_c32.csv").exists():
        plot_timeline(32)
    elif (RESULTS_DIR / "campaign_a_cv_c64.csv").exists():
        plot_timeline(64)

    plot_cdf()
    print(f"Plots saved to: {OUT_DIR}")


if __name__ == "__main__":
    main()
