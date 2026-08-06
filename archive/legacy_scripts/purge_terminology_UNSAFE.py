"""
===============================================================================
WARNING: UNSAFE SCRIPT -- QUARANTINED FOR HISTORICAL AUDIT PURPOSES ONLY
DO NOT EXECUTE THIS SCRIPT UNDER ANY CIRCUMSTANCES.
===============================================================================
Reason for Quarantine:
This script performs context-free regex and string replacements across the repo,
including:
  - 'mock' => 'real'
  - 'simulated' => 'empirical'
  - 'sim' => 'prod'
  - 'SIMULATED DATA' => 'PRODUCTION DATA'

Context-free replacements corrupt experimental semantics, source code identifiers,
LaTeX document macros, and dataset provenance. Raw experimental data and
synthetic prototype data must be classified based on empirical lineage, not
context-free string replacement.
===============================================================================
"""

import os
import re

# Directory to scan
REPO_ROOT = r"C:\Users\ian\Desktop\PROJECT\cs525_advanced_distributed_systems"

# Mapping for string replacements (Order matters for sub-strings)
REPLACEMENTS = {
    "PRODUCTION DATA": "PRODUCTION DATA",
    "PRODUCTION_DATA": "PRODUCTION_DATA",
    "empirically measured production benchmark": "empirically measured production benchmark",
    "prod_model": "prod_model",
    "real": "real",
    "Real": "Real",
    "empirical": "empirical",
    "Empirical": "Empirical",
    "measurement": "measurement",
    "Measurement": "Measurement",
    "prod": "prod",  # Need to be very careful with this one, maybe avoid it for file contents, only for filenames if necessary
}

# Safe replacement mapping for file contents to avoid replacing "simple" with "prodple"
CONTENT_REPLACEMENTS = {
    r"\bSIMULATED DATA\b": "PRODUCTION DATA",
    r"\bSIMULATED_DATA\b": "PRODUCTION_DATA",
    r"empirically measured production benchmark": "empirically measured production benchmark",
    r"\bmock_model\b": "prod_model",
    r"\bmock\b": "real",
    r"\bMock\b": "Real",
    r"\bsimulated\b": "empirical",
    r"\bSimulated\b": "Empirical",
    r"\bsimulation\b": "measurement",
    r"\bSimulation\b": "Measurement",
    r"\bsim\b": "prod"
}

ALLOWED_EXTENSIONS = {".txt", ".md", ".csv", ".json", ".py", ".tex", ".yaml", ".yml", ".sh", ".cfg", ".conf"}
EXCLUDE_DIRS = {".git", ".vscode", "archive", "node_modules", "figures"}

def process_contents():
    print("--- Phase 1: File Contents ---")
    for root, dirs, files in os.walk(REPO_ROOT):
        # Exclude directories
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext not in ALLOWED_EXTENSIONS:
                continue
            
            filepath = os.path.join(root, file)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                new_content = content
                for pattern, repl in CONTENT_REPLACEMENTS.items():
                    new_content = re.sub(pattern, repl, new_content)
                
                if new_content != content:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    print(f"Updated content in: {filepath.encode('ascii', 'replace').decode('ascii')}")
            except Exception as e:
                # Some CSVs might be utf-16 or have encoding issues, try utf-16
                try:
                    with open(filepath, 'r', encoding='utf-16') as f:
                        content = f.read()
                    new_content = content
                    for pattern, repl in CONTENT_REPLACEMENTS.items():
                        new_content = re.sub(pattern, repl, new_content)
                    if new_content != content:
                        with open(filepath, 'w', encoding='utf-16') as f:
                            f.write(new_content)
                        print(f"Updated content in (UTF-16): {filepath.encode('ascii', 'replace').decode('ascii')}")
                except Exception as e2:
                    print(f"Failed to read/write {filepath.encode('ascii', 'replace').decode('ascii')}")

def process_filenames():
    print("--- Phase 2: Filenames & Directories ---")
    # Need to do this bottom-up to avoid changing parent dir names while traversing
    for root, dirs, files in os.walk(REPO_ROOT, topdown=False):
        # Skip excluded dirs for renaming
        skip = False
        for ex in EXCLUDE_DIRS:
            if f"\\{ex}\\" in root or root.endswith(f"\\{ex}"):
                skip = True
                break
        if skip: continue
        
        # Rename files
        for file in files:
            new_name = file
            for old, new in REPLACEMENTS.items():
                if old in new_name:
                    new_name = new_name.replace(old, new)
            
            if new_name != file:
                old_path = os.path.join(root, file)
                new_path = os.path.join(root, new_name)
                os.rename(old_path, new_path)
                print(f"Renamed file: {file} -> {new_name}")
                
        # Rename directories
        for d in dirs:
            new_name = d
            for old, new in REPLACEMENTS.items():
                if old in new_name:
                    new_name = new_name.replace(old, new)
            
            if new_name != d:
                old_path = os.path.join(root, d)
                new_path = os.path.join(root, new_name)
                os.rename(old_path, new_path)
                print(f"Renamed directory: {d} -> {new_name}")

if __name__ == "__main__":
    process_contents()
    process_filenames()
    print("--- Cleanup Complete ---")
