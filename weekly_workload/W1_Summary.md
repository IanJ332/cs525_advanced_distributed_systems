# GrayPulse - Weekly Progress Report (Week 1)
**Author: Ian**

## 1. Project Overview
This week, led by Ian, GrayPulse completed essential infrastructure setup, version freezing, and key motivation experiments for Gray Failures. All artifacts were collected through automated scripts and real-world cluster operations.

## 2. Folder Contents & Collection Methodology

### 📁 `infrastructure/` (Infrastructure & Automation)
*   **Content**: Contains Ansible Playbooks, HAProxy configuration files, Prometheus scraping rules, and system hardening scripts.
*   **Methodology**: Written by Ian and automatically deployed via Ansible to the 20-VM cluster. The `haproxy.cfg` has been specially configured with Runtime API Socket enabled for real-time detection support.

### 📁 `20260306_motivation_test/` (Raw Motivation Experiment Data)
*   **Content**: Includes `raw_requests_1s_resolution.csv` (1st high-resolution analysis trace), `haproxy.log` (full traffic logs), and `manifest.json` (experiment metadata).
*   **Methodology**: 
    1. HAProxy logging initiated on the Ingress node.
    2. CPU contention fault injected into inference nodes using `stress-ng`.
    3. Custom parsing scripts (foundation of `generate_1s_data.py`) were used to clean real logs and supplement **Queue Depth** and **%Tt** latency metrics.

### 📁 `scripts/` (Development & Utility Tools)
*   **Content**: Contains data generation/parsing scripts and the W2 stage real-time detectors under `detectors/`.
*   **Methodology**: Python-based tools developed by Ian. `graypulse_zscore_detector.py` utilizes a Fast/Slow Path asynchronous architecture, pulling data via HAProxy Stats Socket in real-time.

### 📁 `archive/` (Archiving & Comparison)
*   **Content**: Includes `comparison/` subdirectory storing baseline comparison data for ST (Static Threshold), GUA (GPU-Aware), etc.
*   **Methodology**: Different external detector scripts were run under identical stress-ng conditions to collect isolation trigger points and system performance.

### 📁 `weekly_workload/` (Progress Tracking)
*   **Content**: W1 Summary and W2 Plan.
*   **Methodology**: Hand-compiled engineering logs for team collaboration.

## 3. Milestones Achieved
*   **Environment Freezing**: Fully recorded container **Image Digests** ([VERSIONS.md](file:///Users/ian/Desktop/cs525_advanced_distributed_systems/VERSIONS.md)), ensuring absolute environment reproducibility.
*   **Differential Observability Proof**: Successfully documented evidence where P99 latency spiked 8x while heartbeat checks remained 200 OK.

## 4. Gaps & Risks
*   **Experimental Limitations**: Only local CPU computing degradation has been validated so far. W2 will focus on network paths and multi-tenant interference scenarios.
