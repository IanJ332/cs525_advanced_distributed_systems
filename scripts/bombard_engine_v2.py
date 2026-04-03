import aiohttp
import asyncio
import time
import json
import csv
import uuid

TARGET_URL = "http://sp26-cs525-0601.cs.illinois.edu:8080/v2/models/resnet50/infer"

def get_payload():
    return {
        "inputs": [
            {
                "name": "data",
                "shape": [1, 3, 224, 224],
                "datatype": "FP32",
                "data": [0.5] * (3 * 224 * 224) 
            }
        ]
    }

async def fire_enriched_request(session, payload, writer):
    req_id = str(uuid.uuid4())[:8]
    start_time = time.perf_counter()
    
    try:
        async with session.post(TARGET_URL, json=payload, timeout=30) as resp:
            raw_text = await resp.text()
            end_time = time.perf_counter()
            
            # Extract backend ID from response headers if available (gateway should set this)
            backend_id = resp.headers.get('X-Backend-Id', 'unknown')
            status = resp.status
            e2e_ms = (end_time - start_time) * 1000
            
            # Gateway overhead estimation
            # (In reality we need the gateway to return its processing time in headers)
            gw_overhead = float(resp.headers.get('X-Gateway-Overhead-Ms', 0.0))
            
            payload_bytes = len(json.dumps(payload))
            
            writer.writerow([
                time.time(), req_id, payload_bytes, "P2C", 
                backend_id, status, f"{e2e_ms:.2f}", f"{gw_overhead:.2f}"
            ])
            
            if status != 200:
                print(f"FAILED REQ {req_id}: {status} | RAW: {raw_text[:200]}")
            return status == 200
            
    except Exception as e:
        writer.writerow([time.time(), req_id, 0, "P2C", "N/A", 0, -1, -1])
        print(f"EXCEPTION ON {req_id}: {str(e)}")
        return False

async def main():
    print("🔥 ENRICHED DRY FIRE INJECTION: SMOKE TEST (1 REQUEST)")
    payload = get_payload()
    
    with open('smoke_test_enriched.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "req_id", "payload_bytes", "policy", "backend_id", "status_code", "e2e_ms", "gateway_overhead_ms"])
        
        async with aiohttp.ClientSession() as session:
            success = await fire_enriched_request(session, payload, writer)
            if success:
                print("🟢 SMOKE TEST SUCCESSFUL: 200 OK")
            else:
                print("🔴 SMOKE TEST FAILED: CHECK LOGS ABOVE")

if __name__ == "__main__":
    asyncio.run(main())
