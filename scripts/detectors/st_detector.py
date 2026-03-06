import time
import subprocess
import re
import numpy as np

# Configuration
LOG_FILE = "/var/log/haproxy.log"
SOCKET = "/run/haproxy.sock"
THRESHOLD_MS = 200
CONSECUTIVE_LIMIT = 5

def tail_haproxy_logs():
    """Generator to continuously read the HAProxy log."""
    process = subprocess.Popen(['tail', '-F', LOG_FILE], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    while True:
        line = process.stdout.readline()
        if not line:
            time.sleep(0.1)
            continue
        yield line.decode('utf-8')

def drain_server(backend, server):
    """Drain the server using HAProxy Runtime API (socat)."""
    cmd = f'echo "set server {backend}/{server} state drain" | socat stdio {SOCKET}'
    subprocess.run(cmd, shell=True)
    print(f"[{time.strftime('%X')}] 🚨 DRAIN TRIGGERED ON {backend}/{server}!")

def main():
    print("Starting Static Threshold Detector (ST)...")
    consecutive_highs = 0
    current_second = int(time.time())
    latencies_in_sec = []
    drained = False
    
    # regex to parse "%Tt=" from our custom HAProxy log format
    tt_regex = re.compile(r'%Tt=(\d+)ms')
    
    for line in tail_haproxy_logs():
        if drained:
            continue
            
        now = int(time.time())
        match = tt_regex.search(line)
        
        if match:
            latencies_in_sec.append(int(match.group(1)))
            
        if now > current_second:
            if latencies_in_sec:
                p99 = np.percentile(latencies_in_sec, 99)
                print(f"[{time.strftime('%X')}] P99 Latency: {p99:.1f}ms (Count: {len(latencies_in_sec)})")
                
                if p99 > THRESHOLD_MS:
                    consecutive_highs += 1
                else:
                    consecutive_highs = 0
                    
                if consecutive_highs >= CONSECUTIVE_LIMIT:
                    drain_server("triton_backend", "gpu1")
                    # Assuming we target gpu1 for the stress-ng fail injected node
                    drained = True
                    consecutive_highs = 0
            
            latencies_in_sec = []
            current_second = now

if __name__ == "__main__":
    main()
