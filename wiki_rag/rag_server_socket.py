from pydantic import BaseModel
from typing import Optional

import os
from pathlib import Path
import sys
import socket
import json
from pydantic import BaseModel
from typing import Any

# 🧠 Load tokenizer + model
from langchain_community.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings

VSOCK_PORT = 5000


class PromptedBGE(HuggingFaceEmbeddings):

    def embed_documents(self, texts):
        return super().embed_documents(
            [f"Represent this document for retrieval: {t}" for t in texts])

    def embed_query(self, text):
        return super().embed_query(
            f"Represent this query for retrieval: {text}")


# BAAI_embedding = HuggingFaceEmbeddings(model_name="BAAI/bge-large-en")

BAAI_embedding = PromptedBGE(model_name="BAAI/bge-base-en")  # or bge-large-en
### LOAD RAG
FAISS_PATH = Path("/Users/roy/data/wikipedia/hugging_face/")
FAISS_PATH = FAISS_PATH / "faiss_index__top_100000__2025-04-11"
FAISS_PATH = os.environ.get("FAISS_PATH", FAISS_PATH)
print(f"FAISS_PATH {FAISS_PATH}")


# 📚 Load FAISS index (path optionally provided via CLI)
def load_vectorstore(faiss_path: Optional[str] = FAISS_PATH):
    """ adjusts global vectorstore variable """
    global vectorstore
    if faiss_path is None:
        default_FAISS_PATH = Path("/Users/roy/data/wikipedia/hugging_face")
        default_FAISS_PATH = default_FAISS_PATH / "wiki_index__top_100000__2025-04-11"
        faiss_path = default_FAISS_PATH

    else:
        faiss_path = Path(faiss_path)
    print(f"loaded vector store")
    vectorstore = FAISS.load_local(faiss_path,
                                   BAAI_embedding,
                                   allow_dangerous_deserialization=True)
    return vectorstore


# Will be set in main()
vectorstore = load_vectorstore()


# 🧾 Request schema
class Query(BaseModel):
    encrypted_query: str


# Handle incoming requests
def handle_request(data: bytes, vectorstore: Any) -> bytes:
    try:
        request_json = json.loads(data.decode())
        query = Query(**request_json)

        user_query = query.encrypted_query  # plaintext for now
        response = vectorstore.similarity_search(user_query, k=1)[0]

        response_payload = {"results": [response]}
    except Exception as e:
        response_payload = {"error": str(e)}

    return json.dumps(response_payload).encode()


# Main enclave server logic
def enclave_server(vectorstore):
    sock = socket.socket(socket.AF_VSOCK, socket.SOCK_STREAM)
    sock.bind((socket.VMADDR_CID_ANY, VSOCK_PORT))
    sock.listen(1)
    print(f"[Enclave] Listening on VSOCK port {VSOCK_PORT}...")

    while True:
        conn, _ = sock.accept()
        data = conn.recv(4096)  # Adjust buffer size if needed

        if not data:
            conn.close()
            continue

        response = handle_request(data, vectorstore)
        conn.sendall(response)
        conn.close()


if __name__ == "__main__":
    faiss_arg = sys.argv[1] if len(sys.argv) > 1 else None
    vectorstore = load_vectorstore(faiss_arg)
    print(f"vectorstore {vectorstore}")
    enclave_server(vectorstore)
