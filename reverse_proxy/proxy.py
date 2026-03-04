import requests
from http.server import BaseHTTPRequestHandler, HTTPServer

BACKEND_SERVER = "http://localhost:8001"

class ReverseProxyHandler(BaseHTTPRequestHandler):

    def do_GET(self):

        backend_url = BACKEND_SERVER + self.path

        response = requests.get(backend_url)

        self.send_response(response.status_code)

        for key, value in response.headers.items():
            self.send_header(key, value)

        self.end_headers()

        self.wfile.write(response.content)


def run(port):

    server = HTTPServer(("localhost", port), ReverseProxyHandler)

    print(f"Reverse proxy running on port {port}")

    server.serve_forever()


if __name__ == "__main__":
    run(9000)