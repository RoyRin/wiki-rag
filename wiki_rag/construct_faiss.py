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
from tqdm import tqdm 

logging.set_verbosity_debug()


# My personal cache directory
cache_dir = Path('/n/netscratch/vadhan_lab/Lab/rrinberg/HF_cache')
data_cache= Path("/n/netscratch/vadhan_lab/Lab/rrinberg/wikipedia")

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
    


    import sys 
    max_articles = int(sys.argv[1]) if len(sys.argv) > 1 else 2000

    SAVE_PATH = Path(f"/n/netscratch/vadhan_lab/Lab/rrinberg/wikipedia/faiss_index__top_{max_articles}__{date_str}")
    
    embeddings = rag.ModelEmbeddings(model, tokenizer, device)
    vectorstore = None
    counts = 0

    # get the top 1M articles
    HOMEDIR = Path.home()
    BASEDIR = HOMEDIR / 'code/wiki-rag'
    asset_dir = BASEDIR / 'assets'

    json_dir = data_cache / 'json'

    output_f = asset_dir / 'english_pageviews.csv'
    stats_f = asset_dir / 'pageviews-20241201-000000'
    print(f"loading english df from {output_f}")
    english_df = wikipedia.get_sorted_english_df(output_f, stats_f) # output - where to output, stats_f base
    
    title_to_file_path_f_pkl = asset_dir / 'title_to_file_path.pkl'
    print(f"loading wiki index from {title_to_file_path_f_pkl}")

    title_to_file_path = wikipedia.get_title_to_path_index(json_dir, title_to_file_path_f_pkl)

    
    buffer = []
    batch_size = 10

    for i, row in enumerate(tqdm(english_df.itertuples(index=False))):

        #print(f"Processing article {counts}: {d['title']}")
        if i > int(max_articles):
            break

        title = row.page_title
        clean_title_ = wikipedia.clean_title(title)
        data = wikipedia.get_wiki_page(clean_title_, title_to_file_path)
        if data is None:
            continue
        
        title = data['title']
        url = data['url']
        text = data['text']
        id_ = data.get('id')
        
        if len(text) < 100:
            continue
        
        counts +=1
    
        if counts % 250 == 0:
            print(f"Processed {counts} articles so far...")
        
        text = text.strip()
        # abstract is first 3 par
        abstract = "\n".join(text.split("\n")[:5])
        
        
        doc = Document(page_content=abstract, metadata={"title": title, "ind": i, "url": url, "id": id_})
        
        buffer.append(doc)

        if len(buffer) >= batch_size:
            if vectorstore is None:
                print(f"len buffer - {len(buffer)}")
                with torch.no_grad():
                    vectorstore = FAISS.from_documents(buffer, embeddings)
            else:
                vectorstore.add_documents(buffer)
            buffer.clear()
            
        if counts % 500 == 0:
            print(f"✅ FAISS index updated with {counts} articles.")
            vectorstore.save_local(SAVE_PATH)
            print(f"✅ FAISS index saved to {SAVE_PATH}")
            
    # save 
    # print out how many
    print(f"Total articles processed: {counts}")
    print(f"entries in vectorstore: {vectorstore.index.ntotal}")
    
    if vectorstore:
        vectorstore.save_local(SAVE_PATH)
        print(f"✅ FAISS index saved to {SAVE_PATH}")
    else:
        print("⚠️ No documents were indexed.")
    
    print("hello")
    
