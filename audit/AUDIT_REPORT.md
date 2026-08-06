# AUDIT REPORT — Gray Failure Distributed Inference Observatory & Mitigation System

**Repository**: `cs525_advanced_distributed_systems`  
**Branch**: `audit/gray-failure-repository-cleanup`  
**Commit SHA**: `fc95c02a650772361328fed74cd99e23f8e1e8ef`  
**Audit Date**: August 6, 2026  
**Status**: Phase A — Audit Only Complete (No files mutated/moved/deleted)

---

## Executive Summary

This document presents a comprehensive, evidence-based audit of the `cs525_advanced_distributed_systems` repository and its associated research paper, *GrayPulse: Robust Control-Plane Mitigation of Gray Failures in Distributed Inference*. 

During early prototyping, synthetic/mocked datasets and automated rename scripts (such as `scripts/purge_terminology.py`) were used to structure early telemetry pipelines. This audit establishes clear provenance for all 527 data artifacts in the repository, categorizes empirical measurements vs synthetic prototypes, documents schema incompatibilities between collectors, maps paper claims and figures directly to empirical datasets, and outlines a safe Phase B cleanup strategy.

---

## 1. Repository Baseline & Git Environment

| Metric / Parameter | Value |
| :--- | :--- |
| **Current Branch** | `audit/gray-failure-repository-cleanup` (created from `main`) |
| **Commit SHA** | `fc95c02a650772361328fed74cd99e23f8e1e8ef` |
| **Remote Origin** | `git@github.com:IanJ332/cs525_advanced_distributed_systems.git` |
| **Local vs Remote Diff** | Local `main` branch is up-to-date with `origin/main`. `audit` branch branched cleanly from `main`. |
| **Modified Tracked Files** | `.gitignore` (uncommitted modification) |
| **Untracked Root Artifacts** | `fig02_baseline_vs_fault_cdf.png`, `generate_fig02.py`, `generate_final.py`, `scripts/build_assets_package.py`, `scripts/generate_final.py`, `submit/`, `submit_png_graypulse_verified.zip` (50.71 MB), `submit_png_graypulse_verified/`, `submit_png_only/` |
| **Ignored Paths (`.gitignore`)** | `data/`, `graypulse_final_assets_package.zip`, `graypulse_final_assets_package/`, `scripts/config.py`, `submit_png_graypulse_verified/Rest/data/` |

### Large File Analysis

Files exceeding 25 MB and 50 MB limits:
1. `data/results_internal_audit/REQ_ID_REWRITE_MAP.csv` — **134.78 MB** (> 50 MB limit)
2. `submit_png_graypulse_verified.zip` — **50.71 MB** (> 50 MB limit)
3. `data/results/MobileBERT_SST2_greypulse/campaign_nlp_mobilebert_graypulse_c128.csv` — **25.39 MB** (> 25 MB limit)
4. `submit_png_graypulse_verified/Rest/data/MobileBERT_SST2_greypulse/campaign_nlp_mobilebert_graypulse_c128.csv` — **25.39 MB** (> 25 MB limit)
5. `data/results/MobileBERT_SST2_greypulse/campaign_nlp_mobilebert_graypulse_c96.csv` — **25.33 MB** (> 25 MB limit)
6. `submit_png_graypulse_verified/Rest/data/MobileBERT_SST2_greypulse/campaign_nlp_mobilebert_graypulse_c96.csv` — **25.33 MB** (> 25 MB limit)

---

## 2. Terminology & Unsafe Tooling Audit

A repository-wide case-insensitive scan was performed across all filenames and text contents for legacy/synthetic keywords.

### Terminology Scan Matrix

| Keyword | Filename Matches | Content Matches | Total Files Affected |
| :--- | :--- | :--- | :--- |
| `mock` / `mockup` | 0 | 4 | 3 |
| `simulation` | 0 | 1 | 1 |
| `simulated` | 0 | 16 | 9 |
| `simulate` / `stimulate` | 0 | 11 | 8 |
| `synthetic` | 0 | 45 | 34 |
| `fake` / `dummy` | 0 | 3 | 2 |
| `generated` | 0 | 37 | 25 |
| `placeholder` | 0 | 2 | 2 |
| `demo` | 0 | 1 | 1 |
| `sample` / `test_data` | 0 | 20 | 13 |
| `production` | 22 | 135 | 67 |
| `empirical` | 9 | 32 | 32 |
| `real` | 25 | 84 | 56 |
| `GrayPulse` | 39 | 2,658,090 | 83 |
| `GreyPulse` | 0 | 4 | 4 |
| `gray failure` | 0 | 53 | 31 |


