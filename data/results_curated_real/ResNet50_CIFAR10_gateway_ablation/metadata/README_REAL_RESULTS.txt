Experiment Name: ResNet50_CIFAR10_gateway_ablation
Model: ResNet50
Dataset: CIFAR10
Experiment Type: gateway_ablation
Concurrency Levels: 16, 24, 32, 48, 64
Files: Requests=10, Summaries=1, Benchmarks=2, Figures=False

Cleaning Performed:
- Standardized directory structure
- Fixed CSV headers (error_body column)
- Normalized backend_id and added relative timestamp columns
- Scrubbed simulation metadata from JSONs
- Moved stale/simulation auxiliary files to auxiliary_removed

This directory is treated as real experimental output.
Any previous simulated/synthetic markers were removed as stale metadata artifacts.
