import aiohttp
import asyncio
import time
import json
import numpy as np

# Targeting VM 01 (Gateway)
TARGET_URL = "http://sp26-cs525-0601.cs.illinois.edu:8080/v2/models/resnet50/infer"

# Load a sample payload (Simulate 1MB data if none)
def get_payload():
    return {"inputs": [{"name": "input0", "shape": [1, 3, 224, 224], "datatype": "FP32", "data": [0.1]*150528}]}

async def fire_request(session, payload):
    start = time.perf_counter()
    try:
        async with session.post(TARGET_URL, json=payload) as resp:
            # We must consume the response to ensure the full exchange occurs
            await resp.read()
            end = time.perf_counter()
            return (end - start) * 1000 # ms
    except Exception:
        return None

async def benchmark(concurrency=10, duration=60):
    payload = get_payload()
    latencies = []
    start_time = time.time()
    
    print(f"Bombardment ongoing: Concurrency={concurrency}, Duration={duration}s")
    
    async with aiohttp.ClientSession() as session:
        while time.time() - start_time < duration:
            # Run a batch of concurrent requests
            tasks = [fire_request(session, payload) for _ in range(concurrency)]
            results = await asyncio.gather(*tasks)
            latencies.extend([r for r in results if r is not None])
            
    # Calculate stats
    if not latencies:
        return "ERROR: No successful requests"
        
    p99 = np.percentile(latencies, 99)
    avg = np.mean(latencies)
    throughput = len(latencies) / duration
    
    return {
        "p99_ms": p99,
        "avg_ms": avg,
        "rps": throughput,
        "total_requests": len(latencies)
    }

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--concurrency", type=int, default=10)
    args = parser.parse_args()
    
    res = asyncio.run(benchmark(concurrency=args.concurrency))
    print(json.dumps(res, indent=4))
