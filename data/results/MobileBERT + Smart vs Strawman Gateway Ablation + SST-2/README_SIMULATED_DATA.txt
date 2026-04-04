SIMULATED DATA ONLY

Package: Gateway Ablation H (NLP / MobileBERT)

This package contains synthetic, deterministic artifacts for a CPU-only distributed inference gateway ablation:
- Model: MobileBERT
- Dataset semantics: GLUE / SST-2 style sentence inference
- Backend stack: Triton over HTTP
- Deployment: 12 active backend VMs out of a 20-VM cluster
- Gateway modes compared: gateway_smart vs gateway_strawman
- Routing semantics held approximately comparable between modes
- Batch size = 1
- Dynamic batching = disabled
- Fault window: seconds 90-180 on backend sp26-cs525-0605.cs.illinois.edu
- Recovery window: seconds 180-240
- Random seed: 5252603

Important:
- These are NOT measured results.
- These artifacts are intended for a simulated midterm-report dataset package only.
- Request-level CSV schemas follow the prompt exactly.
- Benchmark JSON files aggregate across all five concurrency runs for each mode.
