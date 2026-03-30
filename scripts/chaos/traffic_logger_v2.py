import urllib.request
import urllib.error
import json
import time
import csv
import concurrent.futures
from datetime import datetime, timezone
import queue
import threading

ENDPOINT = "http://localhost:80/v2/models/resnet50/infer"
dummy_data = [0.0] * (3 * 224 * 224)
PAYLOAD = json.dumps({
    "inputs": [{
        "name": "data",
        "shape": [1, 3, 224, 224],
        "datatype": "FP32",
        "data": dummy_data
    }]
}).encode('utf-8')

HEADERS = {'Content-Type': 'application/json'}

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

def send_request(q):
    start_dt = datetime.now(timezone.utc)
    req_start = time.time()
    try:
        req = urllib.request.Request(ENDPOINT, data=PAYLOAD, headers=HEADERS, method='POST')
        with urllib.request.urlopen(req, timeout=5.0) as response:
            status = response.getcode()
            response.read()
    except urllib.error.HTTPError as e:
        status = e.code
    except urllib.error.URLError as e:
        status = "Timeout/URLError"
    except Exception as e:
        status = "Error"
        
    req_end = time.time()
    latency_ms = (req_end - req_start) * 1000
    
    # ISO 8601 with milliseconds
    iso_time = start_dt.isoformat(timespec='milliseconds')
    q.put([iso_time, f"{latency_ms:.2f}", status])

def worker(q, start_time, duration):
    while time.time() - start_time < duration:
        send_request(q)
        time.sleep(0.01)

def main():
    import sys
    if len(sys.argv) < 3:
        print("Usage: python traffic_logger_v2.py [duration_seconds] [output_file.csv]")
        sys.exit(1)
        
    duration = int(sys.argv[1])
    output_file = sys.argv[2]
    concurrency = 8
    
    q = queue.Queue()
    t = threading.Thread(target=writer_thread, args=(q, output_file))
    t.start()
    
    start_time = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [executor.submit(worker, q, start_time, duration) for _ in range(concurrency)]
        concurrent.futures.wait(futures)
        
    q.put(None)
    t.join()

if __name__ == "__main__":
    main()
