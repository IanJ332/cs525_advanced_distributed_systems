import time
import requests
import subprocess
import json

HAPROXY_METRICS = "http://localhost:8404/metrics"
SOCKET = "/run/haproxy.sock"
ERROR_RATE_THRESHOLD = 0.05 # 5% 5xx errors
CONSECUTIVE_LIMIT = 5

def get_haproxy_errors():
    """Simulates grabbing 5xx error responses from HAProxy Prom Metrics."""
    try:
        # A real implementation would parse the prom metrics or HAProxy stats CSV
        # for 'hrsp_5xx' fields over total requests.
        resp = requests.get(HAPROXY_METRICS)
        # Mock logic to pull 5xx error rate from prometheus formatting
        return 0.0 # Returning 0.0 to reflect CPU delay failure signature
    except:
        return 0.0

def drain_server(backend, server):
    cmd = f'echo "set server {backend}/{server} state drain" | socat stdio {SOCKET}'
    subprocess.run(cmd, shell=True)
    print(f"[{time.strftime('%X')}] 🚥 SM-STYLE DRAIN TRIGGERED!")

def main():
    print("Starting SM-Style Error Rate Detector...")
    consecutive_highs = 0
    drained = False
    
    while True:
        if drained:
            time.sleep(10)
            continue
            
        rate = get_haproxy_errors()
        print(f"[{time.strftime('%X')}] Gateway 5xx Error Rate: {rate*100}%")
        
        if rate > ERROR_RATE_THRESHOLD:
            consecutive_highs += 1
        else:
            consecutive_highs = 0
            
        if consecutive_highs > CONSECUTIVE_LIMIT:
            drain_server("triton_backend", "gpu1")
            drained = True
            
        time.sleep(1)

if __name__ == "__main__":
    main()
