import urllib.request
import urllib.error
import json
import time
import csv
import concurrent.futures

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

def send_request(start_time):
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
    timestamp = req_start - start_time
    return [f"{timestamp:.3f}", f"{latency_ms:.2f}", status]

def worker(writer, start_time, duration):
    while time.time() - start_time < duration:
        result = send_request(start_time)
        writer.writerow(result)
        time.sleep(0.01)

def main():
    start_time = time.time()
    duration = 60 # 60 seconds
    concurrency = 8
    
    with open('latency_results.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Timestamp_s', 'Latency_ms', 'Status'])
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
            futures = [executor.submit(worker, writer, start_time, duration) for _ in range(concurrency)]
            concurrent.futures.wait(futures)

if __name__ == "__main__":
    main()
