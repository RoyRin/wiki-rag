from fastapi import FastAPI, Request
from pydantic import BaseModel
from typing import Optional
import uvicorn
import base64
#import faiss
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os
from pathlib import Path 
from langchain.vectorstores import FAISS

# 🔐 Symmetric encryption key (must be securely shared after attestation)
AES_KEY = os.environ.get("RAG_AES_KEY")  # 256-bit key as base64

app = FastAPI()

# HACK: Disable encryption for now
do_encryption = False

# 🧠 Load tokenizer + model
from langchain.embeddings import HuggingFaceEmbeddings

class PromptedBGE(HuggingFaceEmbeddings):
    def embed_documents(self, texts):
        return super().embed_documents([
            f"Represent this document for retrieval: {t}" for t in texts
        ])

    def embed_query(self, text):
        return super().embed_query(f"Represent this query for retrieval: {text}")
# BAAI_embedding = HuggingFaceEmbeddings(model_name="BAAI/bge-large-en")

BAAI_embedding = PromptedBGE(model_name="BAAI/bge-base-en")  # or bge-large-en



# 📚 Load FAISS index (in-memory)
# You'd load your document embeddings here

### LOAD RAG
FAISS_PATH = None # ERROR - need to set FAISS_Path
FAISS_PATH = Path("/Users/roy/data/wikipedia/hugging_face/wiki-rag")
FAISS_PATH = FAISS_PATH/ "wiki_index__top_100000__2025-04-11"
vectorstore = FAISS.load_local(FAISS_PATH, BAAI_embedding, allow_dangerous_deserialization=True  # <-- set this only if you created the file
)


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
    if do_encryption:
        print("should not be called")
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


@app.post("/provision")
async def provision_key(payload: dict):
    raw = payload["aes_key"]
    os.environ["RAG_AES_KEY"] = raw
    AES_KEY = raw
    return {"status": "ok"}

def main():
    import uvicorn
    uvicorn.run("rag_server:app", host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()


