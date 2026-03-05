import requests
import time

BACKEND_SERVERS = [
    "http://localhost:8001",
    "http://localhost:8002",
    "http://localhost:8003"
]

healthy_servers = []

def check_servers():
    global healthy_servers

    new_healthy = []

    for server in BACKEND_SERVERS:
        try:
            r = requests.get(server + "/health", timeout=1)
            if r.status_code == 200:
                new_healthy.append(server)

        except:
            pass

    healthy_servers = new_healthy
    print("Healthy Servers: ", healthy_servers)

while True:
    check_servers()
    time.sleep(5)