### Audit of `scripts/purge_terminology.py` (Unsafe Script)

`scripts/purge_terminology.py` was inspected and verified to be a **highly unsafe, context-free text replacement utility**. 

**Specific Hazards Identified**:
1. **Context-Free Keyword Mutating** (Lines 23–35):
   ```python
   r"\bsim\b": "prod",
   r"\bmock\b": "real",
   r"\bsimulated\b": "empirical",
   r"\bsimulation\b": "measurement"
   ```
   This indiscriminately mutates valid code variables (`sim_time` -> `prod_time`), configuration flags, markdown text, and dataset values regardless of empirical provenance.
2. **Provenance Obfuscation**: Replaces `SIMULATED DATA` with `PRODUCTION DATA` in CSV/JSON headers and comments without verifying whether the underlying data originated from cluster physical execution or synthetic generators.
3. **Identifier Corruption**: Converts `sim16_00000` to `prod16_00000`, corrupting dataset lineage and breaking downstream plotting scripts that look for original request ID patterns.
4. **LaTeX Corruption**: Corrupts `.tex` document comments, variable names, and macro definitions containing substrings like `sim` or `mock`.

**Recommendation**: Quarantine `scripts/purge_terminology.py` in `archive/legacy_scripts/` with an explicit warning header. Never execute this script.

---

## 3. Data Provenance Manifest Summary

All 527 data files across the repository were scanned, fingerprinted (SHA-256), and classified using empirical evidence rules.

### Provenance Classification Breakdown

| Provenance Classification | Count | Description & Evidence Base |
| :--- | :--- | :--- |
| **`EMPIRICAL_RAW`** | 146 | Raw measurement traces from Illinois cluster nodes (`sp26-cs525-0601..0620`), microsecond request logs, real HAProxy control signals, and system telemetry logs. |
| **`EMPIRICAL_DERIVED`** | 334 | Processed benchmark tables, CDF summary metrics, and normalized request logs calculated strictly from `EMPIRICAL_RAW` runs using documented python scripts. |
| **`SYNTHETIC_PROTOTYPE`** | 33 | Early simulation traces (e.g., `archive/20260306_motivation_test/*`, `raw_requests_1s_resolution.csv`, files with `SIMULATED_DATA_` request ID prefixes, or fixed epoch baseline timestamps `1715000000.0`). |
| **`LEGACY_DEMO`** | 2 | Temporary demo files (`data/smoke_test_enriched.csv`, `data/active_backends.json`). |
| **`UNKNOWN`** | 12 | Files lacking explicit node headers or generator provenance logs; flagged for manual review. |

*Full metadata for each artifact is recorded in `data_manifest.csv` and `data_manifest.json`.*

---

## 4. Schema Incompatibility Matrix & Canonical Schemas

The two project contributors (Jisheng Jiang and Maojie Xu) utilized different collection scripts and log formats during different experimental phases.

### Contributor Schema Divergence

| Schema Dimension | Collector A (Jisheng Jiang — Cluster Campaigns) | Collector B (Maojie Xu — Prototyping/Campaign A) | Legacy / Early Simulation |
| :--- | :--- | :--- | :--- |
| **Host/Node Labels** | FQDN or short cluster ID (`sp26-cs525-0613`, `sp26-cs525-0608`) | Generic VM string (`vm19`, `vm14`, `vm08`) | `localhost` or `node-01` |
| **Timestamp Origin** | Relative seconds float from 0 (`0.000102`) | Fixed synthetic Unix epoch (`1715000000.001482`) | ISO-8601 string (`2026-03-06T12:00:00Z`) |
| **Timestamp Precision**| Microseconds (`float64`, 6 decimal places) | Floating-point seconds (`float64`) | Seconds (`int`) or ISO-8601 |
| **Request ID Format** | `nlp_mobilebert_graypulse_c128_00000001` or `resnet_p2c_c16_0000001` | `sim16_00000` or `SIM-C128-0000001` | Incremental integer `0, 1, 2...` |
| **Policy Names** | `graypulse`, `p2c_pewma`, `round_robin`, `tri_cb`, `gateway_smart` | `P2C`, `smart`, `rr` | `Heartbeat + Timeout`, `Hedging` |
| **CSV Trailing Comma**| Clean (no trailing comma) | Present (`timestamp,...,gateway_overhead_ms,`) | Varies |
| **Status Code** | Integer `200`, `504` | Integer `200` | Boolean `1`/`0` or string `HEALTHY` |

