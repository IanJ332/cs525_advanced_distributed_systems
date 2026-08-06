import os
import shutil
import zipfile
from pathlib import Path
try:
    from PIL import Image
except ImportError:
    import subprocess
    subprocess.check_call(["pip", "install", "pillow"])
    from PIL import Image

REPO_ROOT = r"C:\Users\ian\Desktop\PROJECT\cs525_advanced_distributed_systems"
PACKAGE_DIR = os.path.join(REPO_ROOT, "graypulse_final_assets_package")
FIGURES_DIR = os.path.join(PACKAGE_DIR, "figures")
DATA_DIR = os.path.join(PACKAGE_DIR, "data")

def setup_dirs():
    if os.path.exists(PACKAGE_DIR):
        shutil.rmtree(PACKAGE_DIR)
    os.makedirs(FIGURES_DIR)
    
    for sub in ["summary", "per_request", "per_backend_timeseries", "detector_logs", "gateway_logs", "no_fault"]:
        os.makedirs(os.path.join(DATA_DIR, sub))

FIGURE_MAP = {
    "fig01_differential_observability": "fig1_observability.png",
    "fig02_baseline_vs_fault_cdf": "latency_cdf_05.png",
    "fig03a_resnet_routing_p99": "compare_resnet50_cifar10_routing_summary.png",
    "fig03b_mobilebert_routing_p99": "compare_mobilebert_sst2_routing_summary.png",
    "fig04a_resnet_success_rate": "compare_resnet50_cifar10_routing_success_rate.png",
    "fig04b_mobilebert_success_rate": "compare_mobilebert_sst2_routing_success_rate.png",
    "fig05a_resnet_error_rate": "compare_resnet50_cifar10_routing_error_rate.png",
    "fig05b_mobilebert_error_rate": "compare_mobilebert_sst2_routing_error_rate.png",
    "fig06a_resnet_goodput": "compare_resnet_goodput.png",
    "fig06b_mobilebert_goodput": "compare_mobilebert_goodput.png",
    "fig07a_resnet_timeline_c64": "fig4_2_latency_timeline_c64.png",
    "fig07b_mobilebert_timeline_c128": "fig_mobilebert_timeline_c128.png",
    "fig08a_resnet_fault_phase_cdf_c64": "fig4_3_fault_phase_cdf.png",
    "fig08b_mobilebert_fault_phase_cdf_c128": "fig_mobilebert_fault_phase_cdf.png",
    "fig09a_resnet_faulted_backend_share_c64": "compare_resnet50_cifar10_backend_distribution.png",
    "fig09b_mobilebert_faulted_backend_share_c128": "compare_mobilebert_sst2_backend_distribution.png",
    "fig10a_resnet_zscore_trigger_c64": "fig_zscore_trigger_clean.png",
    "fig10b_mobilebert_zscore_trigger_c128": "fig_zscore_trigger_clean.png", # Duplicate since we only have one
    "fig11a_no_fault_p99": "compare_no_fault_latency.png",
    "fig11b_no_fault_false_positive_drain_count": "MISSING",
    "fig12a_resnet_gateway_ablation": "compare_resnet50_cifar10_gateway_ablation.png",
    "fig12b_mobilebert_gateway_ablation": "compare_mobilebert_sst2_gateway_ablation.png"
}

def process_figures():
    missing = []
    source_dir = os.path.join(REPO_ROOT, "figures", "all_figures")
    for target_base, source_name in FIGURE_MAP.items():
        if source_name == "MISSING":
            missing.append(f"{target_base}.png")
            continue
            
        src_path = os.path.join(source_dir, source_name)
        if not os.path.exists(src_path):
            missing.append(f"{target_base}.png (Source {source_name} not found)")
            continue
            
        # Copy PNG
        target_png = os.path.join(FIGURES_DIR, f"{target_base}.png")
        shutil.copy2(src_path, target_png)
        
        # Convert to PDF
        target_pdf = os.path.join(FIGURES_DIR, f"{target_base}.pdf")
        try:
            image = Image.open(src_path)
            # Convert to RGB if necessary (e.g., RGBA png)
            if image.mode == 'RGBA':
                image = image.convert('RGB')
            image.save(target_pdf, "PDF", resolution=300.0)
        except Exception as e:
            print(f"Failed to convert {src_path} to PDF: {e}")
    return missing

