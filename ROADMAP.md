# GrayPulse Project Roadmap

## Phase 1: Foundation (W1)
- [x] **Environment Bring-up**: VM inventory (20 nodes), Ansible infrastructure automation.
- [x] **Version Freezing**: Container Image Digest records and Kernel parameters locking.
- [x] **Model Deployment**: Triton setup on GPU nodes with ResNet50 and BERT.
- [x] **Motivation Experiment**: Differential observability data collection and 1s resolution logs.

## Phase 2: Detection (W2)
- [ ] **Anomaly Detection**: Implement $Z$-score based detector for P99/Queue Depth anomalies.
- [ ] **Data Pipeline**: Real-time log streaming from HAProxy to Prometheus.

## Phase 3: Mitigation (W3)
- [ ] **Adaptive Routing**: Development of GrayPulse-aware plugin for dynamic request rerouting.
- [ ] **Penalty System**: Soft-kill and exponential backoff mechanisms for degraded nodes.

## Phase 4: Integration (W4)
- [ ] **Dashboarding**: Grafana visualization for Gray Failure status and $Z$-score thresholds.
- [ ] **Control Plane**: Unified controller for multiple inference clusters.

## Phase 5: Evaluation (W5)
- [ ] **Fault Injection 2.0**: Network jitter, packet loss, and mixed resource contention tests.
- [ ] **Comparison Study**: Benchmark against standard Round-Robin and static health checks.

## Phase 6: Finalization (W6)
- [ ] **Reliability Drill**: Extreme stress test and automated recovery validation.
- [ ] **Final Report**: Documentation and results visualization for GrayPulse.
