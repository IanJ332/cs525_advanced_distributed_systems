# Data Distribution Plan & Large Asset Management

**Project**: GrayPulse Distributed Inference Observatory  
**Scope**: Dataset distribution tiering, Git tracking boundaries, and long-term academic preservation

---

## 1. Overview & Distribution Tiering

To maintain a lean repository clone size while guaranteeing 100% academic reproducibility, datasets and repository assets are categorized into three distribution tiers:

```
cs525_advanced_distributed_systems/
├── TIER 1: Core Git Repository (Tracked)
│   ├── Source Code (Python, Shell, Go, Ansible)
│   ├── Audit Manifests & Reports (`audit/*`)
│   ├── Canonical Normalized CSV Samples (`data/processed/*`)
│   ├── Paper Figures (`figures/paper/*`, `figures/supplementary/*`)
│   └── Documentation (`docs/*`, `paper/*`)
│
├── TIER 2: External Public Release Assets (GitHub Release / Zenodo)
│   ├── Full Empirical Campaign CSV Runs (`data/raw/*`)
│   └── Compressed Telemetry Archives (`graypulse_v1_empirical_raw.tar.gz`)
│
└── TIER 3: Private & Deprecated Audit Archives (Local / Internal Only)
    ├── `REQ_ID_REWRITE_MAP.csv` (134.78 MB Audit Map)
    └── `submit_png_graypulse_verified.zip` (50.71 MB Redundant Zip)
```

---

## 2. Asset Allocation Breakdown

| Asset Category | Location | Size Range | Storage Mechanism | Rationale |
| :--- | :--- | :--- | :--- | :--- |
| **Source Code & Configs** | `scripts/`, `configs/`, `tests/` | < 1 MB total | Standard Git | Essential codebase for execution and validation. |
| **Audit Manifests** | `audit/*` | < 5 MB | Standard Git | Immutable provenance and duplicate tracking. |
| **Paper Report PDF** | `paper/GrayPulse_*.pdf` | ~3.99 MB | Standard Git | Direct access to original research publication. |
| **Publication Figures** | `figures/paper/*` | ~10 MB total | Standard Git | High-resolution publication plots. |
| **Raw Campaign CSVs** | `data/raw/*` | 15–26 MB per file | GitHub Release / Zenodo | Preserves small repo clone size; downloadable via script. |
| **Audit Rewrite Map** | `REQ_ID_REWRITE_MAP.csv` | 134.78 MB | Private Archive | Deprecated intermediate mapping from early cleanup. |
| **Duplicate Submission ZIPs**| `submit_*.zip` | 50.71 MB | Local Archive | Redundant archive pending Phase B2 removal. |

---

## 3. Automated Dataset Fetcher Script (Planned for Phase B2)

To allow users to automatically download Tier 2 empirical raw datasets upon cloning:

```bash
# Planned command in Phase B2:
python -m scripts.collect.download_raw_datasets
```

This script will verify SHA-256 hashes against [`audit/data_manifest.json`](file:///c:/Users/ian/Desktop/PROJECT/cs525_advanced_distributed_systems/audit/data_manifest.json) after downloading.

---

*End of Data Distribution Plan.*
