SIMULATED DATA PACKAGE
======================

This package contains FULLY SYNTHETIC, TECHNICALLY CONSISTENT mock data for a distributed systems midterm report.

IMPORTANT
---------
- This is SIMULATED DATA.
- This is NOT measured data.
- This is NOT from a real benchmark run.

Scenario
--------
Model: MobileBERT
Routing framework: round_robin
Dataset: GLUE / SST-2
Serving stack: Triton CPU-only distributed serving
Cluster size: 20 VMs overall
Active backend nodes: 12
Active backend list:
  sp26-cs525-0605, sp26-cs525-0606, sp26-cs525-0607, sp26-cs525-0608, sp26-cs525-0609, sp26-cs525-0612, sp26-cs525-0613, sp26-cs525-0614, sp26-cs525-0615, sp26-cs525-0617, sp26-cs525-0618, sp26-cs525-0619

Assumptions
-----------
- CPU-only
- 2 vCPU per backend
- ~7.5 GiB RAM per backend
- batch size = 1
- no dynamic batching
- fixed sequence length = 128
- small payloads
- 240 second campaign duration
- phases:
    0-90 steady
    90-180 fault
    180-240 recovery

Synthetic behavior encoded
--------------------------
- round_robin distributes requests uniformly across active backends
- sp26-cs525-0605 continues to receive proportional traffic during the fault window
- fault-window degradation is intentionally more visible at 64 / 96 / 128 concurrency
- low-concurrency degradation is present but not catastrophic
- runs include both successes and failures

Files
-----
- campaign_nlp_mobilebert_rr_c32.csv
- campaign_nlp_mobilebert_rr_c48.csv
- campaign_nlp_mobilebert_rr_c64.csv
- campaign_nlp_mobilebert_rr_c96.csv
- campaign_nlp_mobilebert_rr_c128.csv
- summary_mobilebert_rr.csv
- benchmark_mobilebert_rr.json
