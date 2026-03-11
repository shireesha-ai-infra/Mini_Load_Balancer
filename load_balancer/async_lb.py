import asyncio
import aiohttp
from aiohttp import web
import time
import json
from collections import defaultdict

# ---------------- METRICS ---------------- #

requests_total = 0
requests_failed = 0

server_requests = {}

request_latency_total = 0

# ---------------- RATE LIMITING ---------------- #

RATE_LIMIT = 10  # max requests per second per client
client_requests = defaultdict(list)

# ---------------- RETRY CONFIG ---------------- #

MAX_RETRIES = 2

# ---------------- BACKEND INFO ---------------- #

BACKEND_SERVERS = []

healthy_servers = []
current_server = 0

# ---------------- LOAD REGISTRY ---------------- #

def load_registry():
    try:
        with open("registry.json") as f:
            data = json.load(f)
        
        servers = []
        for server in data["servers"]:
            url = f"http://localhost:{server['port']}"
            servers.append(url)

        return servers
    except Exception as e:
        print("Registry Load Error : ", e)
        return []
    
# ---------------- REGISTRY MONITOR TASK ---------------- #

async def registry_watcher():
    global BACKEND_SERVERS

    while True:
        servers = load_registry()

        if servers != BACKEND_SERVERS:
            print("Registry updated:", servers)
            BACKEND_SERVERS[:] = servers

        for server in servers:
            if server not in server_requests:
                server_requests[server] = 0

        await asyncio.sleep(5)


# ---------------- HEALTH CHECK ---------------- #

async def health_check():
    global healthy_servers
    while True:
        new_healthy = []
        async with aiohttp.ClientSession() as session:
            for server in BACKEND_SERVERS:
                try:
                    async with session.get(server + "/health", timeout=1) as resp:
                        if resp.status == 200:
                            new_healthy.append(server)
                except:
                    pass

        healthy_servers[:] = new_healthy
        print("Healthy servers:", healthy_servers)
        await asyncio.sleep(5)

# ---------------- METRICS ENDPOINT ---------------- #

def rate_limited(client_ip):
    now = time.time()
    timestamps = client_requests[client_ip]

    # keeping only last 1 second
    client_requests[client_ip] = [t for t in timestamps if now - t < 1]

    if len(client_requests[client_ip]) >= RATE_LIMIT:
        return True
    
    client_requests[client_ip].append(now)
    return False


# ---------------- METRICS ENDPOINT ---------------- #

async def metrics_handler(request):
    avg_latency = 0

    if requests_total > 0:
        avg_latency = request_latency_total / requests_total

    metrics = []

    metrics.append(f"requests_total {requests_total}")
    metrics.append(f"requests failed {requests_failed}")
    metrics.append(f"request_latency_avg {avg_latency}")

    for server, count in server_requests.items():
        metrics.append(f'server_requests{{server = "{server}"}} {count}')

    return web.Response(
        text="\n".join(metrics),
        content_type="text/plain"
    )


# ---------------- REQUEST HANDLER ---------------- #

async def handle_request(request):
    global current_server
    global requests_total
    global requests_failed
    global request_latency_total

    requests_total += 1

    if request.path == "/favicon.ico":
        return web.Response(status=204)
    
    client_ip = request.remote

    # rate limiting
    if rate_limited(client_ip):
        return web.Response(status=429, text="Too Many Requests")

    if not healthy_servers:
        return web.Response(status=503, text="No healthy servers")
    
    start_time = time.time()
    async with aiohttp.ClientSession() as session:
        for attempt in range(MAX_RETRIES + 1):
            backend = healthy_servers[current_server % len(healthy_servers)]
            current_server += 1

            backend_url = backend + request.path
            print(f"Attempt {attempt + 1}: forwarding to {backend}")
            
            try:
                async with session.get(backend_url) as resp:
                    body = await resp.read()

                    latency = time.time() - start_time
                    request_latency_total += latency

                    return web.Response(
                        status=resp.status,
                        body=body,
                        headers=resp.headers
                    )
            except Exception as e:
                print(f"Retry {attempt+1} failed on {backend}: {e}")
                continue
    requests_failed += 1
    return web.Response(
        status=502, 
        text="Backend error"
    )

# ---------------- BACKGROUND TASKS ---------------- #

async def start_background_tasks(app):
    BACKEND_SERVERS[:] = load_registry()
    app['health_task'] = asyncio.create_task(health_check())
    app['registry_task'] = asyncio.create_task(registry_watcher())


async def cleanup_background_tasks(app):
    app['health_task'].cancel()
    app['registry_task'].cancel()

    await app['health_task']
    await app['registry_task']

# ---------------- APPLICATION SETUP ---------------- #

def create_app():
    app = web.Application()
    app.router.add_get("/metrics", metrics_handler)
    app.router.add_get('/{tail:.*}', handle_request)
    app.on_startup.append(start_background_tasks)
    app.on_cleanup.append(cleanup_background_tasks)
    return app


if __name__ == "__main__":
    app = create_app()
    web.run_app(app, port=9000)