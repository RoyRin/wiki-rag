import json
import os
from pathlib import Path
from typing import List, Iterator
from tqdm import tqdm
from itertools import islice
import numpy as np
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from langchain.docstore.document import Document
from langchain.embeddings.base import Embeddings
import transformers
from transformers import AutoModelForCausalLM, AutoTokenizer
from transformers.utils import logging
import faiss

import datetime

import wikipedia
from wiki_rag import wikipedia as rag_wikipedia
from wiki_rag import rag

transformers.utils.logging.set_verbosity(transformers.logging.CRITICAL)
logging.set_verbosity_debug()

device = 'cuda:0'
dtype = torch.float32


# === Helper to batch an iterator ===
def batched(iterable: Iterator, batch_size: int):
    iterator = iter(iterable)
    while batch := list(islice(iterator, batch_size)):
        yield batch


HOMEDIR = Path.home()
# My personal cache directory
cache_dir = Path('/n/netscratch/vadhan_lab/Lab/rrinberg/HF_cache')
if cache_dir.exists():
    os.environ["HF_HOME"] = str(cache_dir)
    os.environ["TRANSFORMERS_CACHE"] = str(cache_dir)
    os.environ["HF_DATASETS_CACHE"] = str(cache_dir)
    os.environ["HF_HUB_CACHE"] = str(cache_dir)
    # Load model

data_cache = Path("/n/netscratch/vadhan_lab/Lab/rrinberg/wikipedia")
if not data_cache.exists():
    data_cache = HOMEDIR

if __name__ == "__main__":
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    help_information = """
    Optional Command line arguments 
        1 - max # of articles (default 2000)
        2 - overriding the location of data_cache (assumes wikipedia-json format in f'{ data_cache }' /json)"
        3 - overriding the location of view-count-directory (containing information on wikipedia-view counts)
    """
    print(help_information)
    # default location for page-view count information
    wiki_view_count_data_dir = HOMEDIR / 'code' / 'wiki-rag' / 'assets'

    import sys
    max_articles = int(sys.argv[1]) if len(sys.argv) > 1 else 2000
    data_cache = sys.argv[2] if len(sys.argv) > 2 else data_cache
    wiki_view_count_data_dir = sys.argv[3] if len(
        sys.argv) > 3 else wiki_view_count_data_dir

    data_json_dir = data_cache / 'json'

    SAVE_PATH = data_cache / f"faiss_index__top_{max_articles}__{date_str}"

    vectorstore = None
    counts = 0

    # get the top 1M articles
    output_f = wiki_view_count_data_dir / 'english_pageviews.csv'  # where to save DF of {title : page views}
    raw_stats_f = wiki_view_count_data_dir / 'pageviews-20241201-000000'

    print(f"loading english df from {output_f}")
    english_df = rag_wikipedia.get_sorted_english_df(
        output_f, raw_stats_f)  # output - where to output, stats_f base

    title_to_file_path_f_pkl = wiki_view_count_data_dir / 'title_to_file_path.pkl'
    print(f"loading wiki index from {title_to_file_path_f_pkl}")

    title_to_file_path = rag_wikipedia.get_title_to_path_index(
        data_json_dir, title_to_file_path_f_pkl)

    embeddings = rag.PromptedBGE(model_name="BAAI/bge-base-en")

    vectorstore = rag.construct_faiss(english_df,
                                      title_to_file_path,
                                      SAVE_PATH,
                                      embeddings=embeddings,
                                      max_articles=max_articles)

    print("Done building FAISS vectorstore")
