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
    USER = "netid"
    BASE_URL = "sp26-cs525-06"
    DOMAIN = ".cs.illinois.edu"
    SSH_KEY_PATH = None

def check_server(vm_id):
    """Pings a single VM to see if it is online."""
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
        # Check standard ms output or ping TTL
        if match or ("TTL=" in output or "ttl=" in output):
            return vm_id, True
        return vm_id, False
            
    except Exception:
        return vm_id, False


def get_hardware_info(vm_id):
    """Connects via SSH to retrieve hardware and health information."""
    hostname = f"{BASE_URL}{vm_id:02d}{DOMAIN}"
    target = f"{USER}@{hostname}"
    
    bash_script = """
echo "[ CPU ]"
lscpu | grep "Model name" | cut -d':' -f2 | xargs
echo "[ CPU Cache ]"
lscpu | grep -i "cache:" | sed -e 's/^[ \t]*//' | tr '\\n' ',' | sed 's/,$//'
echo ""
echo "[ Memory ]"
free -h | awk 'NR==2{print "Total: "$2" | Free (Left): "$4" | Available: "$7" | RAM Cache: "$6}'
echo "[ GPU ]"
if command -v nvidia-smi >/dev/null 2>&1; then
    nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader
else
    VGA=$(lspci 2>/dev/null | grep -i -E 'vga|3d|display' | cut -d':' -f3)
    if [ -z "$VGA" ]; then echo "No dedicated GPU detected (or lspci missing)"; else echo "$VGA" | xargs; fi
fi
echo "[ Internal Storage (/) ]"
df -h / | awk 'NR==2{print "Total: "$2" | Used: "$3" ("$5") | Free: "$4}'
"""

    # We use BatchMode=yes so that it drops the connection instead of hanging on a password prompt forever over concurrent threads.
    ssh_cmd = ["ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=5"]
    if SSH_KEY_PATH:
        ssh_cmd.extend(["-i", SSH_KEY_PATH])
    ssh_cmd.append(target)
    ssh_cmd.append(bash_script)
    
    try:
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
        result = subprocess.run(ssh_cmd, capture_output=True, text=True, startupinfo=startupinfo, timeout=15)
        if result.returncode == 0:
            return vm_id, True, result.stdout.strip()
        else:
            return vm_id, False, f"SSH Error (Wait, did it prompt for a password or is SSH locked?): {result.stderr.strip()}"
    except subprocess.TimeoutExpired:
        return vm_id, False, "SSH command timed out after 15 seconds. The server took too long to respond."
    except Exception as e:
        return vm_id, False, f"Failed to execute command: {type(e).__name__}"


def main():
    print("=== UIUC CS525 Cluster Hardware & Health Monitor ===")
    print("🔍 Step 1/2: Pinging VMs 1-20 to locate active online servers...\n")
    
    online_vms = []
    
    # Ping 20 VMs concurrently.
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        future_to_vm = {executor.submit(check_server, i): i for i in range(1, 21)}
        for future in concurrent.futures.as_completed(future_to_vm):
            vm_id, is_online = future.result()
            if is_online:
                online_vms.append(vm_id)
                
    online_vms.sort()
    
    if not online_vms:
        print("❌ No VMs are reachable right now. Aborting.")
        return
        
    print(f"✅ Found {len(online_vms)} online VMs: {online_vms}")
    print("\n🔍 Step 2/2: Fetching hardware info via SSH concurrently...")
    print("💡 Note: Ensure your SSH keys are set up. This uses batch mode to avoid terminal hangs on password prompts.\n")
    
    results = []
    
    # Check Hardware concurrently for fast response.
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(online_vms)) as executor:
        future_to_info = {executor.submit(get_hardware_info, vm_id): vm_id for vm_id in online_vms}
        for future in concurrent.futures.as_completed(future_to_info):
            results.append(future.result())
            
    results.sort(key=lambda x: x[0])
    
    for vm_id, success, output in results:
        print("="*60)
        print(f"🖥️  VM {vm_id:02d} ({BASE_URL}{vm_id:02d}{DOMAIN})")
        print("="*60)
        if success:
            print(output)
        else:
            print(f"❌ Failed to retrieve info:\n{output}\n")
            print("Tip: If it failed because of SSH keys, ensure `SSH_KEY_PATH` is correctly configured in config.py.")
        print("\n")


if __name__ == "__main__":
    main()
