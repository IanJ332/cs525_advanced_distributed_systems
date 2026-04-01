import urllib.request
import urllib.error
import json
import time
import csv
import concurrent.futures
from datetime import datetime, timezone
import queue
import threading
import sys
import gc
import os
import random

def parse_args():
    if len(sys.argv) < 5:
        print("Usage: python traffic_logger_v3.py [duration_seconds] [model_name] [payload_path] [output_file.csv]")
        print("Example: python traffic_logger_v3.py 60 resnet50 ~/data/payloads/ latency.csv")
        sys.exit(1)
    duration = int(sys.argv[1])
    model = sys.argv[2]
    payload_path = sys.argv[3]
    output_file = sys.argv[4]
    return duration, model, payload_path, output_file

def writer_thread(q, output_file):
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Timestamp_ISO', 'Latency_ms', 'Status'])
        while True:
            item = q.get()
            if item is None:
                break
            writer.writerow(item)
            q.task_done()

def worker(q, endpoint, payload_pool, start_time, duration):
    # Isolated workload engine per thread
    while time.time() - start_time < duration:
        req_start = time.time()
        
        # O(1) random access payload selection (prevent caching biases)
        payload_data = random.choice(payload_pool) 
        
        try:
            req = urllib.request.Request(endpoint, data=payload_data, headers={'Content-Type': 'application/json'}, method='POST')
            with urllib.request.urlopen(req, timeout=5.0) as response:
                status = response.getcode()
                response.read()
        except urllib.error.HTTPError as e:
            status = e.code
        except Exception as e:
            status = "Error"
            
        req_end = time.time()
        latency_ms = (req_end - req_start) * 1000
        iso_time = datetime.now(timezone.utc).isoformat(timespec='milliseconds')
        
        q.put([iso_time, f"{latency_ms:.2f}", status])
        time.sleep(0.01)

def main():
    duration, model, payload_path, output_file = parse_args()
    concurrency = 8
    
    # Architecturally critical: Force traffic exclusively through the VM01 Gateway SmartProxy 
    # to evaluate load balancing blind spots during failures.
    endpoint = f"http://sp26-cs525-0601.cs.illinois.edu:8080/v2/models/{model}/infer"
    print(f"🎯 Target Acquired (Smart Gateway L7): {endpoint}")
    
    q = queue.Queue()
    t = threading.Thread(target=writer_thread, args=(q, output_file))
    t.start()

    payload_pool = []
    files = []
    if os.path.isdir(payload_path):
        files = [os.path.join(payload_path, f) for f in sorted(os.listdir(payload_path)) if f.endswith('.json')]
    else:
        files = [payload_path]

    print(f"Loading {len(files)} chunk(s) into memory to avoid I/O bottlenecks...")
    for file in files:
        with open(file, 'r') as f:
            chunk = json.load(f)
            # Serialize individually to save critical time during actual HTTP requests
            for obj in chunk:
                payload_pool.append(json.dumps(obj).encode('utf-8'))
        
        # 🛡️ Defense Against OOM (Arch Directive)
        del chunk
        gc.collect()
        
    print(f"🚀 Successfully bridged {len(payload_pool)} serialized requests into internal memory pool.")

    start_time = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [executor.submit(worker, q, endpoint, payload_pool, start_time, duration) for _ in range(concurrency)]
        concurrent.futures.wait(futures)
        
    q.put(None)
    t.join()
    print(f"✅ Experiment log securely written to {output_file}")

if __name__ == "__main__":
    main()
