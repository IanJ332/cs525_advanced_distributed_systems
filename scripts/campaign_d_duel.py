import paramiko
import sys
import json
import time

GW_NODE = "sp26-cs525-0601.cs.illinois.edu"
LOAD_NODE = "sp26-cs525-0602.cs.illinois.edu"
USERNAME = "jisheng3"
PASSWORD = "JJSNewPass2025!!"

def execute_remote(host, cmd, get_output=True):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, username=USERNAME, password=PASSWORD)
    stdin, stdout, stderr = client.exec_command(cmd)
    if get_output:
        out = stdout.read().decode().strip()
        err = stderr.read().decode().strip()
        client.close()
        return out, err
    client.close()
    return None, None

def monitor_gw(host, duration=60):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, username=USERNAME, password=PASSWORD)
    
    cpu_peaks = []
    mem_peaks = []
    
    start_time = time.time()
    while time.time() - start_time < duration:
        # Get CPU and RAM using top-like command
        cmd = "ps -C python3 -o %cpu,rss --no-headers | sort -rk 1 | head -n 1"
        stdin, stdout, stderr = client.exec_command(cmd)
        res = stdout.read().decode().strip()
        if res:
            parts = res.split()
            if len(parts) >= 2:
                cpu_peaks.append(float(parts[0]))
                mem_peaks.append(float(parts[1]) / 1024.0) # MB
        time.sleep(2)
        
    client.close()
    if not cpu_peaks: return 0, 0
    return max(cpu_peaks), max(mem_peaks)

def run_battle():
    print("🔥 OPERATION DAWN COMMENCED: THE ARCHITECTURE DUEL")
    
    # 1. Test 0: Warm-up
    print("\n[PHASE 0] Warm-up (Concurrency 1)...")
    execute_remote(GW_NODE, "pkill -f gateway_dual_mode; python3 gateway_dual_mode.py --mode smart --port 8080 > gw_warmup.log 2>&1 &", False)
    time.sleep(5)
    execute_remote(LOAD_NODE, "python3 bombard_engine.py --concurrency 1 > warmup.json")
    print("Warm-up Complete.")

    results = {}

    for mode in ["strawman", "smart"]:
        print(f"\n[PHASE] Testing {mode.upper()} Architecture...")
        execute_remote(GW_NODE, "pkill -f gateway_dual_mode", False)
        time.sleep(2)
        execute_remote(GW_NODE, f"python3 gateway_dual_mode.py --mode {mode} --port 8080 > {mode}.log 2>&1 &", False)
        time.sleep(5)
        
        # Start bombardment and monitoring in parallel
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            bombard_future = executor.submit(execute_remote, LOAD_NODE, f"python3 bombard_engine.py --concurrency 16 > {mode}_metrics.json")
            monitor_future = executor.submit(monitor_gw, GW_NODE, duration=60)
            
            # Wait for both
            bombard_out, _ = bombard_future.result()
            peak_cpu, peak_mem = monitor_future.result()
            
            try:
                metrics = json.loads(bombard_out)
                results[mode] = {
                    "stats": metrics,
                    "peak_cpu": peak_cpu,
                    "peak_mem_mb": peak_mem
                }
            except:
                results[mode] = {"raw": bombard_out, "peak_cpu": peak_cpu, "peak_mem_mb": peak_mem}
                
        print(f"Results for {mode.upper()}: CPU={peak_cpu}%, MEM={peak_mem}MB, P99={results[mode].get('stats', {}).get('p99_ms', 'N/A')}ms")

    with open('campaign_d_duel_results.json', 'w') as f:
        json.dump(results, f, indent=4)
        
    print("\n[COMPLETE] All Campaigns Finished. Final Data Synchronized.")

if __name__ == "__main__":
    run_battle()
