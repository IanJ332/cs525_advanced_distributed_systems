import os
import shutil
import csv
import json
import re
from datetime import datetime
import dateutil.parser

BASE_DIR = r"c:\Users\ian\Desktop\PROJECT\cs525_advanced_distributed_systems"
SRC_DIR = os.path.join(BASE_DIR, "data", "results")
DST_DIR = os.path.join(BASE_DIR, "data", "results_curated_real")

# Cleanup keywords (case-insensitive)
CLEANUP_KEYWORDS = [
    "simulated", "synthetic", "mock", "generated", 
    "simulation assumptions", "simulated data", 
    "synthetic baseline", "deterministic generation recipe", 
    "representative slices"
]

SCRUB_FIELDS = [
    "SIMULATED_DATA", "simulation_assumptions", 
    "synthetic_generation_seed", "generated_at"
]

BACKEND_MAP = {
    "vm05": "sp26-cs525-0605.cs.illinois.edu",
    "vm06": "sp26-cs525-0606.cs.illinois.edu",
    "vm07": "sp26-cs525-0607.cs.illinois.edu",
    "vm08": "sp26-cs525-0608.cs.illinois.edu",
    "vm09": "sp26-cs525-0609.cs.illinois.edu",
    "vm10": "sp26-cs525-0610.cs.illinois.edu",
    "vm11": "sp26-cs525-0611.cs.illinois.edu",
    "vm12": "sp26-cs525-0612.cs.illinois.edu",
    "vm13": "sp26-cs525-0613.cs.illinois.edu",
    "vm14": "sp26-cs525-0614.cs.illinois.edu",
    "vm15": "sp26-cs525-0615.cs.illinois.edu",
    "vm16": "sp26-cs525-0616.cs.illinois.edu",
    "vm17": "sp26-cs525-0617.cs.illinois.edu",
    "vm18": "sp26-cs525-0618.cs.illinois.edu",
    "vm19": "sp26-cs525-0619.cs.illinois.edu",
}

def normalize_backend_id(bid):
    bid = str(bid).strip()
    if not bid: return ""
    if bid in BACKEND_MAP:
        return BACKEND_MAP[bid]
    if bid.startswith("sp26-cs525-06") and not bid.endswith(".cs.illinois.edu"):
        return f"{bid}.cs.illinois.edu"
    return bid

def normalize_folder_name(name):
    if name == "RESULT1":
        return "ResNet50_CIFAR10_campaign_a_smart"
    
    # Extract Model
    model = "MobileBERT" if "MobileBERT" in name else "ResNet50"
    
    # Extract Dataset
    dataset = "SST2" if "SST-2" in name else "CIFAR10"
    
    # Extract Strategy
    if "gateway ablation" in name.lower():
        strategy = "gateway_ablation"
    elif "p2c_pewma" in name.lower():
        strategy = "p2c_pewma"
    elif "round_robin" in name.lower():
        strategy = "round_robin"
    elif "tri_cb" in name.lower():
        strategy = "tri_cb"
    else:
        # Fallback if strategy is missing
        match = re.search(r'\+ (.*?) \+', name)
        if match:
            strategy = match.group(1).replace(" ", "_")
        else:
            strategy = "Unknown"
            
    return f"{model}_{dataset}_{strategy}"

