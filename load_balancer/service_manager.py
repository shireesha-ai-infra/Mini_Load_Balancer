import json
import subprocess
import time

REGISTRY_FILE = "registry.json"

processes = {}

def load_registry():
    with open(REGISTRY_FILE) as f:
        data = json.load(f)

    servers = {}

    for server in data["servers"]:
        server_id = server["id"]
        port = server["port"]
        servers[server_id] = port

    return servers

def reconcile_servers():
    global processes

    desired = load_registry()

    # Starting new servers
    for server_id, port in desired.items():
        if server_id not in processes:
            print(f"Starting {server_id} on port {port}")

            p = subprocess.Popen(
                ["python", "server.py", server_id, str(port)]
            )
            processes[server_id] = p

    # Stop removed servers
    for server_id in list(processes.keys()):
        if server_id not in desired:
            print(f"Stopping {server_id}")
            processes[server_id].terminate()
            del processes[server_id]


if __name__ == "__main__":
    print("Server Manager Started")

    while True:
        reconcile_servers()
        time.sleep(3)