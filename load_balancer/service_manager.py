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

def start_server(server_id, port):
    print(f"Starting {server_id} on {port}")

    p = subprocess.Popen(
        ["python", "server.py", server_id, str(port)]
    )

    processes[server_id] = {
        "process":p,
        "port": port
    }

def stop_server(server_id):
    print(f"Stopping {server_id}")

    processes[server_id]["process"].terminate()
    del processes[server_id]


def reconcile():
    desired_servers = load_registry()

    running_servers = list(processes.keys())

    # Start missing servers
    for server_id, port in desired_servers.items():
        if server_id not in processes:
            start_server(server_id, port)

    # Stop removed servers
    for server_id in running_servers:
        if server_id not in desired_servers:
            stop_server(server_id)


if __name__ == "__main__":
    print("Server Manager Started")

    while True:
        try:
            reconcile()
        except Exception as e:
            print("Manager Error: ",e)
            
        time.sleep(3)