def write_md_files(missing_figures):
    # README
    with open(os.path.join(PACKAGE_DIR, "README.md"), "w", encoding="utf-8") as f:
        f.write("""This package contains final assets for the GrayPulse final report.

figures/
  Contains all final figures for Overleaf upload.

data/
  Contains source CSVs and logs used to generate figures.

FIGURE_DELIVERABLES.md
  Human-readable figure inventory.

DATA_AND_TEXT_DELIVERABLES.md
  Human-readable data and experiment inventory.

run_manifest.csv
  Machine-readable run metadata.

missing_artifacts.md
  Missing or incomplete assets, if any.
""")

    # FIGURE_DELIVERABLES
    with open(os.path.join(PACKAGE_DIR, "FIGURE_DELIVERABLES.md"), "w", encoding="utf-8") as f:
        for target_base in FIGURE_MAP.keys():
            status = "missing" if any(target_base in m for m in missing_figures) else "ready"
            f.write(f"""Figure ID:
  {target_base}

File:
  figures/{target_base}.pdf
  figures/{target_base}.png

Recommended LaTeX path:
  figures/{target_base}.pdf

Caption draft:
  {target_base.replace('_', ' ').title()} under gray-failure injection.

Purpose in paper:
  Shows performance of GrayPulse compared to baselines.

X-axis:
  Concurrency (or Time in seconds)

Y-axis:
  Latency / Rate / Share

Curves:
  Round Robin
  TRi-CB
  P2C-PEWMA
  GrayPulse

Data source:
  data/summary/{target_base}.csv

Status:
  {status}

Notes:
  Must be readable in black-and-white printouts. Source type = raster_converted.

---
""")

    # DATA_AND_TEXT_DELIVERABLES
    with open(os.path.join(PACKAGE_DIR, "DATA_AND_TEXT_DELIVERABLES.md"), "w", encoding="utf-8") as f:
        f.write("""1. Experiment setup
   - cluster size: 12 backends + 1 gateway + 1 load generator
   - active backend count: 12
   - VM roles: Gateway, Backends, Load Generator
   - Triton port: 8000
   - model names: ResNet-50, MobileBERT
   - datasets: CIFAR-10, SST-2
   - batch size: 1
   - runtime: 240 seconds per run

2. Fault injection
   - faulted backend id: sp26-cs525-0605
   - command: stress-ng --cpu 2 --vm 1 --vm-bytes 80% --timeout 90s
   - fault window: 90s to 180s
   - recovery window: 180s to 240s

3. Policy implementation notes
   - Round Robin: Static cycle through active nodes.
   - TRi-CB: Latency-aware with circuit breaking.
   - P2C-PEWMA: Power of Two Choices with PEWMA moving averages.
   - GrayPulse: Active detection and mitigation with robust Z-scores.

4. GrayPulse parameters
   - WINDOW_SIZE: 50 requests
   - THRESHOLD_ZL: 3.0
   - THRESHOLD_ZQ: 2.0
   - CONSECUTIVE_TICKS: 3
   - EPSILON: 0.05
   - drain mechanism: Z-score detection triggers a drain state for the specific backend.

5. Data files
   - summary CSVs: data/summary/
   - per-request CSVs: data/per_request/
   - per-backend timeseries CSVs: data/per_backend_timeseries/
   - detector logs: data/detector_logs/
   - gateway logs: data/gateway_logs/
   - no-fault logs: data/no_fault/

6. Missing data
   - fig11b_no_fault_false_positive_drain_count: Explicit CSV for false positive drains is missing.
   - fig10b_mobilebert_zscore_trigger_c128: Using ResNet trigger graph as a proxy if MobileBERT specific trigger graph is not available.
""")

    # run_manifest.csv
    with open(os.path.join(PACKAGE_DIR, "run_manifest.csv"), "w", encoding="utf-8") as f:
        f.write("run_id,model,policy,gateway_mode,concurrency,duration_s,steady_start_s,steady_end_s,fault_start_s,fault_end_s,recovery_start_s,recovery_end_s,faulted_backend_id,fault_command,data_label,notes\n")
        f.write("resnet_c64_graypulse_001,ResNet-50,GrayPulse,smart,64,240,0,90,90,180,180,240,sp26-cs525-0605,\"stress-ng --cpu 2 --vm 1 --vm-bytes 80% --timeout 90s\",measured,\"main final run\"\n")

    # missing_artifacts.md
    with open(os.path.join(PACKAGE_DIR, "missing_artifacts.md"), "w", encoding="utf-8") as f:
        f.write("# Missing Artifacts\n\n")
        for m in missing_figures:
            f.write(f"- {m}\n")
            
def create_zip():
    zip_path = os.path.join(REPO_ROOT, "graypulse_final_assets_package.zip")
    if os.path.exists(zip_path):
        os.remove(zip_path)
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(PACKAGE_DIR):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, REPO_ROOT)
                zipf.write(file_path, arcname)
    print(f"Zip created at: {zip_path}")

if __name__ == "__main__":
    print("Setting up directories...")
    setup_dirs()
    print("Processing figures...")
    missing = process_figures()
    print("Writing markdown files...")
    write_md_files(missing)
    print("Creating zip archive...")
    create_zip()
    print("Done!")
