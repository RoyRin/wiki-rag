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


default_cache_dir = Path('/n/netscratch/vadhan_lab/Lab/rrinberg/HF_cache')
data_cache= Path("/n/netscratch/vadhan_lab/Lab/rrinberg/wikipedia")


def extract_abstract_from_text(text):
    
    for paragraph in text.split('\n'):
        paragraph = paragraph.strip()
        if paragraph:
            return paragraph
    return None

def read_article_from_json(full_path, offset):
    """ 
    Reads a single article from the JSON file at the given offset.
    """
    with open(full_path, 'r', encoding='utf-8') as f:
        f.seek(offset)
        line = f.readline()
        try:
            data = json.loads(line)
            title = data.get("title")
            text = data.get("text", "")
            return title, text
        except json.JSONDecodeError:
            return None, None   

def wikipedia_abstract_generator(path_to_extracted_dir):
    """
    Generator function to yield (title, abstract) tuples from extracted Wikipedia JSON files.
    """
    for dirpath, _, filenames in os.walk(path_to_extracted_dir):
        for fname in sorted(filenames):
            full_path = os.path.join(dirpath, fname)
            with open(full_path, 'r', encoding='utf-8') as f:
                while True:
                    offset = f.tell()
                    line = f.readline()
                    if not line:
                        break
                    try:
                        # Try to decode to check validity before calling read_article
                        json.loads(line)  # lightweight check
                    except json.JSONDecodeError:
                        continue

                    title, text = read_article_from_json(full_path, offset)
                    if not title or not text:
                        continue
                    abstract = extract_abstract_from_text(text)
                    if abstract:
                        yield (title.strip(), abstract)
                        

def build_title_index(path_to_extracted_dir):
    """ 
    Extracts a title index from the extracted Wikipedia JSON files. For fast look up.
    """
    index = {}
    for dirpath, _, filenames in os.walk(path_to_extracted_dir):
        for fname in sorted(filenames):
            full_path = os.path.join(dirpath, fname)
            with open(full_path, 'r', encoding='utf-8') as f:
                offset = 0
                while True:
                    line = f.readline()
                    if not line:
                        break
                    try:
                        data = json.loads(line)
                        title = data.get("title")
                        if title:
                            index[title] = (full_path, offset)
                    except json.JSONDecodeError:
                        pass
                    offset = f.tell()
    return index




def get_article_local(title, local_dir = None):
    # Call Wiki Extractor 
    if local_dir is None:
        local_dir = data_cache
    
    index = build_title_index(local_dir)
    if title not in index:
        return None
    full_path, offset = index[title]
    
    
    pass 


def get_article_remote(title, abstract_only = False ):
    import wikipedia
    # Set language (optional, default is English)
    wikipedia.set_lang("en")
    if abstract_only:
        # Get the summary (i.e., abstract / lead section)
        summary = wikipedia.summary(title)
        return summary

    # Get the full page content
    page = wikipedia.page(title)
    content = page.content
    return content