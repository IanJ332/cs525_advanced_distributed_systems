import os
import shutil

base_dir = r"c:\Users\ian\Desktop\PROJECT\cs525_advanced_distributed_systems"
data_dir = os.path.join(base_dir, "data")

structure = {
    "cluster_logs": [
        "cluster_test_results.txt",
        "final_results.txt",
        "gpu_scan_results.txt",
        "node05_ip.txt",
    ],
    "chaos_experiment": [
        r"scripts\chaos\latency_results.csv",
        r"scripts\chaos\haproxy_status.csv",
        r"scripts\chaos\experiment_results.tar.gz",
    ],
    "metrics": [
        "zscore_network_metrics.csv",
        r"scripts\detectors\summary_table.csv",
    ],
    "figures": [] # for any png or jpg files
}

for folder in structure.keys():
    os.makedirs(os.path.join(data_dir, folder), exist_ok=True)

# Find images
images = []
for root, _, files in os.walk(base_dir):
    if "data" in root or ".git" in root: continue
    for f in files:
        if f.endswith(".png") or f.endswith(".jpg"):
            images.append(os.path.join(root, f))

# Move files
for category, files in structure.items():
    for f in files:
        src = os.path.join(base_dir, f)
        if os.path.exists(src):
            dst = os.path.join(data_dir, category, os.path.basename(f))
            shutil.move(src, dst)
            print(f"Moved {src} to {dst}")

for src in images:
    dst = os.path.join(data_dir, "figures", os.path.basename(src))
    shutil.move(src, dst)
    print(f"Moved {src} to {dst}")

print("Done organizing data.")
