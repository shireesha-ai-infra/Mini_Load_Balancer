import asyncio
import aiohttp
from aiohttp import web
import time

# ---------------- METRICS ---------------- #

requests_total = 0
requests_failed = 0

server_requests = {}

request_latency_total = 0

# ---------------- BACKEND INFO ---------------- #

BACKEND_SERVERS = [
    "http://localhost:8001",
    "http://localhost:8002",
    "http://localhost:8003"
]

for server in BACKEND_SERVERS:
    server_requests[server] = 0

healthy_servers = []
current_server = 0

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

async def metrics_handler(request):
    avg_latency = 0

    if requests_total > 0:
        avg_latency = request_latency_total / requests_total

    metrics = []

    metrics.append(f"requests_total : {requests_total}")
    metrics.append(f"requests failed : {requests_failed}")
    metrics.append(f"request_latency_avg : {avg_latency}")

    for server, count in server_requests.items():
        metrics.append(f'server_requests{{server = "{server}"}} : {count}')

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

    if not healthy_servers:
        return web.Response(status=503, text="No healthy servers")

    backend = healthy_servers[current_server % len(healthy_servers)]
    current_server += 1

    backend_url = backend + request.path

    server_requests[backend] += 1

    print("Forwarding request to:", backend)

    start_time = time.time()

    async with aiohttp.ClientSession() as session:
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
        except:
            requests_failed += 1
            return web.Response(status=502, text="Backend error")

# ---------------- BACKGROUND TASKS ---------------- #

async def start_background_tasks(app):
    app['health_task'] = asyncio.create_task(health_check())


async def cleanup_background_tasks(app):
    app['health_task'].cancel()
    await app['health_task']

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