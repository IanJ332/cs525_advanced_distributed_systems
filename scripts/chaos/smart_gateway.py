import asyncio
import time
import math
import random
import argparse
from aiohttp import web, ClientSession, ClientTimeout

class Backend:
    def __init__(self, url):
        self.url = url
        # === Circuit Breaker (Tri-CB) State ===
        self.is_open = False
        self.consecutive_failures = 0
        self.eject_until = 0.0
        
        # === P2C-PEWMA State ===
        self.pending_requests = 0
        self.rtt_ewma = 0.0
        self.last_update_time = time.time()

class Router:
    def __init__(self, backends):
        self.backends = backends

    def select_backend(self) -> Backend:
        raise NotImplementedError

    def on_request_start(self, backend: Backend):
        backend.pending_requests += 1

    def on_success(self, backend: Backend, rtt: float):
        backend.pending_requests = max(0, backend.pending_requests - 1)
        backend.consecutive_failures = 0
        if backend.is_open:
            backend.is_open = False

    def on_failure(self, backend: Backend):
        backend.pending_requests = max(0, backend.pending_requests - 1)
        backend.consecutive_failures += 1

class RoundRobinRouter(Router):
    def __init__(self, backends):
        super().__init__(backends)
        self.idx = 0

    def select_backend(self) -> Backend:
        b = self.backends[self.idx % len(self.backends)]
        self.idx += 1
        return b

class TriCBRouter(Router):
    def __init__(self, backends, max_failures=3, eject_duration=5.0):
        super().__init__(backends)
        self.idx = 0
        self.max_failures = max_failures
        self.eject_duration = eject_duration

    def select_backend(self) -> Backend:
        now = time.time()
        # Recover OPEN backends if Timeout (T_eject) expired
        for b in self.backends:
            if b.is_open and now >= b.eject_until:
                b.is_open = False
                b.consecutive_failures = 0

        # Attempt to find a strictly CLOSED backend
        for _ in range(len(self.backends)):
            b = self.backends[self.idx % len(self.backends)]
            self.idx += 1
            if not b.is_open:
                return b
        
        # If all circuits are completely broken, uniformly distribute to fail gracefully
        return random.choice(self.backends)

    def on_failure(self, backend: Backend):
        super().on_failure(backend)
        if backend.consecutive_failures >= self.max_failures:
            backend.is_open = True
            backend.eject_until = time.time() + self.eject_duration

class P2CPEWMARouter(Router):
    def __init__(self, backends, tau=2.0):
        super().__init__(backends)
        self.tau = tau  # Half-life strictly governing decay speed

    def select_backend(self) -> Backend:
        if len(self.backends) == 1:
            return self.backends[0]
            
        # P2C Phase: Pick 2 uniform random backends
        b1, b2 = random.sample(self.backends, 2)
        
        # Scoring Phase: PEWMA RTT weighted by active Inflights
        score1 = b1.rtt_ewma * (b1.pending_requests + 1)
        score2 = b2.rtt_ewma * (b2.pending_requests + 1)
        
        return b1 if score1 <= score2 else b2

    def on_success(self, backend: Backend, rtt: float):
        super().on_success(backend, rtt)
        now = time.time()
        dt = now - backend.last_update_time
        decay = math.exp(-dt / self.tau)
        
        # Peak EWMA Implementation: Sharp rise on RTT degradation, exponential decay on recovery
        backend.rtt_ewma = max(rtt, backend.rtt_ewma * decay)
        backend.last_update_time = now

class SmartGateway:
    def __init__(self, policy, backend_urls):
        self.backends = [Backend(url) for url in backend_urls]
        if policy == "round_robin":
            self.router = RoundRobinRouter(self.backends)
            self.timeout = ClientTimeout(total=10.0) 
        elif policy == "tri_cb":
            self.router = TriCBRouter(self.backends, max_failures=2, eject_duration=10.0)
            self.timeout = ClientTimeout(total=0.5)  # 500ms Aggressive L7 SLA Timeout
        elif policy == "p2c_pewma":
            self.router = P2CPEWMARouter(self.backends, tau=1.0)
            self.timeout = ClientTimeout(total=5.0)
        else:
            raise ValueError(f"Unknown policy: {policy}")

        self.policy = policy
        self.session = None

        # Tri-CB Thread-safe Concurrency Semaphore (Retry Budget)
        self.active_retries = 0
        self.max_retries = 1
        self.lock = asyncio.Lock()

    async def start(self):
        self.session = ClientSession(timeout=self.timeout)

    async def stop(self):
        if self.session:
            await self.session.close()

    async def handle_request(self, request: web.Request):
        body = await request.read()
        target_path = request.path_qs
        
        headers = dict(request.headers)
        headers.pop("Host", None) # Remove host mismatch
        
        max_attempts = 2 if self.policy == "tri_cb" else 1
        
        for attempt in range(max_attempts):
            backend = self.router.select_backend()
            target_url = backend.url + target_path
            
            self.router.on_request_start(backend)
            start_time = time.time()
            
            try:
                # HTTP Payload Forwarding
                async with self.session.post(target_url, data=body, headers=headers) as resp:
                    resp_body = await resp.read()
                    rtt = time.time() - start_time
                    self.router.on_success(backend, rtt)
                    return web.Response(body=resp_body, status=resp.status, headers=list(resp.headers.items()))
                    
            except (asyncio.TimeoutError, Exception) as e:
                self.router.on_failure(backend)
                # TRi-CB Aggressive Failover Logic
                if self.policy == "tri_cb" and attempt < max_attempts - 1:
                    async with self.lock:
                        if self.active_retries < self.max_retries:
                            self.active_retries += 1
                            can_retry = True
                        else:
                            can_retry = False
                            
                    if can_retry:
                        try:
                            continue # Jump to fast failover on alternative replica
                        finally:
                            async with self.lock:
                                self.active_retries -= 1
                    else:
                        break # Short-circuit: Retry Budget Exhausted (Prevent Retry Storm)
                else:
                    break
                    
        return web.Response(status=503, text="SmartGateway 503: Backend Exhaustion or Circuit Breaker Triggered.")

def main():
    parser = argparse.ArgumentParser(description="Smart Gateway with App-level L7 Routing")
    parser.add_argument("--policy", choices=["round_robin", "tri_cb", "p2c_pewma"], default="round_robin")
    parser.add_argument("--port", type=int, default=80)
    parser.add_argument("--backends", nargs="+", default=["http://sp26-cs525-0605.cs.illinois.edu:8000", "http://sp26-cs525-0606.cs.illinois.edu:8000"])
    args = parser.parse_args()

    gateway = SmartGateway(args.policy, args.backends)
    
    app = web.Application()
    app.router.add_route('*', '/{path:.*}', gateway.handle_request)
    
    async def on_startup(app):
        await gateway.start()
        print(f"🚀 [INIT] Smart Gateway L7 Engine started on PORT {args.port}")
        print(f"🧠 [POLICY] Mode Set To: {args.policy.upper()}")
        print(f"🔗 [TARGETS] Cluster Endpoints: {args.backends}")
        
    async def on_cleanup(app):
        await gateway.stop()
        
    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)
    
    web.run_app(app, port=args.port)

if __name__ == "__main__":
    main()
