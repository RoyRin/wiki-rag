# server.py
import socket

VSOCK_PORT = 5000

def handle_request(data: bytes) -> bytes:
    print(f"[Enclave] Received: {data.decode()}")
    return b"Hello from the enclave!"

def enclave_server():
    sock = socket.socket(socket.AF_VSOCK, socket.SOCK_STREAM)
    sock.bind((socket.VMADDR_CID_ANY, VSOCK_PORT))
    sock.listen(1)
    print(f"[Enclave] Listening on VSOCK port {VSOCK_PORT}...")

    while True:
        conn, _ = sock.accept()
        data = conn.recv(1024)
        #data = None
        if not data:
            continue
        response = handle_request(data)
        conn.sendall(response)
        conn.close()

if __name__ == "__main__":
    enclave_server()

