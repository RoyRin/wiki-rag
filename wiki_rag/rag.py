import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from langchain.vectorstores import FAISS
from langchain.docstore.document import Document
from langchain.embeddings.base import Embeddings
from typing import List
import numpy as np
from pathlib import Path
import json
import os
from wiki_rag import wikipedia
from itertools import islice
from typing import Iterator


def load_model(cache_dir=None):
    # === You already did this ===
    model_id = 'HuggingFaceH4/zephyr-7b-beta'
    device = 'cuda:0'
    dtype = torch.float32

    model = AutoModelForCausalLM.from_pretrained(model_id,
                                                 torch_dtype=dtype,
                                                 cache_dir=cache_dir)
    model = model.to(device)
    model.eval()
    tokenizer = AutoTokenizer.from_pretrained(model_id, use_fast=False)
    return model, tokenizer, device


# === Custom LangChain Embeddings wrapper for Mistral ===
class ModelEmbeddings(Embeddings):

    def __init__(self, model, tokenizer, device='cuda:0'):
        self.model = model
        self.tokenizer = tokenizer
        self.device = device

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        inputs = self.tokenizer(texts,
                                padding=True,
                                truncation=True,
                                return_tensors='pt').to(self.device)

        with torch.no_grad():
            outputs = self.model(**inputs, output_hidden_states=True)
            # Use last hidden state (shape: [batch_size, seq_len, hidden_dim])
            hidden_states = outputs.hidden_states[-1]
            # Mean pooling across token dimension
            attention_mask = inputs['attention_mask'].unsqueeze(-1)
            masked_embeddings = hidden_states * attention_mask
            sum_embeddings = masked_embeddings.sum(dim=1)
            count_tokens = attention_mask.sum(dim=1)
            embeddings = sum_embeddings / count_tokens

        return embeddings.cpu().tolist()

    def embed_query(self, text: str) -> List[float]:
        return self.embed_documents([text])[0]


# === Helper to batch an iterator ===
def batched(iterable: Iterator, batch_size: int):
    iterator = iter(iterable)
    while batch := list(islice(iterator, batch_size)):
        yield batch


# === Create and save FAISS index in batches ===
def create_and_save_faiss_index(index_path: str, batch_size: int = 64):
    embeddings = ModelEmbeddings(model, tokenizer, device)
    vectorstore = None

    for batch in batched(get_wikipedia_articles(), batch_size):
        docs = [
            Document(page_content=abstract, metadata={"title": title})
            for title, abstract in batch
        ]

        if vectorstore is None:
            vectorstore = FAISS.from_documents(docs, embeddings)
        else:
            vectorstore.add_documents(docs)

    if vectorstore:
        vectorstore.save_local(index_path)
        print(f"✅ FAISS index saved to {index_path}")
    else:
        print("⚠️ No documents were indexed.")
