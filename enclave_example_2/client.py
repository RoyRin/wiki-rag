# client.py
import socket

ENCLAVE_CID = 16  # Confirmed via nitro-cli describe-enclaves
PORT = 5000

sock = socket.socket(socket.AF_VSOCK, socket.SOCK_STREAM)
sock.connect((ENCLAVE_CID, PORT))
sock.sendall(b"Hello enclave!")
resp = sock.recv(1024)
print("Got:", resp.decode())
sock.close()

