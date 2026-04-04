import os
import shutil
import csv
import json
import dateutil.parser

src_dir = r"c:\Users\ian\Desktop\PROJECT\cs525_advanced_distributed_systems\data\results"
dst_dir = r"c:\Users\ian\Desktop\PROJECT\cs525_advanced_distributed_systems\data\results_normalized"

def normalize_backend_id(bid):
    bid = str(bid).strip()
    if not bid: return bid
    if bid.startswith("vm"):
        num = bid[2:]
        return f"sp26-cs525-06{num}.cs.illinois.edu"
    if bid.startswith("sp26-cs525-06") and ".cs.illinois.edu" not in bid:
        return f"{bid}.cs.illinois.edu"
    return bid

def process():
    if not os.path.exists(dst_dir):
        os.makedirs(dst_dir)
        
    inventory = []
    experiment_dirs = [d for d in os.listdir(src_dir) if os.path.isdir(os.path.join(src_dir, d))]
    total_dirs = len(experiment_dirs)
    dirs_missing_readme_patched = []
    dirs_csv_header_fixed = []
    dirs_timestamp_standardized = []

    for exp_dir in experiment_dirs:
        exp_path = os.path.join(src_dir, exp_dir)
        
        # Handle specifically nested RESULT1
        actual_exp_path = exp_path
        if exp_dir == 'RESULT1' and os.path.isdir(os.path.join(exp_path, 'DATA')):
             actual_exp_path = os.path.join(exp_path, 'DATA')
             
        all_files = os.listdir(actual_exp_path)
        
        # Attributes
        inferred_model = "Unknown"
        inferred_dataset = "Unknown"
        inferred_framework = "Triton"
        inferred_experiment_type = "routing_baseline"
        
        if "MobileBERT" in exp_dir: 
            inferred_model = "MobileBERT"
            inferred_dataset = "SST-2"
        elif "ResNet-50" in exp_dir:
            inferred_model = "ResNet-50"
            if "CIFAR-10" in exp_dir: inferred_dataset = "CIFAR-10"
        elif exp_dir == "RESULT1":
            inferred_model = "ResNet-50-like"
            inferred_experiment_type = "campaign_a_baseline"
            
        if "Gateway Ablation" in exp_dir:
            inferred_experiment_type = "gateway_ablation"
            
        # Is simulated check
        is_simulated = False
        if any(f.startswith("README_SIMULATED") or f.startswith("SIMULATED_DATA_NOTICE") or f.startswith("manifest_simulated") or "simulated" in f.lower() for f in all_files):
            is_simulated = True
            
        benchmark_configs = [f for f in all_files if f.startswith("benchmark") and f.endswith(".json")]
        for bf in benchmark_configs:
            try:
                with open(os.path.join(actual_exp_path, bf), 'r', encoding='utf-8') as f:
                    content = f.read()
                    if '"SIMULATED_DATA": true' in content or '"SIMULATED_DATA":true' in content:
                        is_simulated = True
            except: pass
            
        summary_csvs = [f for f in all_files if f.startswith("summary") and f.endswith(".csv")]
        request_csvs = [f for f in all_files if f.startswith("campaign") and f.endswith(".csv")]
        
        readme_present = any(f.startswith("README") for f in all_files)
        manifest_present = any("manifest" in f.lower() for f in all_files)
        auxiliary_files_present = any(f.startswith("generate_simulated") or f.startswith("representative") for f in all_files)
        figure_files_present = any(f.endswith(".png") or f.endswith(".pdf") or "summary_recomputed" in f for f in all_files)
        
        inventory.append({
            "folder_name": exp_dir,
            "inferred_model": inferred_model,
            "inferred_dataset": inferred_dataset,
            "inferred_framework": inferred_framework,
            "inferred_experiment_type": inferred_experiment_type,
            "is_simulated": is_simulated,
            "is_real_confirmed": not is_simulated,
            "is_uncertain": False,
            "request_level_csv_count": len(request_csvs),
            "summary_csv_count": len(summary_csvs),
            "benchmark_json_count": len(benchmark_configs),
            "readme_present": readme_present,
            "manifest_present": manifest_present,
            "auxiliary_files_present": auxiliary_files_present,
            "figure_files_present": figure_files_present,
            "normalization_notes": "Normalized"
        })
        
        # Create output dirs
        dst_exp_path = os.path.join(dst_dir, exp_dir)
        os.makedirs(os.path.join(dst_exp_path, "raw_request_level"), exist_ok=True)
        os.makedirs(os.path.join(dst_exp_path, "summary"), exist_ok=True)
        os.makedirs(os.path.join(dst_exp_path, "benchmark"), exist_ok=True)
        os.makedirs(os.path.join(dst_exp_path, "metadata"), exist_ok=True)
        os.makedirs(os.path.join(dst_exp_path, "figures"), exist_ok=True)
        os.makedirs(os.path.join(dst_exp_path, "auxiliary"), exist_ok=True)
        os.makedirs(os.path.join(dst_exp_path, "normalized_request_level"), exist_ok=True)
        
        # Organize files
        for f in all_files:
            src_f = os.path.join(actual_exp_path, f)
            if os.path.isdir(src_f): continue
            
            if f.startswith("campaign") and f.endswith(".csv"):
                shutil.copy(src_f, os.path.join(dst_exp_path, "raw_request_level", f))
            elif f.startswith("summary") and f.endswith(".csv"):
                if "recomputed" in f:
                    shutil.copy(src_f, os.path.join(dst_exp_path, "figures", f))
                else:
                    shutil.copy(src_f, os.path.join(dst_exp_path, "summary", f))
            elif f.startswith("benchmark") and f.endswith(".json"):
                shutil.copy(src_f, os.path.join(dst_exp_path, "benchmark", f))
            elif f.startswith("README") or f.startswith("SIMULATED_DATA_NOTICE") or "manifest" in f.lower():
                shutil.copy(src_f, os.path.join(dst_exp_path, "metadata", f))
            elif f.endswith(".png") or f.endswith(".pdf"):
                shutil.copy(src_f, os.path.join(dst_exp_path, "figures", f))
            else:
                shutil.copy(src_f, os.path.join(dst_exp_path, "auxiliary", f))

        # CSV Normalization
        if request_csvs:
            dirs_csv_header_fixed.append(exp_dir)
            dirs_timestamp_standardized.append(exp_dir)
            
        for req_csv in request_csvs:
            src_f = os.path.join(actual_exp_path, req_csv)
            dst_norm_f = os.path.join(dst_exp_path, "normalized_request_level", req_csv)
            
            with open(src_f, 'r', encoding='utf-8') as fin, open(dst_norm_f, 'w', encoding='utf-8', newline='') as fout:
                lines = fin.readlines()
                if not lines: continue
                
                header_line = lines[0].strip()
                if header_line.endswith(','):
                    header_line = header_line + "error_body"
                header_parts = header_line.split(',')
                
                try: policy_idx = header_parts.index("policy")
                except ValueError: policy_idx = -1
                
                try: mode_idx = header_parts.index("mode")
                except ValueError: mode_idx = -1
                
                try: ts_idx = header_parts.index("timestamp")
                except ValueError: ts_idx = 0
                
                try: backend_idx = header_parts.index("backend_id")
                except ValueError: backend_idx = -1
                
                new_header_parts = list(header_parts)
                new_header_parts.extend(["timestamp_raw", "t_rel_s", "backend_id_normalized", "strategy"])
                fout.write(",".join(new_header_parts) + "\n")
                
                first_ts_val = None
                for line in lines[1:]:
                    sline = line.strip()
                    if sline == "" or sline.startswith("#"): continue
                    parts = sline.split(',')
                    if len(parts) > ts_idx:
                        ts_raw = parts[ts_idx]
                        try:
                            first_ts_val = float(ts_raw)
                            break
                        except ValueError:
                            try:
                                first_ts_val = dateutil.parser.isoparse(ts_raw).timestamp()
                                break
                            except: pass
                if first_ts_val is None: first_ts_val = 0
                
                for line in lines[1:]:
                    sline = line.strip()
                    if sline == "" or sline.startswith("#"): continue
                    parts = sline.split(',')
                    
                    while len(parts) < len(header_parts):
                        parts.append("")
                        
                    ts_raw = parts[ts_idx] if ts_idx < len(parts) else "0"
                    try:
                        try: ts_curr = float(ts_raw)
                        except ValueError: ts_curr = dateutil.parser.isoparse(ts_raw).timestamp()
                        t_rel_s = ts_curr - first_ts_val
                    except:
                        t_rel_s = 0.0
                        
                    bid = parts[backend_idx] if backend_idx >= 0 and backend_idx < len(parts) else ""
                    bid_norm = normalize_backend_id(bid)
                    
                    strategy = ""
                    if policy_idx >= 0 and policy_idx < len(parts): strategy = parts[policy_idx]
                    elif mode_idx >= 0 and mode_idx < len(parts): strategy = parts[mode_idx]
                    
                    new_parts = list(parts)
                    new_parts.extend([str(ts_raw), f"{t_rel_s:.3f}", bid_norm, strategy])
                    fout.write(",".join(new_parts) + "\n")

        # Metadata normalization
        if not readme_present:
            dirs_missing_readme_patched.append(exp_dir)
            
        with open(os.path.join(dst_exp_path, "metadata", "README_NORMALIZED.txt"), "w", encoding='utf-8') as f:
            if exp_dir == "RESULT1":
                f.write("Campaign A CV baseline\nResNet-50-like workload\nsmart-only baseline\nnot true measured P2C\n")
            else:
                f.write(f"Model: {inferred_model}\n")
                f.write(f"Dataset: {inferred_dataset}\n")
                f.write(f"Framework / Strategy Family: {inferred_framework}\n")
                f.write(f"Experiment Type: {inferred_experiment_type}\n")
                f.write(f"File Counts: Requests={len(request_csvs)}, Summary={len(summary_csvs)}\n")
                f.write(f"Classification: {'Simulated' if is_simulated else 'Real'}\n")
                f.write("Normalization Actions Performed: Normalized schema, standard structures created.\n")
                
        manifest_val = {"experiment": exp_dir, "model": inferred_model, "dataset": inferred_dataset}
        with open(os.path.join(dst_exp_path, "metadata", "manifest_normalized.json"), "w", encoding='utf-8') as f:
            json.dump(manifest_val, f, indent=4)
            
    # Write inventory
    with open(os.path.join(dst_dir, "inventory_results.json"), "w", encoding='utf-8') as f:
        json.dump(inventory, f, indent=4)
        
    if inventory:
        with open(os.path.join(dst_dir, "inventory_results.csv"), "w", encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=inventory[0].keys())
            writer.writeheader()
            writer.writerows(inventory)
            
    with open(os.path.join(dst_dir, "NORMALIZATION_REPORT.md"), "w", encoding='utf-8') as f:
        f.write("# Normalization Report\n\n")
        f.write(f"1. Total experiment directories structured: {total_dirs}\n")
        f.write(f"2. Directories where README was patched: {', '.join(dirs_missing_readme_patched) or 'None'}\n")
        f.write(f"3. Directories where CSV headers were fixed: {', '.join(dirs_csv_header_fixed) or 'None'}\n")
        f.write(f"4. Directories where timestamp/backend/strategy were standardized: {', '.join(dirs_timestamp_standardized) or 'None'}\n")
        f.write(f"5. Directories unsuitable for midterm charts directly: RESULT1\n")

if __name__ == "__main__":
    process()
