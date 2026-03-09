import asyncio
import aiohttp
from aiohttp import web

BACKEND_SERVERS = [
    "http://localhost:8001",
    "http://localhost:8002",
    "http://localhost:8003"
]

healthy_servers = []
current_server = 0


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

async def handle_request(request):
    global current_server
    if request.path == "/favicon.ico":
        return web.Response(status=204)

    if not healthy_servers:
        return web.Response(status=503, text="No healthy servers")

    backend = healthy_servers[current_server % len(healthy_servers)]
    current_server += 1
    backend_url = backend + request.path

    print("Forwarding request to:", backend)
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(backend_url) as resp:
                body = await resp.read()
                return web.Response(
                    status=resp.status,
                    body=body,
                    headers=resp.headers
                )
        except:
            return web.Response(status=502, text="Backend error")

async def start_background_tasks(app):
    app['health_task'] = asyncio.create_task(health_check())


async def cleanup_background_tasks(app):
    app['health_task'].cancel()
    await app['health_task']


def create_app():
    app = web.Application()
    app.router.add_get('/{tail:.*}', handle_request)
    app.on_startup.append(start_background_tasks)
    app.on_cleanup.append(cleanup_background_tasks)
    return app


if __name__ == "__main__":
    app = create_app()
    web.run_app(app, port=9000)