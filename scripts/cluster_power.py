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
    PASSWORD = getattr(config, 'PASSWORD', None)
except ImportError:
    USER = "netid"
    BASE_URL = "sp26-cs525-06"
    DOMAIN = ".cs.illinois.edu"
    SSH_KEY_PATH = None
    PASSWORD = None

def shutdown_node(vm_id):
    hostname = f"{BASE_URL}{vm_id:02d}{DOMAIN}"
    target = f"{USER}@{hostname}"
    
    # If a password is provided, use sudo -S to read from stdin
    if PASSWORD:
        cmd_str = f"echo '{PASSWORD}' | sudo -S poweroff"
    else:
        cmd_str = "sudo poweroff"
    
    ssh_cmd = ["ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=3"]
    if SSH_KEY_PATH:
        ssh_cmd.extend(["-i", SSH_KEY_PATH])
    ssh_cmd.extend([target, cmd_str])
    
    try:
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
        result = subprocess.run(ssh_cmd, capture_output=True, text=True, startupinfo=startupinfo, timeout=5)
        
        if result.returncode == 0:
            return vm_id, True, "Shutdown command sent successfully."
        else:
            # If the server is already shutting down or connection dropped immediately
            err = result.stderr.strip()
            if not err or "Connection closed" in err or "Terminated" in err:
                return vm_id, True, "Shutdown command accepted (Connection closed)."
            return vm_id, False, f"Failed: {err}"
            
    except subprocess.TimeoutExpired:
        # For a poweroff command, a timeout is EXCELLENT news. 
        # It means the OS accepted the command and immediately killed the network/SSH stack.
        return vm_id, True, "SENT (No response - server is likely shutting down)"
    except Exception as e:
        # Actual connection errors (like VM 10/20) will fall here
        msg = str(e)
        if "timed out" in msg.lower():
            return vm_id, False, "UNREACHABLE (Network timeout - VM might be stuck/frozen)"
        return vm_id, False, f"Error: {msg}"

def main():
    print("=== 🛑 UIUC CS525 Cluster Power Manager 🛑 ===")
    
    # Check for specific node argument
    target_vms = []
    if len(sys.argv) > 1:
        try:
            vm_id = int(sys.argv[1])
            if 1 <= vm_id <= 20:
                target_vms = [vm_id]
                print(f"⚠️ Target: Single VM {vm_id:02d}")
            else:
                print("❌ Error: VM ID must be between 1 and 20.")
                return
        except ValueError:
            print("❌ Usage: python cluster_power.py [node_number] (leave empty to shutdown ALL)")
            return
    else:
        target_vms = list(range(1, 21))
        print("🚨 WARNING: SHUTTING DOWN ALL NODES (1-20) 🚨")
        confirm = input("Are you sure? (y/n): ")
        if confirm.lower() != 'y':
            print("Aborted.")
            return

    print(f"🚀 Sending power-off signals to {len(target_vms)} nodes concurrently...\n")
    
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        future_to_vm = {executor.submit(shutdown_node, i): i for i in target_vms}
        for future in concurrent.futures.as_completed(future_to_vm):
            results.append(future.result())
            
    results.sort(key=lambda x: x[0])
    
    for vm_id, success, message in results:
        status = "✅ SENT" if success else "❌ FAIL"
        print(f"VM {vm_id:02d} | {status} | {message}")

    print("\nPower-off sequence complete. Use live_monitor.py to verify they go OFFLINE.")

if __name__ == "__main__":
    main()