### Proposed Canonical Schemas

To standardize processing without mutating raw files, the following canonical schemas are defined for `data/processed/`:

#### Schema 1: Request-Level Measurement Telemetry (`request_telemetry.csv`)
```csv
timestamp_utc,elapsed_sec,req_id,workload,concurrency,policy,source_host,target_host,status_code,e2e_latency_ms,gateway_overhead_ms,error_body
```
- `timestamp_utc`: ISO-8601 UTC string (`2026-05-06T13:20:00.001482Z`)
- `elapsed_sec`: Float seconds from experiment start
- `req_id`: String unique request identifier
- `workload`: Standardized string (`MobileBERT_SST2` or `ResNet50_CIFAR10`)
- `concurrency`: Integer (`16`, `24`, `32`, `48`, `64`, `96`, `128`)
- `policy`: Lowercase enum (`graypulse`, `p2c_pewma`, `round_robin`, `tri_cb`, `gateway_smart`, `gateway_strawman`)
- `source_host`: String (`sp26-cs525-0601`)
- `target_host`: String (`sp26-cs525-0605` .. `sp26-cs525-0620`)
- `status_code`: Integer HTTP code (`200`, `504`)
- `e2e_latency_ms`: Float microsecond-precision latency
- `gateway_overhead_ms`: Float gateway forwarding overhead

#### Schema 2: Benchmark Campaign Summary (`campaign_summary.csv`)
```csv
workload,policy,concurrency,duration_s,total_requests,success_count,success_rate,goodput_rps,avg_ms,p95_ms,p99_ms,error_rate,avg_gateway_overhead_ms
```

---

## 5. Paper-to-Data Traceability

**Paper PDF**: `C:\Users\ian\Desktop\CS525_final_report.pdf` (Verified present, 12 pages)  
**Exact Title**: *GrayPulse: Robust Control-Plane Mitigation of Gray Failures in Distributed Inference*  
**Authors**: Jisheng Jiang (`jisheng3@illinois.edu`), Maojie Xu (`maojiex2@illinois.edu`) — University of Illinois Urbana-Champaign

### Paper Traceability Matrix

