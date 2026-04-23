import aiohttp
import asyncio
import time
import json
import csv
import uuid
import argparse

TARGET_URL = "http://sp26-cs525-0601.cs.illinois.edu:8080/v2/models/resnet50/infer"

def get_payload():
    return {
        "inputs": [
            {
                "name": "data",  # 👈 已经被你证明是唯一正确的协议名！
                "shape": [1, 3, 224, 224],
                "datatype": "FP32",
                "data": [0.5] * (3 * 224 * 224) 
            }
        ]
    }

async def worker(session, payload, writer, end_time):
    while time.time() < end_time:
        req_id = str(uuid.uuid4())[:8]
        start_req = time.perf_counter()
        try:
            async with session.post(TARGET_URL, json=payload, timeout=30) as resp:
                raw_text = await resp.text()
                e2e_ms = (time.perf_counter() - start_req) * 1000
                
                backend_id = resp.headers.get('X-Backend-Id', 'unknown')
                gw_overhead = resp.headers.get('X-Gateway-Overhead-Ms', '-1')
                status = resp.status
                payload_bytes = len(json.dumps(payload))
                
                # 提取报错正文前150个字符，死也要死得明白
                error_body = raw_text[:150].replace('\n', ' ') if status != 200 else ""
                
                writer.writerow([
                    time.time(), req_id, payload_bytes, "P2C", 
                    backend_id, status, f"{e2e_ms:.2f}", gw_overhead, error_body
                ])
        except Exception as e:
            # 网络级崩溃也记录下来
            writer.writerow([time.time(), req_id, 0, "P2C", "N/A", 500, -1, -1, str(e)[:150]])

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--concurrency', type=int, required=True)
    parser.add_argument('--duration', type=int, required=True)
    parser.add_argument('--output', type=str, required=True)
    args = parser.parse_args()

    payload = get_payload()
    end_time = time.time() + args.duration

    with open(args.output, 'w', newline='') as f:
        writer = csv.writer(f)
        # 表头加入了 error_body，满足 Research Agent 的要求
        writer.writerow(["timestamp", "req_id", "payload_bytes", "policy", "backend_id", "status_code", "e2e_ms", "gateway_overhead_ms", "error_body"])
        
        async with aiohttp.ClientSession() as session:
            tasks = [worker(session, payload, writer, end_time) for _ in range(args.concurrency)]
            await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