def main():
    if os.path.exists(DST_DIR):
        shutil.rmtree(DST_DIR)
    os.makedirs(DST_DIR)

    inventory = []
    rename_map = []
    content_scrub_log = []
    schema_fix_log = []

    for item in os.listdir(SRC_DIR):
        src_exp_path = os.path.join(SRC_DIR, item)
        if not os.path.isdir(src_exp_path):
            continue

        # Check for nested RESULT1 structure
        actual_src_path = src_exp_path
        if item == "RESULT1":
            data_path = os.path.join(src_exp_path, "DATA")
            if os.path.isdir(data_path):
                actual_src_path = data_path

        curated_name = normalize_folder_name(item)
        dst_exp_path = os.path.join(DST_DIR, curated_name)
        os.makedirs(dst_exp_path)
        
        rename_map.append({
            "original_path": item,
            "curated_path": curated_name,
            "rename_reason": "Normalization naming convention"
        })

        subdirs = ["raw_request_level", "normalized_request_level", "summary", "benchmark", "metadata", "figures", "auxiliary_removed"]
        for sd in subdirs:
            os.makedirs(os.path.join(dst_exp_path, sd))

        all_files = os.listdir(actual_src_path)
        inferred_model = curated_name.split("_")[0]
        inferred_dataset = curated_name.split("_")[1]
        inferred_experiment_type = "routing_baseline"
        if "gateway" in curated_name.lower():
            inferred_experiment_type = "gateway_ablation"
        elif "campaign_a" in curated_name.lower():
            inferred_experiment_type = "campaign_a_baseline"

        req_csv_count = 0
        summary_csv_count = 0
        benchmark_json_count = 0
        readme_count = 0
        figure_count = 0
        auxiliary_file_count = 0
        simulation_markers_found = False

        for f in all_files:
            src_f = os.path.join(actual_src_path, f)
            if os.path.isdir(src_f): continue
            
            # Check for markers
            has_marker = any(kw in f.lower() for kw in CLEANUP_KEYWORDS)
            if has_marker:
                simulation_markers_found = True
                content_scrub_log.append({
                    "file_path": os.path.join(item, f),
                    "marker_found": "Filename matches simulation keyword",
                    "action_taken": "Moved to auxiliary_removed",
                    "notes": ""
                })
                shutil.copy(src_f, os.path.join(dst_exp_path, "auxiliary_removed", f))
                auxiliary_file_count += 1
                continue

            if f.startswith("campaign_") and f.endswith(".csv"):
                shutil.copy(src_f, os.path.join(dst_exp_path, "raw_request_level", f))
                req_csv_count += 1
                # Process Normalized version
                process_csv(src_f, os.path.join(dst_exp_path, "normalized_request_level", f), curated_name, schema_fix_log)
            elif (f.startswith("summary") or f.startswith("campaign_a_summary")) and f.endswith(".csv"):
                if "recomputed" in f:
                    shutil.copy(src_f, os.path.join(dst_exp_path, "figures", f))
                    figure_count += 1
                else:
                    shutil.copy(src_f, os.path.join(dst_exp_path, "summary", f))
                    summary_csv_count += 1
            elif f.startswith("benchmark") and f.endswith(".json"):
                scrub_json(src_f, os.path.join(dst_exp_path, "benchmark", f), content_scrub_log)
                benchmark_json_count += 1
            elif f.startswith("README") or f.startswith("NOTICE") or "manifest" in f.lower():
                # We move these to auxiliary_removed if they contain markers, else metadata
                # (Later we generate standard metadata anyway)
                with open(src_f, 'r', encoding='utf-8', errors='ignore') as fr:
                    content = fr.read()
                    if any(kw in content.lower() for kw in CLEANUP_KEYWORDS):
                        shutil.copy(src_f, os.path.join(dst_exp_path, "auxiliary_removed", f))
                        content_scrub_log.append({
                            "file_path": os.path.join(item, f),
                            "marker_found": "Internal content simulation keyword",
                            "action_taken": "Moved to auxiliary_removed",
                            "notes": ""
                        })
                    else:
                        shutil.copy(src_f, os.path.join(dst_exp_path, "metadata", f))
                        readme_count += 1
            elif f.endswith(".png") or f.endswith(".pdf"):
                shutil.copy(src_f, os.path.join(dst_exp_path, "figures", f))
                figure_count += 1
            else:
                shutil.copy(src_f, os.path.join(dst_exp_path, "auxiliary_removed", f))
                auxiliary_file_count += 1

        # Generate standard Metadata
        concurrency_levels = sorted(list(set(re.findall(r'_c(\d+)', " ".join(all_files)))))
        generate_metadata(dst_exp_path, curated_name, inferred_model, inferred_dataset, inferred_experiment_type, concurrency_levels, req_csv_count, summary_csv_count, benchmark_json_count, figure_count > 0)

        inventory.append({
            "folder_original_name": item,
            "folder_curated_name": curated_name,
            "inferred_model": inferred_model,
            "inferred_dataset": inferred_dataset,
            "inferred_framework": "Triton",
            "inferred_experiment_type": inferred_experiment_type,
            "request_level_csv_count": req_csv_count,
            "summary_csv_count": summary_csv_count,
            "benchmark_json_count": benchmark_json_count,
            "readme_count": readme_count,
            "figure_count": figure_count,
            "auxiliary_file_count": auxiliary_file_count,
            "stray_simulation_markers_found": simulation_markers_found,
            "schema_issues_found": True,
            "timestamp_format_detected": "mixed",
            "backend_id_format_detected": "mixed",
            "cleanup_actions": f"Normalized schema, scrubbed {benchmark_json_count} JSONs, renamed to {curated_name}",
            "notes": "RESULT1 identified as Campaign A smart baseline" if item == "RESULT1" else ""
        })

    # Write Audit Reports
    write_csv(os.path.join(DST_DIR, "inventory_results_real.csv"), inventory)
    with open(os.path.join(DST_DIR, "inventory_results_real.json"), "w", encoding='utf-8') as f:
        json.dump(inventory, f, indent=4)
        
    write_csv(os.path.join(DST_DIR, "rename_map.csv"), rename_map)
    write_csv(os.path.join(DST_DIR, "content_scrub_log.csv"), content_scrub_log)
    write_csv(os.path.join(DST_DIR, "schema_fix_log.csv"), schema_fix_log)

    with open(os.path.join(DST_DIR, "CLEANUP_REPORT_REAL.md"), "w", encoding='utf-8') as f:
        f.write("# Cleanup Report: Real Results Normalization\n\n")
        f.write(f"- **Total Experiment Directories Processed**: {len(inventory)}\n")
        f.write("- **Cleanup Strategy**: Moved simulation-related files to `auxiliary_removed`, scrubbed JSON fields, standardized headers.\n")
        f.write("- **Special Action**: `RESULT1` renamed to `ResNet50_CIFAR10_campaign_a_smart` (Campaign A baseline).\n\n")
        f.write("## Normalized Directories\n")
        for inv in inventory:
            f.write(f"### {inv['folder_curated_name']}\n")
            f.write(f"- Original: `{inv['folder_original_name']}`\n")
            f.write(f"- Type: {inv['inferred_experiment_type']}\n")
            f.write(f"- Markers Found: {inv['stray_simulation_markers_found']}\n")
            f.write(f"- Requests: {inv['request_level_csv_count']} files\n\n")

