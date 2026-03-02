import time
import os
import sys
import subprocess
import concurrent.futures

# Try to load configuration from config.py
try:
    if os.path.dirname(__file__) not in sys.path:
        sys.path.append(os.path.dirname(__file__))
    import config
    USER = getattr(config, 'USER', 'netid')
    BASE_URL = getattr(config, 'BASE_URL', 'sp26-cs525-06')
    DOMAIN = getattr(config, 'DOMAIN', '.cs.illinois.edu')
    SSH_KEY_PATH = getattr(config, 'SSH_KEY_PATH', None)
except ImportError:
    USER = "netid"
    BASE_URL = "sp26-cs525-06"
    DOMAIN = ".cs.illinois.edu"
    SSH_KEY_PATH = None

def check_reachable(hostname):
    """Fast ping check."""
    param = '-n' if sys.platform.lower() == 'win32' else '-c'
    cmd = ['ping', param, '1', '-w', '1000', hostname]
    try:
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, startupinfo=startupinfo, check=True)
        return True
    except:
        return False

def get_node_status(vm_id):
    if vm_id == 99:
        hostname = "cc-login.campuscluster.illinois.edu"
        display_name = "GPU"
    else:
        hostname = f"{BASE_URL}{vm_id:02d}{DOMAIN}"
        display_name = f"{vm_id:02d}"
        
    target = f"{USER}@{hostname}"
    
    if not check_reachable(hostname):
        return display_name, "OFFLINE", "-", "-", "-", "-", "-", "-", "-", "-"

    # Script remains the same, queries hardware info
    bash_script = """
cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print 100 - $8}')
total_mem=$(free -m | awk 'NR==2{print $2}')
used_mem=$(free -m | awk 'NR==2{print $3}')

if command -v nvidia-smi >/dev/null 2>&1; then
    gpu_data=$(nvidia-smi --query-gpu=name,utilization.gpu,memory.used,memory.total,temperature.gpu --format=csv,noheader,nounits | head -n 1)
else
    gpu_data="-,0,0,0,0"
fi
echo "${cpu_usage}|${used_mem}|${total_mem}|${gpu_data}"
"""
    
    ssh_cmd = ["ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=6"]
    if SSH_KEY_PATH:
        ssh_cmd.extend(["-i", SSH_KEY_PATH])
    ssh_cmd.extend([target, bash_script])
    
    try:
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
        result = subprocess.run(ssh_cmd, capture_output=True, text=True, startupinfo=startupinfo, timeout=12)
        if result.returncode == 0:
            parts = result.stdout.strip().split('|')
            if len(parts) >= 4:
                cpu_u = parts[0]
                ram_u = parts[1]
                ram_t = parts[2]
                g_parts = parts[3].split(',')
                # g_parts: [name, util, v_used, v_total, temp]
                return display_name, "ONLINE", cpu_u, ram_u, ram_t, g_parts[0].strip(), g_parts[1].strip(), g_parts[2].strip(), g_parts[3].strip(), g_parts[4].strip()
        return display_name, "SSH BUSY", "-", "-", "-", "-", "-", "-", "-", "-"
    except Exception:
        return display_name, "SSH TIMEOUT", "-", "-", "-", "-", "-", "-", "-", "-"

def create_bar(used, total, width=10):
    try:
        u, t = float(used), float(total)
        if t <= 0: return "[" + " "*width + "]  0.0%"
        percent = u / t
        filled = int(round(width * percent))
        return "[" + ("#" * filled) + ("-" * (width - filled)) + f"] {percent*100:5.1f}%"
    except:
        return "[" + " "*width + "]  --%"

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def main():
    print("Starting Deep GPU/Cluster Live Monitor...")
    # Standard VMs (1-20) + Special GPU Node (99)
    monitor_ids = list(range(1, 21)) + [99]
    
    while True:
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=21) as executor:
            future_to_vm = {executor.submit(get_node_status, i): i for i in monitor_ids}
            for future in concurrent.futures.as_completed(future_to_vm):
                results.append(future.result())
                
        # Sorting logic: Numbers first, then named tags
        results.sort(key=lambda x: (int(x[0]) if x[0].isdigit() else 999))
        
        clear_screen()
        print("=== 🚀 UIUC CS525 Deep Resource Monitor 🚀 ===")
        header = f"{'ID':<3} | {'Status':<11} | {'CPU%':<6} | {'RAM Usage (Used/Total)':<32} | {'GPU Util':<10} | {'VRAM Usage'}"
        print(header)
        print("-" * len(header))
        
        for res in results:
            vm_id, status, cpu_u, ram_u, ram_t, g_name, g_util, g_v_u, g_v_t, g_temp = res
            
            if status == "ONLINE":
                # CPU / RAM
                ram_bar = create_bar(ram_u, ram_t, width=10)
                # GPU Formatting
                if g_name != "-":
                    g_util_str = f"{g_util:>3}% {g_temp:>2}C"
                    vram_bar = create_bar(g_v_u, g_v_t, width=10)
                else:
                    g_util_str = "-"
                    vram_bar = "-"

                print(f"{vm_id:3} | ✅ ONLINE   | {cpu_u:>4}% | {ram_u:>5}M/{ram_t:<5}M {ram_bar} | {g_util_str:<10} | {vram_bar}")
            else:
                color_icon = "❌" if "OFFLINE" in status else "⚠️"
                print(f"{vm_id:3} | {color_icon} {status:<10} | {'-':<5} | {'-':<32} | {'-':<10} | -")
                
        print("-" * len(header))
        print(f"Refreshed at {time.strftime('%H:%M:%S')}. Press Ctrl+C to exit.")
        time.sleep(5)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        clear_screen()
        print("Exited Live Monitor.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        clear_screen()
        print("Exited Live Monitor.")
