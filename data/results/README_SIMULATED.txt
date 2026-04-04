Deterministic generation recipe:
- RNG seed: 42
- Backend set: vm05, vm06, vm07, vm08, vm09, vm12, vm13, vm14, vm15, vm17, vm18, vm19
- policy column fixed to "P2C" to preserve logger schema only
- backend choice modeled as near-uniform pseudo-random over 12 backends
- smart gateway overhead modeled as low single-digit ms, rising mildly under pressure
- fault window: 90s-180s on vm05 with higher latency and error probability
- recovery: 180s-240s with gradual partial recovery, incomplete at higher concurrency
- payload_bytes held near-constant around a plausible serialized JSON body for FP32 [1,3,224,224] data tensor with value 0.5 repeated 150528 times
- latency modeled with heavy-tailed lognormal mixtures, not Gaussian
- no GPU, no dynamic batching, no true P2C/EWMA semantics, no NLP workloads

Row-count plan:
- campaign_a_cv_c16.csv: 8880 rows
- campaign_a_cv_c24.csv: 11760 rows
- campaign_a_cv_c32.csv: 13680 rows
- campaign_a_cv_c48.csv: 14520 rows
- campaign_a_cv_c64.csv: 14400 rows
