import asyncio
import aiohttp
import json
import time
import sys
import psutil

# Health Check Config: Backends (12 Nodes Ready)
BACKENDS = [
    "sp26-cs525-0605.cs.illinois.edu", "sp26-cs525-0606.cs.illinois.edu",
    "sp26-cs525-0607.cs.illinois.edu", "sp26-cs525-0608.cs.illinois.edu",
    "sp26-cs525-0609.cs.illinois.edu", "sp26-cs525-0612.cs.illinois.edu",
    "sp26-cs525-0613.cs.illinois.edu", "sp26-cs525-0614.cs.illinois.edu",
    "sp26-cs525-0615.cs.illinois.edu", "sp26-cs525-0617.cs.illinois.edu",
    "sp26-cs525-0618.cs.illinois.edu", "sp26-cs525-0619.cs.illinois.edu"
]

from aiohttp import web

async def strawman_handler(request):
    # CRITICAL FALLACY: Full JSON Parsing and Reserialization
    # This blocks the event loop and consumes memory for large payloads
    try:
        # 1. Block and Parse (The "Strawman" mistake)
        data = await request.json()
        
        # 2. Select backend (Simple Round Robin)
        backend = BACKENDS[hash(request.path) % len(BACKENDS)]
        url = f"http://{backend}:8000{request.path}"
        
        async with aiohttp.ClientSession() as session:
            # 3. Reserialize and Post (Double overhead)
            async with session.post(url, json=data) as resp:
                result = await resp.json()
                return web.json_response(result)
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)

async def smart_handler(request):
    start_time = time.perf_counter()
    # P2C Selection (Simplified for this version)
    backend = BACKENDS[hash(time.time()) % len(BACKENDS)]
    url = f"http://{backend}:8000{request.path}"
    
    # 1. Read binary body (Passthrough)
    body_data = await request.read()
    
    async with aiohttp.ClientSession() as session:
        # 2. Forward without JSON parsing
        try:
            async with session.post(url, data=body_data) as resp:
                body = await resp.read()
                overhead = (time.perf_counter() - start_time) * 1000
                headers = {
                    'X-Backend-Id': backend,
                    'X-Gateway-Overhead-Ms': f"{overhead:.2f}",
                    'Content-Type': 'application/json'
                }
                return web.Response(body=body, status=resp.status, headers=headers)
        except Exception as e:
            return web.Response(body=json.dumps({"gateway_error": str(e)}), status=502)

app = web.Application(client_max_size=1024**3) # 1GB Max

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["smart", "strawman"], required=True)
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()
    
    handler = smart_handler if args.mode == "smart" else strawman_handler
    app.router.add_post("/{tail:.*}", handler)
    
    print(f"Launching {args.mode.upper()} Gateway on port {args.port}...")
    web.run_app(app, port=args.port)
