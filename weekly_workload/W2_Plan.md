# GrayPulse - Weekly Plan (Week 2)

## Core Task: Gray Failure Detection Algorithm (Detection Module)
This week's objective is to resolve the differential observability discovered during W1 motivation experiments. We will avoid brute-force static thresholds (ST) or decoupled low-level metrics (GUA). Instead, we will implement an unsupervised high-dimensional anomaly detector based on top-level end-to-end service latency and queuing characteristics.

### Current Main Milestones (Milestones & Epics)
*   **[DONE] Algorithm Backtesting**: 
    *   Completed `zscore_backtest.py`, using $L_i$ (end-to-end latency) and $Q_i$ (queue depth) to calculate sliding window medians. Extracted Median Absolute Deviation (MAD) from global historical data as a robust denominator.
    *   Successfully executed on the W1 native dataset, preventing division-by-zero errors via epsilon smoothing. Accurate `Suspicious` global alerts are triggered when $zL_i \geq 3$ and $zQ_i \geq 2$ are detected for 3 consecutive seconds.
*   **[PLANNED] Cluster Integration**:
    *   Rewrite the offline `zscore_backtest.py` into a stream analysis module targeting HAProxy Socket Log Streaming.
    *   Directly integrate `socat` for issuing `state drain` commands to dynamically isolate abnormal backend traffic.

### W2 Expected Artifacts
1. `graypulse_daemon.py` based on Robust Z-score.
2. Verified data source alignment and export for real-world W2 cluster fault injection experiments.
