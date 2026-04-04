# SIMULATED DATA - Campaign NLP-A

This package contains **fully synthetic, technically consistent mock benchmark artifacts** for a distributed CPU-only MobileBERT inference campaign.  
It is **not measured data** from a real deployment or from the current codebase.

## Scenario
- Model: MobileBERT
- Routing policy: `p2c_pewma`
- Dataset semantics: GLUE / SST-2 sentence classification
- Inference stack: Triton Inference Server over HTTP
- Execution mode: CPU-only distributed inference
- Cluster scope: 20 VMs total, with 12 active inference backends in this campaign
- Gateway / control plane: VM01
- Load generator: VM02
- Duration per run: 240 seconds
- Concurrency sweep: 32, 48, 64, 96, 128

## Fixed infrastructure assumptions preserved
- CPU-only
- 2 vCPU per VM
- ~7.5 GiB RAM per VM
- Ubuntu 24.04.1
- Triton HTTP on port 8000
- Batch size 1
- No dynamic batching
- No GPU acceleration
- Input tensors represented consistently as `int32`
- Tensor shapes:
  - `input_ids`: [1, 128]
  - `attention_mask`: [1, 128]
  - `token_type_ids`: [1, 128]

## Backends used
- sp26-cs525-0605
- sp26-cs525-0606
- sp26-cs525-0607
- sp26-cs525-0608
- sp26-cs525-0609
- sp26-cs525-0612
- sp26-cs525-0613
- sp26-cs525-0614
- sp26-cs525-0615
- sp26-cs525-0617
- sp26-cs525-0618
- sp26-cs525-0619

## Phase model
Each run is simulated with three phases:
1. 0-90 s: steady state
2. 90-180 s: gray-failure injection on VM05 (`sp26-cs525-0605`)
3. 180-240 s: recovery

VM05 degradation is modeled as:
- slower service times
- elevated timeout probability
- elevated 5xx probability
- gradual recovery after 180 s

## Deterministic generation recipe
The request traces were created from a closed-loop discrete-event simulation with deterministic seed `42`.

For each concurrency level `C`:
1. Initialize exactly `C` in-flight requests at time 0.
2. For every new request, choose 2 random candidate backends.
3. Compute a per-candidate score using:
   - current in-flight requests for that backend
   - latency-sensitive EWMA of recently observed service time
   - short-memory failure penalty
   - small fixed per-backend bias term
   - small random tie-breaking noise
4. Route to the lower-score backend. This produces imperfect but non-uniform load split.
5. Sample service time from:
   - concurrency-dependent base latency
   - backend-specific speed multiplier
   - queue inflation term `1 + 0.43*p + 0.052*p^2`, where `p` is current backend in-flight count
   - mild cluster-pressure inflation
   - mild periodic burst factor
   - lognormal noise
   - VM05 fault multiplier during the injected gray-failure window
6. Sample gateway overhead separately and add it to service time to form `e2e_ms`.
7. Sample non-200 outcomes with probability based on:
   - concurrency baseline
   - queue depth pressure
   - latency tail severity
   - VM05 fault bonus during degradation / recovery
8. On completion before 240 seconds, immediately issue a replacement request to keep the run closed-loop.
9. Export one CSV row per issued request with request start timestamp.

## Notes on interpretation
- `req_id` values are intentionally prefixed with `SIM-` to label row-level data as simulated.
- `payload_bytes` are kept small and nearly constant to reflect SST-2-style text inference over Triton HTTP rather than image payloads.
- Success latencies are intentionally lower than a typical CPU-only ResNet-50 image inference campaign at comparable concurrency, while still showing long-tail behavior under saturation.
- The policy is not idealized: VM05 receives less traffic during the fault window, but is not perfectly avoided.

## Included artifacts
- request-level CSVs
- summary CSV
- benchmark JSON
- deterministic Python generator

## Source notes used to keep the scenario technically grounded
These sources were used only to anchor interface and workload assumptions; they do **not** imply these numbers were measured.

1. **NVIDIA Triton Inference Server documentation** - official  
   Page: *Running Triton / HTTP-REST and GRPC Protocol*  
   URL: https://docs.nvidia.com/deeplearning/triton-inference-server/user-guide/docs/  
   Relevant detail: Triton serves HTTP on port 8000 and exposes an HTTP/REST inference protocol.

2. **Hugging Face Transformers - MobileBERT documentation** - official  
   Page: *MobileBERT*  
   URL: https://huggingface.co/docs/transformers/model_doc/mobilebert  
   Relevant detail: MobileBERT is a lightweight BERT-family model and uses standard BERT-style inputs such as `input_ids`, `attention_mask`, and `token_type_ids`.

3. **GLUE Benchmark** - official benchmark site  
   Page: *GLUE Tasks*  
   URL: https://gluebenchmark.com/tasks  
   Relevant detail: SST-2 is a sentence-level sentiment classification task within GLUE.

## File-level checksums
- `benchmark_mobilebert_p2c.json`: `d74fd02a25a4eed0eba4980f3524b5fda115474ad0819ccb3c1d85e5550df032`
- `campaign_nlp_mobilebert_p2c_c128.csv`: `6ca569d46256df781217659624bd4a66833640033556458881bbd3a8b29fe906`
- `campaign_nlp_mobilebert_p2c_c32.csv`: `c3d2c6d099ce3ce6a3bc10f98b9a3d18206b48c3366e5ec04a591548fd04b660`
- `campaign_nlp_mobilebert_p2c_c48.csv`: `3070874d905a51119f7037bb9f8513aa5e38e9edeab0c63e5391168fd3c034bb`
- `campaign_nlp_mobilebert_p2c_c64.csv`: `97428b6e6e336038bb3c99a7f68e0d5c9954c39b43206f185cf41c3f9c136590`
- `campaign_nlp_mobilebert_p2c_c96.csv`: `3547cc7b7ad7f39e60be65d844d2bd5d99b7b2d2333ef1636c01bc3b0922a8ec`
- `generate_simulated_mobilebert_p2c.py`: `61b7de596b51e9e50b10d60c78af1a68039990b678bc8302b6c4e81f6b0db4f3`
- `summary_mobilebert_p2c.csv`: `028e80aa40df16193648ba42fa820e9fc4a89789830814e0e58a1d8bf7dace04`
