import aiohttp
import asyncio
import time
import json
import csv
import uuid
import argparse
import sys

TARGET_URL = "http://sp26-cs525-0601.cs.illinois.edu:8080/v2/models/resnet50/infer"

def get_payload_bytes():
    # 提前生成并序列化 JSON，避免打流时疯狂消耗 CPU
    payload = {
        "inputs": [{"name": "data", "shape": [1, 3, 224, 224], "datatype": "FP32", "data": [0.5] * (3 * 224 * 224)}]
    }
    return json.dumps(payload).encode('utf-8')

async def worker(session, payload_bytes, writer, end_time, is_smoke_test=False):
    while time.time() < end_time or is_smoke_test:
        req_id = str(uuid.uuid4())[:8]
        start_req = time.perf_counter()
        try:
            # 明确设置 Content-Type 为 application/json
            headers = {'Content-Type': 'application/json'}
            # 使用 data=payload_bytes 直接发送已经序列化的字节流，极致性能
            async with session.post(TARGET_URL, data=payload_bytes, headers=headers, timeout=30) as resp:
                raw_text = await resp.text()
                e2e_ms = (time.perf_counter() - start_req) * 1000
                
                backend_id = resp.headers.get('X-Backend-Id', 'unknown')
                gw_overhead = resp.headers.get('X-Gateway-Overhead-Ms', '-1')
                status = resp.status
                error_body = raw_text[:150].replace('\n', ' ') if status != 200 else ""
                
                if writer:
                    writer.writerow([time.time(), req_id, len(payload_bytes), "P2C", backend_id, status, f"{e2e_ms:.2f}", gw_overhead, error_body])
                
                if is_smoke_test:
                    if status == 200:
                        print("🟢 SMOKE TEST SUCCESSFUL: 200 OK")
                        return True
                    else:
                        print(f"🔴 SMOKE TEST FAILED: {status} | {error_body}")
                        return False
        except Exception as e:
            if writer:
                writer.writerow([time.time(), req_id, 0, "P2C", "N/A", 500, -1, -1, str(e)[:150]])
            if is_smoke_test:
                print(f"🔴 SMOKE TEST EXCEPTION: {str(e)}")
                return False
        
        if is_smoke_test:
            break

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--smoke-test', action='store_true')
    parser.add_argument('--concurrency', type=int, default=1)
    parser.add_argument('--duration', type=int, default=1)
    parser.add_argument('--output', type=str, default='smoke.csv')
    args = parser.parse_args()

    payload_bytes = get_payload_bytes()

    async with aiohttp.ClientSession() as session:
        if args.smoke_test:
            print("🔥🔥 RUNNING REMOTE SMOKE TEST (V3)...")
            success = await worker(session, payload_bytes, None, time.time()+10, is_smoke_test=True)
            sys.exit(0 if success else 1)
        else:
            end_time = time.time() + args.duration
            with open(args.output, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["timestamp", "req_id", "payload_bytes", "policy", "backend_id", "status_code", "e2e_ms", "gateway_overhead_ms", "error_body"])
                tasks = [worker(session, payload_bytes, writer, end_time) for _ in range(args.concurrency)]
                await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
