from http.server import HTTPServer, BaseHTTPRequestHandler
import sys

class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        server_id = sys.argv[1]
        message = f"Hello from server : {server_id}"
        
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()

        self.wfile.write(message.encode())


def run(port):
    server = HTTPServer(("localhost", port), SimpleHandler)
    print(f"Backend Server running on port {port}")
    server.serve_forever()

if __name__ == "__main__":

    port = int(sys.argv[2])

    run(port)