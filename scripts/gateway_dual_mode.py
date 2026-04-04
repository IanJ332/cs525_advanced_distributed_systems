import aiohttp
from aiohttp import web
import argparse
import random
import time

# 动态后端列表 (12 个 CPU 节点)
BACKENDS = [
    "sp26-cs525-0605.cs.illinois.edu", "sp26-cs525-0606.cs.illinois.edu",
    "sp26-cs525-0607.cs.illinois.edu", "sp26-cs525-0608.cs.illinois.edu",
    "sp26-cs525-0609.cs.illinois.edu", "sp26-cs525-0612.cs.illinois.edu",
    "sp26-cs525-0613.cs.illinois.edu", "sp26-cs525-0614.cs.illinois.edu",
    "sp26-cs525-0615.cs.illinois.edu", "sp26-cs525-0617.cs.illinois.edu",
    "sp26-cs525-0618.cs.illinois.edu", "sp26-cs525-0619.cs.illinois.edu"
]

# 真实的 P2C 状态表：记录每个后端的飞行中请求数 (In-flight requests)
pending_requests = {b: 0 for b in BACKENDS}

async def init_session(app):
    # 全局 Session 开启，彻底消除每请求建连开销
    app['session'] = aiohttp.ClientSession()

async def close_session(app):
    await app['session'].close()

def p2c_select():
    # 真正的 P2C 逻辑：随机抽两个，选负载最轻的
    c1, c2 = random.sample(BACKENDS, 2)
    return c1 if pending_requests[c1] <= pending_requests[c2] else c2

async def handle_smart(request):
    """【满血 Smart 模式】：P2C 路由 + 全流式透明转发 (零拷贝)"""
    session = request.app['session']
    backend = p2c_select()
    target_url = f"http://{backend}:8000{request.path}"
    
    # 【Bug 修复】：不能剔除 Content-Length！
    # 必须带着 Content-Length 传给 Triton，否则 aiohttp 会强制使用 chunked 编码，导致 Triton 拒载！
    clean_headers = {
        k: v for k, v in request.headers.items()
        if k.lower() not in ('host', 'transfer-encoding', 'connection')
    }
    
    pending_requests[backend] += 1
    start_time = time.perf_counter()
    try:
        # aiohttp 发现传入了流 (request.content)，同时又看到了 Content-Length，就会完美地按大小流式转发，不会 Chunked！
        async with session.post(target_url, data=request.content, headers=clean_headers) as resp:
            response = web.StreamResponse(status=resp.status)
            response.headers['X-Backend-Id'] = backend
            response.headers['X-Gateway-Overhead-Ms'] = str((time.perf_counter() - start_time) * 1000)
            await response.prepare(request)
            
            async for chunk in resp.content.iter_chunked(8192):
                await response.write(chunk)
            return response
    except Exception as e:
        # 兜底捕获：如果再有网络底层错误，直接返回 502 并在正文里写明原因！
        error_msg = f"Gateway Proxy Error: {str(e.__class__.__name__)} - {str(e)}"
        return web.Response(status=502, text=error_msg)
    finally:
        pending_requests[backend] -= 1

async def handle_strawman(request):
    """【Strawman 模式】：全量 JSON 解析 (反面教材)"""
    session = request.app['session']
    backend = BACKENDS[hash(time.time()) % len(BACKENDS)] # 随意路由
    target_url = f"http://{backend}:8000{request.path}"
    
    start_time = time.perf_counter()
    # 致命开销 1：将整个 body 读入内存并解析为 JSON
    payload = await request.json()
    
    # 致命开销 2：重新序列化发送
    async with session.post(target_url, json=payload) as resp:
        # 致命开销 3：将上游响应全部读入并解析
        resp_payload = await resp.json()
        
        headers = {
            'X-Backend-Id': backend,
            'X-Gateway-Overhead-Ms': str((time.perf_counter() - start_time) * 1000)
        }
        return web.json_response(resp_payload, status=resp.status, headers=headers)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=['smart', 'strawman'], required=True)
    parser.add_argument('--port', type=int, default=8080)
    args = parser.parse_args()

    app = web.Application()
    app.on_startup.append(init_session)
    app.on_cleanup.append(close_session)
    
    handler = handle_smart if args.mode == 'smart' else handle_strawman
    app.router.add_post('/{tail:.*}', handler)
    
    print(f"🚀 Gateway starting in {args.mode.upper()} mode on port {args.port}...")
    web.run_app(app, port=args.port)