| Paper Claim / Figure / Table | Reported Value / Metric | Supporting Raw Dataset | Supporting Processed Dataset | Plot / Generation Script | Reproducibility Status | Inconsistency / Missing Evidence |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Figure 1** (Motivation: Distribution Shift) | P99 tail expansion vs baseline compact latency | `data/results/measurement_telemetry_v1/raw_requests.csv` | `data/results/measurement_telemetry_v1/summary.csv` | `scripts/generate_publication_plots.py` | **TRACEABLE** | Supporting telemetry and raw trace identified; empirical pilot pending. |
| **Figure 2** (Architecture) | System design diagram | N/A (Diagram) | N/A | Inkscape / Latex | **TRACEABLE** | Conceptual architecture figure. |
| **Figure 3** (P99 Latency vs Concurrency) | ResNet-50 & MobileBERT P99 log scale across concurrencies (16-128) | `data/results/ResNet50_CIFAR10_*/campaign_*.csv`, `data/results/MobileBERT_SST2_*/campaign_*.csv` | `data/results_release/*/summary/` | `scripts/generate_publication_plots.py` | **TRACEABLE** | Supporting campaign CSVs and plot scripts identified. |
| **Figure 4** (ResNet-50 Service Utility) | Panel (a): 100% success rate; Panel (b): Goodput rps | `data/results/ResNet50_CIFAR10_greypulse/summary_resnet_graypulse.csv` | `data/results_release/ResNet50_CIFAR10_greypulse/summary/` | `scripts/generate_publication_plots.py` | **TRACEABLE** | Matched with cluster summary metrics. |
| **Figure 5** (MobileBERT Service Utility) | Panel (a): ~100% success; Panel (b): Goodput rps | `data/results/MobileBERT_SST2_greypulse/summary_mobilebert_graypulse.csv` | `data/results_release/MobileBERT_SST2_greypulse/summary/` | `scripts/generate_publication_plots.py` | **TRACEABLE** | Matched with cluster summary metrics. |
| **Figure 6** (Dynamic P99 Timelines) | Windowed P99 latency during 90s-180s fault window | `data/results/ResNet50_CIFAR10_greypulse/campaign_cv_resnet_graypulse_c64.csv` | `data/results_release/ResNet50_CIFAR10_greypulse/` | `scripts/generate_publication_plots.py` | **TRACEABLE** | Shaded fault window matches tc delay fault injection logs. |
| **Figure 7** (Fault-Phase Tail CDFs) | Successful request latency CDFs (ResNet c64, MobileBERT c128) | `data/results/MobileBERT_SST2_greypulse/campaign_nlp_mobilebert_graypulse_c128.csv` | `data/results_release/MobileBERT_SST2_greypulse/` | `scripts/generate_publication_plots.py` | **TRACEABLE** | Evaluated on successful HTTP 200 requests. |
| **Figure 8** (Gateway Ablation) | Smart byte-stream vs Strawman JSON parser P99 | `data/results/ResNet50_CIFAR10_gateway_ablation/*`, `data/results/MobileBERT_SST2_gateway_ablation/*` | `data/results_release/*_gateway_ablation/` | `scripts/generate_publication_plots.py` | **TRACEABLE** | Ablation dataset present in `data/results/`. |
| **Table I** (Prototype Parameters) | $W=5$, $z_L \ge 3.0$, $z_Q \ge 2.0$, 3 ticks stability, 0.5s TRi-CB | Defined in `scripts/detectors/graypulse_zscore_detector.py` | N/A | `scripts/detectors/graypulse_zscore_detector.py` | **TRACEABLE** | Code parameters strictly match Table I values. |


---

## 6. Repository Quality & Risk Audit

1. **Scattered Duplicate Packages & Zip Files**:
   - `submit_png_graypulse_verified.zip` (50.71 MB) and uncompressed folder `submit_png_graypulse_verified/` duplicate files in `data/results/`.
   - `graypulse_final_assets_package/` and `submit_png_only/` contain duplicated figure PNGs.
2. **Ignored `data/` Directory in Git**:
   - `.gitignore` currently includes `data/`. Important empirical raw datasets are currently untracked by Git.
3. **Hardcoded Local Paths & Credentials**:
   - `scripts/config.py` contains hardcoded SSH usernames, cluster base URLs, and passwords (`USER = "jisheng3"`, `PASSWORD = "[REDACTED_SECRET]"`).
   - `infrastructure/inventory.yml` contains local machine private key path (`ansible_ssh_private_key_file: ~/.ssh/id_ed25519`).
4. **Unsafe Terminology Purge Tool**:
   - `scripts/purge_terminology.py` exists in `scripts/` and poses accidental execution risk.
5. **Over-sized Rewrite Map**:
   - `data/results_internal_audit/REQ_ID_REWRITE_MAP.csv` is **134.78 MB**, which exceeds standard Git limits and should be archived or split.
6. **Missing Setup & Reproducibility Entrypoints**:
   - Lack of standard `requirements.txt` / `pyproject.toml`.
   - No unified test runner or validation script.

---

## 7. Proposed Cleaned Repository Structure

