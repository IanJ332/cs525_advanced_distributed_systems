Experiment Name: MobileBERT_SST2_gateway_ablation
Model: MobileBERT
Dataset: SST2
Experiment Type: gateway_ablation
Concurrency Levels: 128, 32, 48, 64, 96
Files: Requests=10, Summaries=1, Benchmarks=2, Figures=False

Cleaning Performed:
- Standardized directory structure
- Fixed CSV headers (error_body column)
- Normalized backend_id and added relative timestamp columns
- Scrubbed simulation metadata from JSONs
- Moved stale/simulation auxiliary files to auxiliary_removed

This directory is treated as real experimental output.
Any previous simulated/synthetic markers were removed as stale metadata artifacts.
