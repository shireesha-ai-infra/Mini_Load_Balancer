import json
import time
import requests

REGISTRY_FILE = "registry.json"

MAX_SERVERS = 6
MIN_SERVERS = 2

SCALE_UP_THRESHOLD = 30
SCALE_DOWN_THRESHOLD = 10

def read_registry():
    with open(REGISTRY_FILE) as f:
        data = json.load(f)

    return data

def write_registry(data):
    with open(REGISTRY_FILE, "w") as f:
        json.dump(data, f, indent=2)

def get_request_rate():
    try:
        r = requests.get("http://localhost:9000/metrics")
        metrics = r.text.split("\n")
        for m in metrics:
            if "requests_total" in m:
                return int(m.split()[1])
    except:
        return 0
    
def scale_up(registry):
    servers = registry["servers"]

    if len(servers) >= MAX_SERVERS:
        return registry
    
    new_id = f"server{len(servers)+1}"
    new_port = 8000 + len(servers) + 1

    print("Scaling up -> ", new_id)

    servers.append({
        "id": new_id,
        "port": new_port
    })
    return registry

def scale_down(registry):
    servers = registry["servers"]

    if len(servers) <= MIN_SERVERS:
        return registry
    
    removed = servers.pop()

    print("Scaling down -> ", removed["id"])
    return registry

if __name__ == "__main__":
    print("Autoscaler started")

    last_requests = 0

    while True:
        registry = read_registry()
        current_requests = get_request_rate()
        rate = current_requests - last_requests

        print("Request rate : ", rate)

        if rate > SCALE_UP_THRESHOLD:
            registry = scale_up(registry)
            write_registry(registry)

        elif rate < SCALE_DOWN_THRESHOLD:
            registry = scale_down(registry)
            write_registry(registry)

        last_requests = current_requests
        time.sleep(10)