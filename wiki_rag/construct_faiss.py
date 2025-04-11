import wikipedia 
import transformers
from pathlib import Path 
from transformers import AutoModelForCausalLM, AutoTokenizer
transformers.utils.logging.set_verbosity(transformers.logging.CRITICAL)
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

from wiki_rag import wikipedia
from wiki_rag import rag
import os
from pathlib import Path

import torch 
from transformers.utils import logging
logging.set_verbosity_debug()


# My personal cache directory
cache_dir = Path('/n/netscratch/vadhan_lab/Lab/rrinberg/HF_cache')
data_cache= Path("/n/netscratch/vadhan_lab/Lab/rrinberg/wikipedia")
data_cache= Path("/n/netscratch/vadhan_lab/Lab/rrinberg/wikipedia/text")
if not cache_dir.exists():
    cache_dir = None 
if not data_cache.exists():
    data_cache = None 
    

os.environ["HF_HOME"] = str(cache_dir)
os.environ["TRANSFORMERS_CACHE"] = str(cache_dir)
os.environ["HF_DATASETS_CACHE"] = str(cache_dir)
os.environ["HF_HUB_CACHE"] = str(cache_dir)


# Load model
model_id = 'HuggingFaceH4/zephyr-7b-beta'
#model_id = "mistralai/Mistral-7B-Instruct-v0.3"
print(f"model_id- {model_id}")
print(f"cache_dir - {cache_dir}")   
device = 'cuda:0'
dtype= torch.float32
model = AutoModelForCausalLM.from_pretrained(model_id,
                 
                                             torch_dtype=dtype, cache_dir=cache_dir,)
model = model.to(device)
model.requires_grad_(False)
tokenizer = AutoTokenizer.from_pretrained(model_id, 
                                          use_fast=False, cache_dir=cache_dir)




# === Helper to batch an iterator ===
def batched(iterable: Iterator, batch_size: int):
    iterator = iter(iterable)
    while batch := list(islice(iterator, batch_size)):
        yield batch

import datetime

if __name__ == "__main__":
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    SAVE_PATH = Path(f"/n/netscratch/vadhan_lab/Lab/rrinberg/wikipedia/2_faiss_index__{date_str}")

    import sys 
    max_articles = int(sys.argv[1]) if len(sys.argv) > 1 else 2000
    
    
    embeddings = rag.ModelEmbeddings(model, tokenizer, device)
    vectorstore = None

    wiki_generator = wikipedia.parse_wikiextractor_output(data_cache)
    counts = 0
    batch_size = 4


    for i, d in enumerate(wiki_generator):
        #print(f"Processing article {counts}: {d['title']}")
        if i > int(max_articles):
            break

        title = d['title']
        url = d['url']
        text = d['text']
        id_ = d.get('id')
        if len(text) < 100:
            continue
        counts +=1
        
        if counts % 250 == 0:
            print(f"Processed {counts} articles so far...")
        
        text = text.strip()
        # abstract is first 3 par
        abstract = "\n".join(text.split("\n")[:5])
        doc = Document(page_content=abstract, metadata={"title": title, "ind": i, "url": url, "id": id_})
        
        if vectorstore is None:
            vectorstore = FAISS.from_documents([doc], embeddings)
        else:
            vectorstore.add_documents([doc])

        if counts % 2_500 == 0:
            print(f"✅ FAISS index updated with {counts} articles.")
            # save 
            vectorstore.save_local(SAVE_PATH)
            print(f"✅ FAISS index saved to {SAVE_PATH}")
            
    # save 
    
    if vectorstore:
        vectorstore.save_local(SAVE_PATH)
        print(f"✅ FAISS index saved to {SAVE_PATH}")
    else:
        print("⚠️ No documents were indexed.")
    
    print("hello")
    
