## Latency Quantitative Analysis (VM 05 Run A)

| Metric | Baseline (0-30s) | Fault Zone (30-90s) | Degrade. Ratio |
|--------|------------------|---------------------|----------------|
| Mean   | 535.83 ms | 739.57 ms | 1.4x |
| StdDev | 113.78 ms | 749.61 ms | - |
| P50    | 534.90 ms | 558.40 ms | - |
| P90    | 689.11 ms | 2126.63 ms | - |
| P95    | 718.28 ms | 2197.48 ms | - |
| **P99**| **805.61 ms** | **2571.37 ms** | **3.2x** |
| Max    | 880.25 ms | 2906.83 ms | - |

> Critical Insight: The Gray Failure starvation caused the P99 tail latency to degrade by a factor of **3.2x**.
