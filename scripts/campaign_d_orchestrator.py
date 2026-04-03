import paramiko
import sys
import json
import time

MODES = ["strawman", "smart"]
GW_NODE = "sp26-cs525-0601.cs.illinois.edu"
LOAD_NODE = "sp26-cs525-0602.cs.illinois.edu"
USERNAME = "jisheng3"
PASSWORD = "JJSNewPass2025!!"

def run_remote_python(host, content, filename):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, username=USERNAME, password=PASSWORD)
    sftp = client.open_sftp()
    with sftp.file(filename, 'w') as f:
        f.write(content)
    client.close()

def execute_on_node(host, cmd):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, username=USERNAME, password=PASSWORD)
    stdin, stdout, stderr = client.exec_command(cmd)
    # Background execution helpers should not block if needed, but here we need results
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    client.close()
    return out, err

def run_campaign_d():
    print(f"BATTLE COMMENCED: Campaign D (12-Node CPU Cluster)")
    
    # 1. Prepare Gateway Code (VM 01)
    with open('scripts/gateway_dual_mode.py', 'r') as f:
        code_gw = f.read()
    run_remote_python(GW_NODE, code_gw, 'gateway_dual_mode.py')
    
    # 2. Prepare Bombard Code (VM 02)
    with open('scripts/bombard_engine.py', 'r') as f:
        code_bm = f.read()
    run_remote_python(LOAD_NODE, code_bm, 'bombard_engine.py')
    
    results_final = {}
    
    for mode in MODES:
        print(f"\n[PHASE] Testing {mode.upper()} Mode...")
        
        # Kill previous gateway
        execute_on_node(GW_NODE, "pkill -f gateway_dual_mode")
        
        # Start Gateway in background
        gw_client = paramiko.SSHClient()
        gw_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        gw_client.connect(GW_NODE, username=USERNAME, password=PASSWORD)
        gw_client.exec_command(f"python3 gateway_dual_mode.py --mode {mode} --port 8080 > gw_{mode}.log 2>&1")
        
        time.sleep(5) # Heat up
        
        # Start Bombardment
        print(f"Firing bombardment (Concurrency 10, 60s)...")
        # We run it synchronously to wait for results
        out, err = execute_on_node(LOAD_NODE, "python3 bombard_engine.py --concurrency 10")
        
        try:
            res_json = json.loads(out)
            results_final[mode] = res_json
        except:
            results_final[mode] = {"raw": out, "error": err}
            
        print(f"Result for {mode}: {results_final[mode]}")
        
    with open('campaign_d_results.json', 'w') as f:
        json.dump(results_final, f, indent=4)
        
    # Clean up
    execute_on_node(GW_NODE, "pkill -f gateway_dual_mode")
    print("\n[COMPLETE] Campaign D Final Data Collected.")

if __name__ == "__main__":
    run_campaign_d()