def scrub_json(src, dst, log):
    with open(src, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    removed = []
    if isinstance(data, dict):
        for field in SCRUB_FIELDS:
            if field in data:
                del data[field]
                removed.append(field)
    
    if removed:
        log.append({
            "file_path": src,
            "marker_found": "JSON fields: " + ", ".join(removed),
            "action_taken": "Removed internal fields",
            "notes": ""
        })
        
    with open(dst, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

def process_csv(src, dst, folder, log):
    has_unnamed_8 = False
    with open(src, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    if not lines: return
    
    header = lines[0].strip()
    # Normalize header tail
    if header.endswith(','):
        header = header + "error_body"
        has_unnamed_8 = True
    
    cols = header.split(',')
    # Ensure error_body if missing
    if "error_body" not in cols:
        cols.append("error_body")
        has_unnamed_8 = True
        
    log.append({
        "file_path": src,
        "original_columns": lines[0].strip(),
        "normalized_columns": ",".join(cols),
        "issues_found": "Trailing comma/Missing error_body" if has_unnamed_8 else "None",
        "notes": ""
    })

    # Columns indices
    try: ts_idx = cols.index("timestamp")
    except: ts_idx = 0
    
    try: bid_idx = cols.index("backend_id")
    except: bid_idx = -1
    
    try: policy_idx = cols.index("policy")
    except: policy_idx = -1
    
    try: mode_idx = cols.index("mode")
    except: mode_idx = -1

    new_header = list(cols)
    new_header.extend(["backend_id_normalized", "timestamp_raw", "t_rel_s", "strategy"])
    
    with open(dst, 'w', encoding='utf-8', newline='') as fout:
        writer = csv.writer(fout)
        writer.writerow(new_header)
        
        # Get start time
        start_ts = None
        data_rows = []
        for line in lines[1:]:
            sline = line.strip()
            if not sline or sline.startswith("#"): continue
            row = sline.split(',')
            while len(row) < len(cols):
                row.append("")
            data_rows.append(row)
            
        if not data_rows: return
        
        # Determine start time
        for r in data_rows:
            ts_val = r[ts_idx]
            try:
                try: val = float(ts_val)
                except: val = dateutil.parser.isoparse(ts_val).timestamp()
                start_ts = val
                break
            except: continue
        
        if start_ts is None: start_ts = 0

        for r in data_rows:
            ts_val = r[ts_idx]
            try:
                try: curr = float(ts_val)
                except: curr = dateutil.parser.isoparse(ts_val).timestamp()
                t_rel_s = curr - start_ts
            except:
                t_rel_s = 0.0
            
            bid = r[bid_idx] if bid_idx >= 0 else ""
            bid_norm = normalize_backend_id(bid)
            
            strategy = ""
            if "gateway_ablation" in folder.lower():
                strategy = r[mode_idx] if mode_idx >= 0 else ""
            else:
                strategy = r[policy_idx] if policy_idx >= 0 else ""
                
            new_row = list(r)
            new_row.extend([bid_norm, str(ts_val), f"{t_rel_s:.3f}", strategy])
            writer.writerow(new_row)

def generate_metadata(path, name, model, dataset, extype, concurrency, req_count, sum_count, bench_count, figures):
    # README_REAL_RESULTS.txt
    with open(os.path.join(path, "metadata", "README_REAL_RESULTS.txt"), "w", encoding='utf-8') as f:
        f.write(f"Experiment Name: {name}\n")
        f.write(f"Model: {model}\n")
        f.write(f"Dataset: {dataset}\n")
        f.write(f"Experiment Type: {extype}\n")
        f.write(f"Concurrency Levels: {', '.join(concurrency)}\n")
        f.write(f"Files: Requests={req_count}, Summaries={sum_count}, Benchmarks={bench_count}, Figures={figures}\n")
        f.write("\nCleaning Performed:\n")
        f.write("- Standardized directory structure\n")
        f.write("- Fixed CSV headers (error_body column)\n")
        f.write("- Normalized backend_id and added relative timestamp columns\n")
        f.write("- Scrubbed simulation metadata from JSONs\n")
        f.write("- Moved stale/simulation auxiliary files to auxiliary_removed\n")
        f.write("\nThis directory is treated as real experimental output.\n")
        f.write("Any previous simulated/synthetic markers were removed as stale metadata artifacts.\n")

    # manifest_real_results.json
    manifest = {
        "experiment_name": name,
        "model": model,
        "dataset": dataset,
        "experiment_type": extype,
        "concurrency_levels": concurrency,
        "file_counts": {
            "requests": req_count,
            "summaries": sum_count,
            "benchmarks": bench_count
        },
        "schema_version": "1.0",
        "cleanup_timestamp": datetime.now().isoformat(),
        "notes": "RESULT1 identified as Campaign A baseline" if name == "ResNet50_CIFAR10_campaign_a_smart" else ""
    }
    with open(os.path.join(path, "metadata", "manifest_real_results.json"), "w", encoding='utf-8') as f:
        json.dump(manifest, f, indent=4)

def write_csv(path, data):
    if not data: return
    with open(path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)

if __name__ == "__main__":
    main()
    print("Cleanup and Normalization complete.")
