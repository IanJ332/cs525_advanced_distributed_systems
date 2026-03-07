import time
import requests
import threading
import numpy as np
import concurrent.futures

HAPROXY_URL = "http://sp26-cs525-0601.cs.illinois.edu:80/v2/health/ready"

def single_request():
    start = time.time()
    try:
        requests.get(HAPROXY_URL, timeout=2)
    except:
        pass
    return time.time() - start

def hedged_request():
    start = time.time()
    # Hedging: fire two requests and take the fastest
    def fetch():
        try:
            requests.get(HAPROXY_URL, timeout=2)
            return time.time()
        except:
            return time.time() + 999
            
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        f1 = executor.submit(fetch)
        f2 = executor.submit(fetch)
        
        # We wait for the first one to complete
        done, not_done = concurrent.futures.wait(
            [f1, f2], 
            return_when=concurrent.futures.FIRST_COMPLETED
        )
        end = list(done)[0].result()
        
    return end - start

def benchmark(mode="single", duration=15, concurrency=200):
    print(f"Starting {mode} benchmark. Concurrency: {concurrency}. Duration: {duration}s")
    latencies = []
    end_time = time.time() + duration
    
    def worker():
        while time.time() < end_time:
            if mode == "hedging":
                lat = hedged_request()
            else:
                lat = single_request()
            latencies.append(lat)
            
    threads = []
    for _ in range(concurrency):
        t = threading.Thread(target=worker)
        t.start()
        threads.append(t)
        
    for t in threads:
        t.join()
        
    p99 = np.percentile(latencies, 99) * 1000
    avg = np.mean(latencies) * 1000
    total_reqs = len(latencies) * (2 if mode == "hedging" else 1)
    
    print(f"[{mode.upper()} MODE RESULTS]")
    print(f"Total Client Requests Initiated (Network Load): {total_reqs}")
    print(f"P99 Latency: {p99:.2f} ms | Avg Latency: {avg:.2f} ms")
    print("-" * 50)
    return p99, total_reqs

if __name__ == "__main__":
    # We run single mode then hedging mode
    benchmark("single", duration=10)
    benchmark("hedging", duration=10)
