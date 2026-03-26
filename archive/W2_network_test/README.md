# W2 Network Fault Injection Protocol

**Objective:** Execute a `tc netem` network delay and packet loss experiment on Node 05 to evaluate the GrayPulse detector's passive monitoring capabilities under network-induced Gray Failures.

---

## Experiment Protocol

This experiment utilizes a 3-terminal execution layout across the bastion host. Ensure you have activated your Python virtual environment where required.

### Terminal 1: Live Workload Dashboard
Monitors the overall cluster heartbeat and node resource saturation in real-time.
- **Command:**
  ```bash
  python .\scripts\live_monitor.py
  ```
- **Expected Observation:** Node 05 CPU should remain low indicating that the application itself has not crashed or spiked in resource usage, effectively isolating the network fault.

### Terminal 2: GrayPulse Z-Score Detector
Runs the core passive monitoring algorithm targeting the HAProxy logs.
- **Command:**
  ```bash
  python .\scripts\detectors\graypulse_zscore_detector.py
  ```
- **Expected Observation:** The detector will begin tracking rolling statistics. You should monitor the output for sudden spikes in $zL_i$ (Latency Z-Score) and $zQ_i$ (Queue Depth Z-Score) shortly after the fault is triggered.

### Terminal 3: Trigger Network Fault
Deploy and immediately execute the safe defensive bash script on the target node.
- **Command:**
  ```bash
  ansible node05 -i inventory.ini -m script -a "scripts/fault_injection/tc_fault_injection.sh --action delay" -b
  ```
- **Expected Observation:** The script pushes exactly 200ms delay with 20ms jitter to the primary network interface on Node 05, scheduling an automatic rollback 60 seconds later.

---

## Generated Artifacts

Upon completion of the experiment, specific telemetry and diagnostic files are generated. These serve as empirical evidence of the system's performance.

- **`haproxy_network_delay.log`**
  - **Purpose:** Captures the raw HAProxy HTTP timing metrics during the injection window, serving as ground-truth evidence that GrayPulse correctly intercepts network-induced latencies before they cause upstream timeouts.
- **`zscore_network_metrics.csv`**
  - **Purpose:** Logs the calculated Z-score standard deviations ($zL_i$, $zQ_i$) over time, proving that the GrayPulse anomaly algorithm can passively mathematically distinguish between normal traffic variance and an active gray failure.
