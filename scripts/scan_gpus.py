import os
import sys
import subprocess
import concurrent.futures
import paramiko

# Load configuration
sys.path.append(os.path.join(os.getcwd(), 'scripts'))
import config
USER = getattr(config, 'USER', 'jisheng3')
BASE_URL = getattr(config, 'BASE_URL', 'sp26-cs525-06')
DOMAIN = getattr(config, 'DOMAIN', '.cs.illinois.edu')
PASSWORD = getattr(config, 'PASSWORD', 'JJSNewPass2025!!')

HOSTNAME_LIST = [f"{BASE_URL}{i:02d}{DOMAIN}" for i in range(1, 21)]

def check_node(target):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        # Check ping first
        param = '-n' if sys.platform.lower() == 'win32' else '-c'
        subprocess.check_output(['ping', param, '1', '-w', '1000', target], stderr=subprocess.STDOUT)
        
        # Check GPU via SSH
        client.connect(target, username=USER, password=PASSWORD, timeout=5)
        stdin, stdout, stderr = client.exec_command("lspci | grep -i -E 'nvidia|3d|vga'")
        lspci_out = stdout.read().decode().strip()
        client.close()
        
        # Filter out VMware SVGA
        gpu_info = []
        for line in lspci_out.splitlines():
            if "VMware" not in line:
                gpu_info.append(line)
        
        return target, True, "\n".join(gpu_info) if gpu_info else "No non-VMware GPU"
    except Exception:
        return target, False, "Offline or SSH failed"

def main():
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        future_to_node = {executor.submit(check_node, host): host for host in HOSTNAME_LIST}
        for future in concurrent.futures.as_completed(future_to_node):
            results.append(future.result())
    
    results.sort()
    for host, online, info in results:
        if online:
            print(f"{host}: {info}")
        else:
            print(f"{host}: OFFLINE")

if __name__ == "__main__":
    main()
