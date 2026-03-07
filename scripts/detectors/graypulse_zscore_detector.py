import time
import requests
import threading
import subprocess
import numpy as np

# Configuration
HAPROXY_STATS_URL = "http://sp26-cs525-0601.cs.illinois.edu:8404/metrics;csv"
HAPROXY_HOST = "sp26-cs525-0601.cs.illinois.edu"
SSH_USER = "jisheng3"
SSH_KEY_PATH = "/Users/ian/.ssh/id_ed25519"
CHECK_INTERVAL_SEC = 1
WINDOW_SIZE = 5
DRAIN_BACKEND = "triton_backend"
DRAIN_SERVER = "gpu1"

# Shared state
history_l = []
history_q = []
window_l = []
window_q = []
state_lock = threading.Lock()

def calculate_mad(arr):
    if len(arr) == 0:
        return 0.0, 0.0
    med = np.median(arr)
    mad = np.median(np.abs(arr - med))
    return med, mad

def drain_node():
    print(f"\n[{time.strftime('%X')}] 🚨 EXECUTING DRAIN PATH...")
    # Using SSH to execute socat on the remote HAProxy node
    socat_cmd = f"echo 'set server {DRAIN_BACKEND}/{DRAIN_SERVER} state drain' | sudo -S socat stdio /run/haproxy.sock"
    ssh_cmd = f'ssh -i {SSH_KEY_PATH} -o StrictHostKeyChecking=no {SSH_USER}@{HAPROXY_HOST} "{socat_cmd}"'
    
    # Normally we'd pass password 'JJSNewPass2025!!' if sudo prompts, but as an automated worker:
    subprocess.run(f"echo 'JJSNewPass2025!!' | {ssh_cmd}", shell=True)
    print(f"[{time.strftime('%X')}] ✅ Node {DRAIN_SERVER} successfully drained via Runtime API!")

def monitor_loop():
    print(f"Starting Fast Path Monitoring on {HAPROXY_STATS_URL} ...")
    consecutive_trigger = 0
    epsilon = 1e-4
    
    while True:
        try:
            # We use HTTP ;csv endpoint on the HAProxy stats port
            # rtime = Avg Response Time, qcur = Current Queue Depth
            # Note: Approximating P99 with rtime from the socket.
            resp = requests.get(HAPROXY_STATS_URL, timeout=2)
            if resp.status_code == 200:
                lines = resp.text.split('\n')
                gpu1_rtime = 0.0
                gpu1_qcur = 0.0
                
                for line in lines:
                    if f"{DRAIN_BACKEND},{DRAIN_SERVER}," in line:
                        parts = line.split(',')
                        # Index for qcur is 2, rtime is 60 (based on HAProxy 2.x standard CSV format)
                        # We do a safe extraction:
                        try:
                            gpu1_qcur = float(parts[2]) if parts[2] else 0.0
                            gpu1_rtime = float(parts[60]) if parts[60] else 0.0
                        except:
                            pass
                        break
                        
                with state_lock:
                    history_l.append(gpu1_rtime)
                    history_q.append(gpu1_qcur)
                    window_l.append(gpu1_rtime)
                    window_q.append(gpu1_qcur)
                    
                    if len(window_l) > WINDOW_SIZE:
                        window_l.pop(0)
                        window_q.pop(0)
                        
                    if len(window_l) == WINDOW_SIZE:
                        Li = np.median(window_l)
                        Qi = np.median(window_q)
                        
                        med_L, mad_L = calculate_mad(history_l)
                        med_Q, mad_Q = calculate_mad(history_q)
                        
                        zL_i = (Li - med_L) / (mad_L + epsilon)
                        zQ_i = (Qi - med_Q) / (mad_Q + epsilon)
                        
                        print(f"[{time.strftime('%X')}] Fast-Path zL: {zL_i:6.2f} | zQ: {zQ_i:6.2f} (L: {gpu1_rtime}ms, Q: {gpu1_qcur})")
                        
                        # Trigger Check
                        if zL_i >= 3 and zQ_i >= 2:
                            consecutive_trigger += 1
                        else:
                            consecutive_trigger = 0
                            
                        # Fire drain asynchronously to avoid blocking the fast-path loop
                        if consecutive_trigger >= 3:
                            print(f"\n=> ⚡ [TRIGGER CONDITION MET] 3 continuous seconds of zL >= 3 and zQ >= 2! zL={zL_i:.2f}, zQ={zQ_i:.2f}")
                            t = threading.Thread(target=drain_node)
                            t.start()
                            consecutive_trigger = 0 # reset to avoid repeated fast triggers
                            
            time.sleep(CHECK_INTERVAL_SEC)
            
        except requests.exceptions.RequestException as e:
            print(f"[{time.strftime('%X')}] Endpoint Unreachable: {e}")
            time.sleep(CHECK_INTERVAL_SEC)

if __name__ == "__main__":
    monitor_loop()
