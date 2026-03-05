import requests
from http.server import BaseHTTPRequestHandler, HTTPServer

BACKEND_SERVERS = [
    "http://localhost:8001",
    "http://localhost:8002",
    "http://localhost:8003"
]

current_server = 0

class LoadBalancerHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        if self.path == "/favicon.ico":
            self.send_response(204)
            self.end_headers()
            return
        
        global current_server
        backend = BACKEND_SERVERS[current_server]

        print("Forwarding request to:", backend)

        # Round Robin logic
        current_server = (current_server+1)%len(BACKEND_SERVERS)

        backend_url = backend + self.path
        response = requests.get(backend_url)

        self.send_response(response.status_code)

        for key, value in response.headers.items():
            self.send_header(key, value)

        self.end_headers()

        self.wfile.write(response.content)

def run(port):
    server = HTTPServer(("localhost",port), LoadBalancerHandler)
    print(f"Load Balancer running on port {port}")
    server.serve_forever()

if __name__ == "__main__":
    run(9000)