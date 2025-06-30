from typing import List
import numpy as np
from pathlib import Path
import json
import os
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from langchain.docstore.document import Document
from langchain.embeddings.base import Embeddings
import faiss
from langchain_community.vectorstores import FAISS

from itertools import islice
from typing import Iterator
from tqdm import tqdm
from huggingface_hub import snapshot_download


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


from wiki_rag import wikipedia as rag_wikipedia

from langchain_community.embeddings import HuggingFaceEmbeddings


class PromptedBGE(HuggingFaceEmbeddings):

    def embed_documents(self, texts):
        return super().embed_documents(
            [f"Represent this document for retrieval: {t}" for t in texts])

    def embed_query(self, text):
        return super().embed_query(
            f"Represent this query for retrieval: {text}")


# BAAI_embedding = HuggingFaceEmbeddings(model_name="BAAI/bge-large-en")


def construct_faiss(
    english_df,
    title_to_file_path,
    SAVE_PATH,
    embeddings=PromptedBGE(model_name="BAAI/bge-base-en"),
    max_articles=1_000_000,
):

    buffer = []
    batch_size = 10

    for i, row in enumerate(tqdm(english_df.itertuples(index=False))):

        #print(f"Processing article {counts}: {d['title']}")
        if i > int(max_articles):
            break

        title = row.page_title
        clean_title_ = rag_wikipedia.clean_title(title)
        data = rag_wikipedia.get_wiki_page(clean_title_, title_to_file_path)
        if data is None:
            continue

        title = data['title']
        url = data['url']
        text = data['text']
        id_ = data.get('id')

        if len(text) < 100:
            continue

        counts += 1

        if counts % 250 == 0:
            print(f"Processed {counts} articles so far...")

        text = text.strip()
        # abstract is first 3 par
        #abstract = "\n".join(text.split("\n")[:5]) # 1st paragraph only
        abstract = text

        doc = Document(page_content=abstract,
                       metadata={
                           "title": title,
                           "ind": i,
                           "url": url,
                           "id": id_
                       })

        buffer.append(doc)

        if len(buffer) >= batch_size:
            if vectorstore is None:
                print(f"len buffer - {len(buffer)}")
                with torch.no_grad():
                    vectorstore = faiss.from_documents(buffer, embeddings)
            else:
                vectorstore.add_documents(buffer)
            buffer.clear()

        if counts % 5000 == 0:
            print(f"✅ FAISS index updated with {counts} articles.")
            vectorstore.save_local(SAVE_PATH)
            print(f"✅ FAISS index saved to {SAVE_PATH}")

    # save
    print(f"Total articles processed: {counts}")
    print(f"entries in vectorstore: {vectorstore.index.ntotal}")
    # clear the buffer
    if vectorstore is None:
        print(f"len buffer - {len(buffer)}")
        with torch.no_grad():
            vectorstore = faiss.from_documents(buffer, embeddings)
    else:
        vectorstore.add_documents(buffer)
    buffer.clear()
    if vectorstore:
        vectorstore.save_local(SAVE_PATH)
        print(f"✅ FAISS index saved to {SAVE_PATH}")
    else:
        print("⚠️ No documents were indexed.")

    return vectorstore


def download_and_build_rag_from_huggingface(
        embeddings=PromptedBGE(model_name="BAAI/bge-base-en"),
        rag_name="wiki_index__top_100000__2025-04-11",
        save_dir=None,
        repo_id="royrin/wiki-rag"):

    if save_dir is None:
        save_dir = Path("wiki_rag_data")

    # make dir
    save_dir.mkdir(parents=True, exist_ok=True)

    # download the specific folder
    local_dir = snapshot_download(repo_id=repo_id,
                                  repo_type="model",
                                  allow_patterns=[f"{rag_name}/**"],
                                  local_dir=f"./{save_dir}",
                                  local_dir_use_symlinks=False)
    faiss_path = Path(local_dir) / rag_name
    vectorstore = FAISS.load_local(faiss_path,
                                   embeddings,
                                   allow_dangerous_deserialization=True)
    return vectorstore
