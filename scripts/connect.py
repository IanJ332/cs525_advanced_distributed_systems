import os
import sys
import subprocess
import concurrent.futures
import re

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
    print("⚠️  Warning: config.py not found. Using default/placeholder values.")
    print("💡 Hint: Copy scripts/config.py.example to scripts/config.py and fill in your info.")
    USER = "netid"
    BASE_URL = "sp26-cs525-06"
    DOMAIN = ".cs.illinois.edu"
    SSH_KEY_PATH = None


def check_server(vm_id):
    hostname = f"{BASE_URL}{vm_id:02d}{DOMAIN}"
    param_n = '-n' if sys.platform.lower() == 'win32' else '-c'
    param_w = '-w' if sys.platform.lower() == 'win32' else '-W'
    val_w = '1000' if sys.platform.lower() == 'win32' else '1'
    
    cmd = ['ping', param_n, '1', param_w, val_w, hostname]
    try:
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, universal_newlines=True, startupinfo=startupinfo)
        
        match = re.search(r'time[=<]\s*([0-9.]+)\s*ms', output, re.IGNORECASE)
        if match:
            latency = match.group(1) + " ms"
            return vm_id, True, latency
        elif "TTL=" in output or "ttl=" in output:
            return vm_id, True, "<unknown ms>"
        else:
            return vm_id, False, "Offline / Unreachable"
            
    except subprocess.CalledProcessError:
        return vm_id, False, "Offline / Unreachable"
    except Exception as e:
        return vm_id, False, "Error"

def scan_all_servers():
    print("🔍 Scanning VMs 1-20... Please wait.\n")
    print(f"{'VM ID':<10} | {'Status':<15} | {'Latency'}")
    print("-" * 45)
    
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        future_to_vm = {executor.submit(check_server, i): i for i in range(1, 21)}
        for future in concurrent.futures.as_completed(future_to_vm):
            results.append(future.result())
            
    # Sort by VM ID
    results.sort(key=lambda x: x[0])
    
    online_count = 0
    for vm_id, is_online, latency in results:
        status = "✅ Online" if is_online else "❌ Offline"
        if is_online:
            online_count += 1
        print(f"VM {vm_id:02d}    | {status:<15} | {latency}")
        
    print("-" * 45)
    print(f"Total Online: {online_count}/20\n")

def get_vm_connection():
    while True:
        print("--- UIUC CS525 Cluster Connector ---")
        try:
            # Obtain the user's input
            choice = input("Which VM do you want to connect to? (1-20, 'g' for GPU, 'x' to scan, 'q' to quit): ").strip()
            
            if choice.lower() == 'q':
                break
            elif choice.lower() == 'x':
                scan_all_servers()
                continue
            elif choice.lower() == 'g':
                target = f"{USER}@cc-login.campuscluster.illinois.edu"
                print(f"🚀 Connecting to Campus Cluster ({target})...")
                print("💡 Tip: Once logged in, use: srun --partition=eng-instruction --account=26sp-cs525s-eng --gres=gpu:A10:1 --pty bash")
                
                ssh_cmd = "ssh"
                if SSH_KEY_PATH:
                    ssh_cmd += f' -i "{SSH_KEY_PATH}"'
                
                os.system(f"{ssh_cmd} {target}")
                continue
    
            # (e.g., 1 -> 01)
            vm_id = int(choice)
            if 1 <= vm_id <= 20:
                target = f"{USER}@{BASE_URL}{vm_id:02d}{DOMAIN}"
                print(f"🚀 Connecting to Node {vm_id:02d} ({target})...")
                
                ssh_cmd = "ssh"
                if SSH_KEY_PATH:
                    ssh_cmd += f' -i "{SSH_KEY_PATH}"'
                
                os.system(f"{ssh_cmd} {target}")
    
            else:
                print("❌ Invalid range. Please enter a number between 1 and 20.")
                
        except ValueError:
            print("❌ Please enter a valid number or command.")

if __name__ == "__main__":
    get_vm_connection()