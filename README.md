# Wiki-RAG

Quick start to download entire Wikipedia and load it into a RAG for you. This RAG code gives you a RAG that directly gives you the relevant wikipedia article. It's entirely offline, so saves on requests to Wikipedia. 

Note: The RAG is generated on the first 3 paragraphs of the Wikipedia page. To then get the full page from Wikipedia, you can access a local version of Wikipedia, or make an API call for that page.

There are things like this, but somehow nothing quite like this. Other things require many HTTP requests to Wikipedia (like this https://llamahub.ai/l/readers/llama-index-readers-wikipedia?from=).

Date of download of Wikipedia : April 10, 2025, from `https://dumps.wikimedia.org/other/pageviews/2024/2024-12/`.

HuggingFace RAG here: https://huggingface.co/royrin/wiki-rag/tree/main

# What this repo does:

1. I downloaded Wikipedia into a cache (~22 GB, 2 hours to download). This takes time. I have done it locally, and extracted the first paragraph of each title into a new dataset, which is available here. 
2. Processes the Wikidump into a JSON (using WikiExtract)
3. Builds a RAG around the `{abstract: title}` for a specific set of model embeddings
4. Gives a simple API to extract the full wiki article (either through URL or locally) given a title.


# Necessary things left to do:
1. write a function that you give a text, and it returns the title, and then also queries wikipedia (either locally, or through HTTPS)
2. After RAG finishes computing, share it!
3. a bit of code clean up due to hardcoding paths

# Fun things to do
1. update RAG to only store an index into the DB, so that you can interface it with PathORAM ( and run it in TEE!)


# Do it for yourself, from Scratch
1. Download Wikipedia full (~22 GB, 2 hours to download over Wget, ~30 min using Aria2c)
    `aria2c -x 16 -s 16 https://dumps.wikimedia.org/enwiki/latest/enwiki-latest-pages-articles.xml.bz2`
2. Extract Wikipedia into machine-readable code:
    `python3 WikiExtractor.py ../enwiki-latest-pages-articles.xml.bz2 -o extracted --json`
3. Get list of top 100k or 1M articles, by page-views from
    `https://dumps.wikimedia.org/other/pageviews/2024/2024-12/`
4. load abstracts into RAG




# Helpful Links:
1. Wikipedia downloads: `https://dumps.wikimedia.org/enwiki/latest/`
2. Wikipedia page views: `https://dumps.wikimedia.org/other/pageviews/2024/2024-12/`
