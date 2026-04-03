import aiohttp
import asyncio
import time
import json
import csv
import os

TARGET_URL = "http://sp26-cs525-0601.cs.illinois.edu:8080/v2/models/resnet50/infer"

def get_payload():
    return {"inputs": [{"name": "input0", "shape": [1, 3, 224, 224], "datatype": "FP32", "data": [0.1]*150528}]}

async def fire_request(session, payload, csv_writer):
    start = time.perf_counter()
    try:
        async with session.post(TARGET_URL, json=payload, timeout=20) as resp:
            await resp.read()
            end = time.perf_counter()
            latency = (end - start) * 1000
            csv_writer.writerow([time.time(), latency, resp.status])
            return latency
    except Exception as e:
        csv_writer.writerow([time.time(), -1, 500])
        return None

async def run_sweep(concurrency, duration, filename):
    payload = get_payload()
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "latency_ms", "status"])
        
        async with aiohttp.ClientSession() as session:
            start_time = time.time()
            while time.time() - start_time < duration:
                tasks = [fire_request(session, payload, writer) for _ in range(concurrency)]
                await asyncio.gather(*tasks)
                await asyncio.sleep(0.01) # Small gap for loop breathing

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--concurrency", type=int, required=True)
    parser.add_argument("--duration", type=int, default=240)
    parser.add_argument("--output", type=str, required=True)
    args = parser.parse_args()
    
    asyncio.run(run_sweep(args.concurrency, args.duration, args.output))
