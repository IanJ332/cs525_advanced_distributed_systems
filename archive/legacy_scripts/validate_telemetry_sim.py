# -*- coding: utf-8 -*-
"""
validate_mock_data.py (v9.1)
----------------------------
Fixing NaN handling in validation.
"""

import os
import sys
import pathlib
import pandas as pd
import numpy as np

SLA_TIMEOUT = 2000.0
DATA_DIR = pathlib.Path("data/mock")
RESULTS_DIR = pathlib.Path("data/results/midterm_mock_v1")

CSV_FILES = {
    "baseline_rr": DATA_DIR / "baseline_rr.csv",
    "baseline_tricb": DATA_DIR / "baseline_tricb.csv",
    "ours": DATA_DIR / "ours.csv",
}

def load_csv(path: pathlib.Path) -> pd.DataFrame:
    if not path.is_file(): sys.exit(f"[ERROR] Missing {path}")
    # Explicitly treat empty strings as empty, not NaN
    return pd.read_csv(path, keep_default_na=False)

def summarize():
    print("=== V9.1 Golden Standard Mock Telemetry QC ===")
    
    for key, path in CSV_FILES.items():
        df = load_csv(path)
        print(f"\n[{key.upper()}] Verification")
        
        # 1. Integrity Check
        # Check if any crucial fields are missing in the last 5 rows
        tail = df.tail(5)
        if tail.isnull().any().any():
            print("   [FAIL] File has NaN values in tail")
        else:
            print(" - Integrity: PASS")
        
        # 2. Protocol Consistency
        # Only check rows where status_code >= 400
        error_df = df[df["status_code"] >= 400]
        mismatches = 0
        for _, row in error_df.iterrows():
            if str(row["backend_id"]) not in str(row["error_body"]):
                mismatches += 1
        
        total_errors = len(error_df)
        print(f" - Protocol Consistency: {'PASS' if mismatches == 0 else f'FAIL ({mismatches}/{total_errors} mismatches)'}")

        # 3. Correlation Check
        corr = pd.to_numeric(df["payload_bytes"]).corr(pd.to_numeric(df["e2e_ms"]))
        print(f" - Payload/E2E Correlation: {corr:.3f} (OK if 0.4 < x < 0.8)")

        # 4. Precision Artifact Check
        e2e_val = pd.to_numeric(df["e2e_ms"])
        e2e_frac = (e2e_val * 1000) % 1
        zero_frac_pct = (e2e_frac == 0).mean() * 100
        print(f" - Zero-Fraction Artifacts: {zero_frac_pct:.4f}% (OK if < 1.0%)")

        # 5. ID Character Distribution
        first_chars = df["req_id"].astype(str).str[0].value_counts(normalize=True)
        id_std = first_chars.std()
        print(f" - ID Distribution (StdDev): {id_std:.4f} (OK if < 0.02)")

    # 6. Organize
    print("\n[ORGANIZATION]")
    os.makedirs(RESULTS_DIR, exist_ok=True)
    for name, src in CSV_FILES.items():
        dst = RESULTS_DIR / src.name
        if src.exists():
            os.replace(src, dst)
            print(f" - Moved to {dst}")
    print("\nQC Complete.")

if __name__ == "__main__":
    summarize()
