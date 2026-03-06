import requests
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

BACKEND_SERVERS = [
    "http://localhost:8001",
    "http://localhost:8002",
    "http://localhost:8003"
]

healthy_servers = []
current_server = 0

lock = threading.Lock()


def health_check():
    global healthy_servers
    while True:
        new_healthy = []
        for server in BACKEND_SERVERS:
            try:
                r = requests.get(server + "/health", timeout=1)
                if r.status_code == 200:
                    new_healthy.append(server)
            except:
                pass

        with lock:
            healthy_servers = new_healthy

        print("Healthy servers:", healthy_servers)
        time.sleep(5)


class LoadBalancerHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global current_server
        if self.path == "/favicon.ico":
            self.send_response(204)
            self.end_headers()
            return

        with lock:
            if len(healthy_servers) == 0:
                self.send_response(503)
                self.end_headers()
                self.wfile.write(b"No healthy backend servers")
                return

            backend = healthy_servers[current_server % len(healthy_servers)]
            current_server += 1

        print("Forwarding request to:", backend)
        backend_url = backend + self.path
        try:
            response = requests.get(backend_url)
            self.send_response(response.status_code)
            for key, value in response.headers.items():
                self.send_header(key, value)

            self.end_headers()
            self.wfile.write(response.content)
        except:
            self.send_response(502)
            self.end_headers()
            self.wfile.write(b"Backend server error")


def run():
    health_thread = threading.Thread(target=health_check, daemon=True)
    health_thread.start()
    server = HTTPServer(("localhost", 9000), LoadBalancerHandler)
    print("Load balancer running on port 9000")
    server.serve_forever()

if __name__ == "__main__":
    run()