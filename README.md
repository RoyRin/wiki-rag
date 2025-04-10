# Wiki-RAG

Quick start to download entire Wikipedia and load it into a RAG for you. This RAG code gives you a RAG that directly gives you the relevant wikipedia article. It's entirely offline, so saves on requests to Wikipedia. 

There are things like this, but somehow nothing quite like this. Other things require many HTTP requests to Wikipedia (like this https://llamahub.ai/l/readers/llama-index-readers-wikipedia?from=).

Date of download of Wikipedia : April 10, 2025.



# What this repo does:

1. I downloaded Wikipedia into a cache (~22 GB, 2 hours to download). This takes time. I have done it locally, and extracted the first paragraph of each title into a new dataset, which is available here. 
2. Processes the Wikidump into a JSON (using WikiExtract)
3. Builds a RAG around the `{abstract: title}` for a specific set of model embeddings
4. Gives a simple API to extract the full wiki article (either through URL or locally) given a title,



# things that Roy needs to do:
1. download wikipedia (done)
2. load wiki through wikiextractor (doing)
2. extract {title: abstracts} from wikipedia
3. load abstracts into FAISS with title as RAG response 
4. save that 
5. write a function that you give a text, and it returns the title, and then also queries wikipedia (either locally, or through HTTPS)

# Do it for yourself, from Scratch
1. Download Wikipedia full (~22 GB, 2 hours to download over Wget, ~30 min using Aria2c)
    `aria2c -x 16 -s 16 https://dumps.wikimedia.org/enwiki/latest/enwiki-latest-pages-articles.xml.bz2`
2. Extract Wikipedia into machine-readable code:
    `python3 WikiExtractor.py ../enwiki-latest-pages-articles.xml.bz2 -o extracted --json`
2. Extract abstracts into new directory:
    ``
3. load abstracts into RAG
4. offer RAG service that queries Wikipedia through CURL (or locally), after a RAG query on the abstracts 

# Actions :
1. Download Titles:
`wget https://dumps.wikimedia.org/enwiki/latest/enwiki-latest-all-titles-in-ns0.gz`
2. Unzip titles: `gunzip enwiki-latest-all-titles-in-ns0.gz`
3. 



# Helpful Links:
1. Wikipedia downloads: `https://dumps.wikimedia.org/enwiki/latest/`
2. 