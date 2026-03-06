import time
import subprocess

# Configuration
# Assuming SSH access to ingress node without password if running on inference node
# OR if running on Control Layer, connecting to both Infer & Ingress
INGRESS_HOST = "sp26-cs525-0601.cs.illinois.edu" # Active HAProxy
SOCKET = "/run/haproxy.sock"

# GPU Thresholds
GPU_LOAD_THRESHOLD = 90 # percentage
CONSECUTIVE_LIMIT = 3
CHECK_INTERVAL_SEC = 2

def get_gpu_utilization():
    """Fetch GPU Volatile Utilization from nvidia-smi."""
    try:
        res = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=utilization.gpu", "--format=csv,noheader,nounits"],
            text=True
        )
        # return the max utilization across GPUs or specific one
        utils = [int(u.strip()) for u in res.strip().split('\n')]
        return max(utils)
    except Exception as e:
        print(f"Error reading GPU util: {e}")
        return 0

def remote_drain_haproxy(backend, server):
    """Use SSH and socat remote execution to drain node from HAProxy pool."""
    cmd = f'ssh {INGRESS_HOST} "echo \\"set server {backend}/{server} state drain\\" | sudo socat stdio {SOCKET}"'
    subprocess.run(cmd, shell=True)
    print(f"[{time.strftime('%X')}] 🚥 GUA DRAIN TRIGGERED for {server} at HAProxy!")

def main():
    print("Starting GPU-Aware Detector (GUA) on Inference Node...")
    consecutive_highs = 0
    drained = False
    
    while True:
        if drained:
            time.sleep(10)
            continue
            
        util = get_gpu_utilization()
        print(f"[{time.strftime('%X')}] Current GPU Utilization: {util}%")
        
        if util > GPU_LOAD_THRESHOLD:
            consecutive_highs += 1
            print(f"   -> Over threshold ({consecutive_highs}/{CONSECUTIVE_LIMIT})")
        else:
            consecutive_highs = 0
            
        if consecutive_highs >= CONSECUTIVE_LIMIT:
            # Drain self (assuming we are gpu1)
            remote_drain_haproxy("triton_backend", "gpu1")
            drained = True
            
        time.sleep(CHECK_INTERVAL_SEC)

if __name__ == "__main__":
    main()