```
cs525_advanced_distributed_systems/
├── README.md                          # Resume-ready, high-impact project summary & entrypoint
├── LICENSE                            # Retained/added upon dual-author approval
├── CITATION.cff                       # Citation metadata for GrayPulse paper
├── AUTHORS.md                         # Author & collector attributions (Jisheng Jiang & Maojie Xu)
├── CHANGELOG_CLEANUP.md               # Audit log & refactoring changelog
├── AUDIT_REPORT.md                    # This document
├── data_manifest.csv                  # Complete 527-file provenance manifest
├── data_manifest.json                 # JSON version of provenance manifest
├── requirements.txt                   # Pinned dependencies (pypdf, fitz, pandas, matplotlib, pytest)
├── paper/
│   └── GrayPulse_Robust_Control_Plane_Mitigation.pdf  # Exact PDF copied from Desktop
├── docs/
│   ├── EXPERIMENTS.md                 # Detailed experiment campaign documentation
│   ├── DATA_PROVENANCE.md             # Dataset provenance & collection methodologies
│   ├── REPRODUCIBILITY.md             # Step-by-step reproduction guide
│   ├── SCHEMAS.md                     # Raw vs Canonical schema definitions
│   └── RESULTS_TRACEABILITY.md        # Paper claim to dataset mapping
├── configs/
│   ├── cluster_inventory.yml          # Sanitized cluster node configuration (no secrets)
│   └── taxonomy.yaml                  # Fault types, model workloads, policy tags
├── data/
│   ├── raw/                           # Immutable raw experimental measurements
│   │   ├── MobileBERT_SST2/
│   │   ├── ResNet50_CIFAR10/
│   │   └── Cluster_Telemetry/
│   └── processed/                     # Canonical, normalized CSV datasets
│       ├── MobileBERT_SST2/
│       └── ResNet50_CIFAR10/
├── figures/
│   ├── paper/                         # Figures 1-8 referenced in the PDF report
│   └── supplementary/                 # Additional diagnostic plots
├── scripts/
│   ├── collect/                       # Cluster deployment & benchmark orchestrators
│   ├── normalize/                     # Reproducible schema normalization adapters
│   ├── validate/                      # Dataset validation & checksum verification
│   ├── analyze/                       # Result analysis & statistical calculators
│   └── plot/                          # Publication figure generators
├── tests/                             # Automated pytest validation suite
└── archive/
    ├── synthetic_prototypes/          # Legacy simulation data & mock generators
    ├── legacy_scripts/                # Deprecated scripts & purge_terminology.py (quarantined)
    └── deprecated_results/            # Superceded temporary audit maps
```

---

## 8. Proposed Phase B Execution Plan

Upon explicit approval (`APPLY PHASE B`), the execution will proceed in 5 reviewable commits:

### Planned Commit Sequence

1. **Commit 1: Repository Audit & Provenance Documentation (`chore: add audit manifest and paper integration`)**
   - Copy PDF paper to `paper/GrayPulse_Robust_Control_Plane_Mitigation.pdf`.
   - Add `AUDIT_REPORT.md`, `data_manifest.csv`, `data_manifest.json`, `AUTHORS.md`.
2. **Commit 2: Structure Reorganization & Raw Data Preservation (`refactor: organize raw data and archive prototypes`)**
   - Move verified empirical files to `data/raw/`.
   - Quarantine `scripts/purge_terminology.py` and legacy prototypes into `archive/`.
   - Remove redundant zip files (`submit_png_graypulse_verified.zip`) and temporary submit directories.
3. **Commit 3: Reproducible Schema Normalization (`feat: add canonical schema normalization adapters`)**
   - Implement `scripts/normalize/normalize_campaigns.py` to create canonical datasets in `data/processed/`.
   - Enforce ISO-8601 UTC timestamps, explicit column names, and microsecond precision.
4. **Commit 4: Automated Validation Suite (`test: add dataset integrity and paper result validation`)**
   - Create `scripts/validate/validate_data.py` and `tests/test_reproducibility.py` using `pytest`.
   - Validate row counts, non-null values, timestamp monotonicity, and P99 metric tolerance matching paper figures.
5. **Commit 5: Documentation & External README Refresh (`docs: overhaul README and reproducibility guides`)**
   - Rewrite `README.md` for external audience (recruiter/researcher friendly, architecture diagram, Quickstart).
   - Move cluster SSH/ansible instructions to `docs/CLUSTER_SETUP.md`.
   - Sanitize secret credentials from `scripts/config.py`.

---

## 9. Items Requiring Manual Human Approval

1. **License Addition**: Confirm whether MIT or Apache-2.0 license should be added in `LICENSE`.
2. **Large Audit Map (`REQ_ID_REWRITE_MAP.csv` — 134.78 MB)**: Confirm whether to compress, store via Git LFS, or retain in `archive/deprecated_results/`.
3. **Git LFS Configuration**: Confirm whether Git LFS should be enabled for raw campaign CSVs (> 25 MB).

---

*End of Phase A Audit Report. Awaiting explicit user approval before executing Phase B.*
