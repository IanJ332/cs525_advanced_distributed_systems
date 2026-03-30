import os
import sys
import subprocess
import concurrent.futures
import paramiko
import time

# Load configuration from scripts/config.py
try:
    sys.path.append(os.path.join(os.getcwd(), 'scripts'))
    import config
    USER = getattr(config, 'USER', 'jisheng3')
    BASE_URL = getattr(config, 'BASE_URL', 'sp26-cs525-06')
    DOMAIN = getattr(config, 'DOMAIN', '.cs.illinois.edu')
    PASSWORD = getattr(config, 'PASSWORD', 'JJSNewPass2025!!')
except ImportError:
    USER = "jisheng3"
    BASE_URL = "sp26-cs525-06"
    DOMAIN = ".cs.illinois.edu"
    PASSWORD = "JJSNewPass2025!!"

# Define the targets: sp26-cs525-0601 through sp26-cs525-0620
HOSTNAME_LIST = [f"{BASE_URL}{i:02d}{DOMAIN}" for i in range(1, 21)]

def test_ping(target):
    """Pings a target (IP or hostname) to see if it is online."""
    param = '-n' if sys.platform.lower() == 'win32' else '-c'
    cmd = ['ping', param, '1', '-w', '1000', target]
    try:
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        
        subprocess.check_output(cmd, stderr=subprocess.STDOUT, universal_newlines=True, startupinfo=startupinfo)
        return target, True
    except Exception:
        return target, False

def check_gpu(target):
    """Checks for GPU connectivity using nvidia-smi and lspci via SSH."""
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        # Use password for nodes as the user provided it explicitly.
        client.connect(target, username=USER, password=PASSWORD, timeout=10)
        
        # Try nvidia-smi first
        stdin, stdout, stderr = client.exec_command("nvidia-smi --query-gpu=name --format=csv,noheader")
        result_nv = stdout.read().decode().strip()
        
        if result_nv:
            client.close()
            return target, True, f"NVIDIA GPU: {result_nv}"
        
        # If nvidia-smi fails, try lspci to see if the hardware is at least present
        stdin, stdout, stderr = client.exec_command("lspci | grep -i -E 'vga|3d|display|nvidia'")
        result_lspci = stdout.read().decode().strip()
        client.close()
        
        if result_lspci:
            return target, True, f"Hardware detected via lspci: {result_lspci} (Drivers might be missing)"
        else:
            return target, False, "No GPU related hardware found in lspci or nvidia-smi."
            
    except Exception as e:
        return target, False, f"SSH/Connection Error: {str(e)}"

def main():
    print(f"=== Distributed System Cluster Connectivity & GPU Test ===")
    print(f"User: {USER}")
    print(f"Starting connectivity check for nodes 01-20 using FQDNs...\n")

    # Step 1: Ping all nodes
    results_ping = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        future_to_ping = {executor.submit(test_ping, host): host for host in HOSTNAME_LIST}
        for future in concurrent.futures.as_completed(future_to_ping):
            results_ping.append(future.result())
    
    results_ping.sort()
    
    online_count = 0
    print(f"{'Hostname':<35} | {'Status'}")
    print("-" * 50)
    for host, is_online in results_ping:
        status = "ONLINE" if is_online else "OFFLINE"
        if is_online:
            online_count += 1
        print(f"{host:<35} | {status}")
    
    print("-" * 50)
    print(f"Total Online: {online_count}/20\n")

    # Step 2: Check GPUs for Node 05 and Node 06
    gpu_nodes = [f"{BASE_URL}05{DOMAIN}", f"{BASE_URL}06{DOMAIN}"]
    print(f"Checking GPU connectivity on nodes 05 and 06 specifically...")
    
    results_gpu = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        future_to_gpu = {executor.submit(check_gpu, host): host for host in gpu_nodes}
        for future in concurrent.futures.as_completed(future_to_gpu):
            results_gpu.append(future.result())
            
    results_gpu.sort()
    
    for host, has_gpu, info in results_gpu:
        print("="*60)
        print(f"Node {host}")
        if has_gpu:
            print(f"GPU DETECTED: {info}")
        else:
            print(f"GPU CHECK FAILED: {info}")
    print("="*60)

if __name__ == "__main__":
    main()
