import paramiko
import sys
import json
import time

GW_NODE = "sp26-cs525-0601.cs.illinois.edu"
LOAD_NODE = "sp26-cs525-0602.cs.illinois.edu"
WORKER_FALLIBLE = "sp26-cs525-0605.cs.illinois.edu"
USERNAME = "jisheng3"
PASSWORD = "JJSNewPass2025!!"

def remote_cmd(host, cmd):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, username=USERNAME, password=PASSWORD)
    return client.exec_command(cmd)

def run_campaign_a():
    print("🚀 CAMPAIGN A: CV KNEE SEARCH & GRAY FAILURE INJECTION")
    
    # Ensure Smart Gateway is running
    remote_cmd(GW_NODE, "pkill -f gateway_dual_mode; python3 gateway_dual_mode.py --mode smart --port 8080 > smart.log 2>&1 &")
    time.sleep(5)
    
    # Sync Campaign Engine
    with open('scripts/campaign_a_engine.py', 'r') as f:
        code = f.read()
    
    client_load = paramiko.SSHClient()
    client_load.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client_load.connect(LOAD_NODE, username=USERNAME, password=PASSWORD)
    sftp = client_load.open_sftp()
    with sftp.file('campaign_a_engine.py', 'w') as f:
        f.write(code)
    client_load.close()

    concurrencies = [16, 24, 32, 48, 64]
    
    for c in concurrencies:
        print(f"\n[SWEEP] Concurrency={c} | Duration 240s")
        out_file = f"campaign_a_cv_c{c}.csv"
        
        # Start Bombardment
        _, stdout_load, _ = remote_cmd(LOAD_NODE, f"python3 campaign_a_engine.py --concurrency {c} --duration 240 --output {out_file}")
        
        # Wait 90s for steady state, then inject failure
        print("Steady State Monitoring (90s)...")
        time.sleep(90)
        
        print("Injecting Gray Failure on VM 05 (90s)...")
        remote_cmd(WORKER_FALLIBLE, f"echo '{PASSWORD}' | sudo -S stress-ng --cpu 2 --vm 1 --vm-bytes 80% --timeout 90s")
        
        print("Waiting for final recovery phase...")
        # Now wait for the load engine to finish its 240s run
        stdout_load.read()
        
        print(f"Sweep C{c} Finished.")
        time.sleep(30) # Cool down
        
        print(f"Sweep C{c} Finished.")
        time.sleep(30) # Cool down
        
    print("\n[COMPLETE] Campaign A Physical Limits Mapping Finished.")

if __name__ == "__main__":
    run_campaign_a()
