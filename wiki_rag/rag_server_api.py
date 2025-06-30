from fastapi import FastAPI, Request
from pydantic import BaseModel
from typing import Optional
import uvicorn
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os
from pathlib import Path
#import faiss
import sys
import uvicorn

# 🔐 Symmetric encryption key (must be securely shared after attestation)
AES_KEY = os.environ.get("RAG_AES_KEY")  # 256-bit key as base64

app = FastAPI()

# HACK: Disable encryption for now
do_encryption = False

# 🧠 Load tokenizer + model
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings


class PromptedBGE(HuggingFaceEmbeddings):

    def embed_documents(self, texts):
        return super().embed_documents(
            [f"Represent this document for retrieval: {t}" for t in texts])

    def embed_query(self, text):
        return super().embed_query(
            f"Represent this query for retrieval: {text}")


# BAAI_embedding = HuggingFaceEmbeddings(model_name="BAAI/bge-large-en")

BAAI_embedding = PromptedBGE(model_name="BAAI/bge-base-en")  # or bge-large-en

# 📚 Load FAISS index (in-memory)
# You'd load your document embeddings here

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


# 🔒 Decrypt helper
def decrypt_message(enc_b64: str, key: bytes) -> str:
    data = base64.b64decode(enc_b64)
    nonce, ciphertext = data[:12], data[12:]
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, ciphertext, None).decode()


# 🔒 Encrypt helper
def encrypt_message(message: str, key: bytes) -> str:
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, message.encode(), None)
    return base64.b64encode(nonce + ciphertext).decode()


# 🧾 Request schema
class Query(BaseModel):
    encrypted_query: str


@app.post("/rag")
async def rag_endpoint(query: Query):
    global vectorstore
    print(f"vectorstore {vectorstore}")

    if do_encryption:
        key = base64.b64decode(AES_KEY)
        user_query = decrypt_message(query.encrypted_query, key)
    else:
        user_query = query.encrypted_query  # use plaintext

    response = vectorstore.similarity_search(user_query, k=1)[0]

    if do_encryption:
        encrypted_response = encrypt_message(response, key)
    else:
        encrypted_response = response

    return {"results": [encrypted_response]}


@app.post("/test")
async def rag_endpoint(query: Query):
    global vectorstore

    print(f"query {query}")
    return {"results": [vectorstore]}


@app.post("/provision")
async def provision_key(payload: dict):
    raw = payload["aes_key"]
    os.environ["RAG_AES_KEY"] = raw
    AES_KEY = raw
    return {"status": "ok"}


def main():
    global vectorstore
    # Optional CLI arg: FAISS path
    faiss_arg = sys.argv[1] if len(sys.argv) > 1 else None
    vectorstore = load_vectorstore(faiss_arg)
    print(f"vectorstore {vectorstore}")
    uvicorn.run("rag_server:app", host="0.0.0.0", port=8000)


if __name__ == "__main__":
    print("hello!")
    main()
