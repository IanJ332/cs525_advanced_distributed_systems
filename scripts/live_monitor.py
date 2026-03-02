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
    hostname = f"{BASE_URL}{vm_id:02d}{DOMAIN}"
    target = f"{USER}@{hostname}"
    
    if not check_reachable(hostname):
        return vm_id, "OFFLINE", "-", "-", "-", "-", "-"

    bash_script = """
cpu_model=$(lscpu | grep "Model name" | cut -d':' -f2 | xargs | awk '{print $1" "$2" "$3}')
cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print 100 - $8}')
total_mem=$(free -m | awk 'NR==2{print $2}')
used_mem=$(free -m | awk 'NR==2{print $3}')

if command -v nvidia-smi >/dev/null 2>&1; then
    gpu=$(nvidia-smi --query-gpu=name --format=csv,noheader | head -n 1)
else
    a10=$(lspci 2>/dev/null | grep -i -E 'a10|nvidia' | cut -d':' -f3 | xargs)
    if [ ! -z "$a10" ]; then gpu="$a10"; else gpu=$(lspci 2>/dev/null | grep -i -E 'vga|3d|display' | cut -d':' -f3 | xargs | cut -d' ' -f1-3); fi
fi
echo "${cpu_usage}|${cpu_model}|${used_mem}|${total_mem}|${gpu}"
"""
    
    # Increased ConnectTimeout to 5 seconds
    ssh_cmd = ["ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=5"]
    if SSH_KEY_PATH:
        ssh_cmd.extend(["-i", SSH_KEY_PATH])
    ssh_cmd.extend([target, bash_script])
    
    try:
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
        # Increased subprocess timeout to 10 seconds
        result = subprocess.run(ssh_cmd, capture_output=True, text=True, startupinfo=startupinfo, timeout=10)
        if result.returncode == 0:
            parts = result.stdout.strip().split('|')
            if len(parts) >= 5:
                return vm_id, "ONLINE", parts[0], parts[1], parts[2], parts[3], parts[4]
        return vm_id, "SSH BUSY", "-", "-", "-", "-", "Check Console"
    except subprocess.TimeoutExpired:
        return vm_id, "SSH TIMEOUT", "-", "-", "-", "-", "Slow response"
    except Exception:
        return vm_id, "ERROR", "-", "-", "-", "-", "Unknown"

def create_bar(used, total, width=15):
    if total == 0: return "[" + " "*width + "]"
    percent = used / total
    filled = int(round(width * percent))
    return "[" + ("#" * filled) + ("-" * (width - filled)) + f"] {percent*100:5.1f}%"

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def main():
    print("Starting Live Monitor (Gathering initial data...)")
    while True:
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            future_to_vm = {executor.submit(get_node_status, i): i for i in range(1, 21)}
            for future in concurrent.futures.as_completed(future_to_vm):
                results.append(future.result())
                
        results.sort(key=lambda x: x[0])
        
        clear_screen()
        print("=== 🚀 UIUC CS525 Cluster Live Monitor 🚀 ===")
        print(f"{'VM':<4} | {'Status':<10} | {'CPU %':<7} | {'RAM Usage':<35} | {'GPU Info'}")
        print("-" * 95)
        
        for res in results:
            vm_id, status, cpu_usage, cpu_model, used_mem, total_mem, gpu = res
            
            if status == "ONLINE":
                try:
                    cpu_val = float(cpu_usage)
                    cpu_str = f"{cpu_val:5.1f}%"
                except:
                    cpu_str = str(cpu_usage)[:7]
                    
                try:
                    used_val = float(used_mem)
                    total_val = float(total_mem)
                    if total_val == 0: total_val = 1  # prevent div/0
                    # Standardize sizes to Gigs if large
                    used_disp = f"{used_val/1024:.1f}G" if used_val > 1024 else f"{int(used_val)}M"
                    total_disp = f"{total_val/1024:.1f}G" if total_val > 1024 else f"{int(total_val)}M"
                    
                    mem_bar = create_bar(used_val, total_val, width=12)
                    mem_str = f"{used_disp:>5} / {total_disp:<5} {mem_bar}"
                except:
                    mem_str = f"{used_mem} / {total_mem}"
                    
                print(f"{vm_id:02d}   | ✅ {status:<8} | {cpu_str:<7} | {mem_str:<35} | {gpu}")
            else:
                print(f"{vm_id:02d}   | ❌ {status:<8} | {'-':<7} | {'-':<35} | -")
                
        print("-" * 95)
        print("Press Ctrl+C to exit. Refreshing every 5 seconds...")
        time.sleep(5)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        clear_screen()
        print("Exited Live Monitor.")
