import socket

ENCLAVE_CID = 16   # default CID for enclave
VSOCK_PORT = 5000

def send_message_to_enclave(message: str):
    sock = socket.socket(socket.AF_VSOCK, socket.SOCK_STREAM)
    sock.connect((ENCLAVE_CID, VSOCK_PORT))
    sock.sendall(message.encode())
    response = sock.recv(1024)
    print(f"[Parent] Received from enclave: {response.decode()}")
    sock.close()

if __name__ == "__main__":
    send_message_to_enclave("Hello enclave!")

