import socket

HOST = "127.0.0.1"
PORT = 8001

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server_socket.bind((HOST, PORT))

server_socket.listen(5)

while True:
    client_socket, address = server_socket.accept()

    print("Connection from : ", address)

    request = client_socket.recv(1024)

    print("Request Received:")
    print(request.decode())

    response = """HTTP/1.1 200 OK
Content-Type: text/plain

Hello from raw TCP server
"""
    client_socket.sendall(response.encode())

    client_socket.close()
