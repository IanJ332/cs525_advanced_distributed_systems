SIMULATED DATA — Gateway Ablation G (CV / ResNet-50)

This directory contains a fully synthetic but internally consistent mock dataset package for a distributed systems midterm report.
These files are NOT measured results and MUST NOT be presented as real system measurements.

Campaign scope
- Model: ResNet-50
- Dataset semantics: CIFAR-10 test images resized/cropped to 224x224 and normalized for ImageNet-style ResNet inference
- Comparative target: gateway architecture only
- Gateway modes: smart vs strawman
- Batch size: 1
- Dynamic batching: disabled / not simulated
- Backend stack: Triton Inference Server over HTTP with ONNX Runtime
- System type: CPU-only
- Environment: 20-VM cluster, 12 active backend inference nodes, 1 gateway/control plane VM, 1 load-generator VM
- Fault window: 90s–180s, degradation on sp26-cs525-0605.cs.illinois.edu
- Run duration: 240 seconds per concurrency point
- Concurrency sweep: 16, 24, 32, 48, 64

Deterministic generation notes
- Request bodies are modeled as large near-constant JSON payloads carrying one FP32 tensor named "data" with logical shape [1, 3, 224, 224].
- smart gateway: full-body byte read + forward, without JSON parse / re-serialize.
- strawman gateway: full JSON parse + re-serialize before forward.
- Backend routing semantics are intentionally kept comparable across both modes via even backend assignment.
- Successful latencies and gateway overheads are generated from heavy-tailed lognormal distributions.
- Failures are injected with phase-aware probabilities and non-empty error bodies.
- Summary CSV rps is defined as successful requests per second over the 240-second run.
- Benchmark JSON files aggregate across the full five-run family for each mode.

Source basis
- Primary task specification: user-provided requirements in this conversation.
- HTTP/REST + Triton inference protocol context: NVIDIA Triton official docs.
- ImageNet-style ResNet preprocessing context: PyTorch/TorchVision official docs.
- CIFAR-10 dataset context: Alex Krizhevsky / University of Toronto CIFAR page.

Files included
- campaign_cv_resnet_gatewaysmart_c16.csv
- campaign_cv_resnet_gatewaysmart_c24.csv
- campaign_cv_resnet_gatewaysmart_c32.csv
- campaign_cv_resnet_gatewaysmart_c48.csv
- campaign_cv_resnet_gatewaysmart_c64.csv
- campaign_cv_resnet_gatewaystrawman_c16.csv
- campaign_cv_resnet_gatewaystrawman_c24.csv
- campaign_cv_resnet_gatewaystrawman_c32.csv
- campaign_cv_resnet_gatewaystrawman_c48.csv
- campaign_cv_resnet_gatewaystrawman_c64.csv
- summary_resnet_gateway_ablation.csv
- benchmark_resnet_gatewaysmart.json
- benchmark_resnet_gatewaystrawman.json
- representative_slices_SIMULATED.txt
- generate_simulated_gateway_ablation.py

Quick summary
            mode  concurrency  total_requests  success_rate       rps   avg_ms   p95_ms   p99_ms  error_rate  avg_gateway_overhead_ms
   gateway_smart           16           10121      0.994368 41.933333  379.801  626.050  824.850    0.005632                    2.939
   gateway_smart           24           11386      0.992271 47.075000  506.505  848.867 1099.269    0.007729                    3.786
   gateway_smart           32           12027      0.988276 49.525000  639.557 1152.363 1567.299    0.011724                    5.224
   gateway_smart           48           12249      0.973304 49.675000  942.265 1863.361 2713.436    0.026696                   10.325
   gateway_smart           64           11977      0.963931 48.104167 1287.215 2786.388 4282.248    0.036069                   17.102
gateway_strawman           16            9883      0.992310 40.862500  388.845  636.097  821.701    0.007690                   11.879
gateway_strawman           24           11099      0.988377 45.708333  519.741  864.140 1114.101    0.011623                   16.067
gateway_strawman           32           11438      0.978580 46.637500  672.368 1192.757 1593.064    0.021420                   37.785
gateway_strawman           48           11380      0.957030 45.379167 1014.659 1947.475 2730.989    0.042970                   78.049
gateway_strawman           64           10921      0.923359 42.016667 1412.118 2938.472 4456.630    0.076641                  128.088

Important use restriction
- These artifacts are for simulation / report prototyping only.
- Do not cite them as experimental measurements.
