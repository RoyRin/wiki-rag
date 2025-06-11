# Wiki-RAG

[![Hugging Face](https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-Dataset-yellow?style=for-the-badge)](https://huggingface.co/datasets/royrin/wiki-rag/tree/main) [![Licence](https://img.shields.io/badge/MIT_License-lightgreen?style=for-the-badge)](./LICENSE.md)

Quick start to download entire Wikipedia and load it into a RAG for you. This RAG code gives you a RAG that directly gives you the relevant wikipedia article. It's entirely offline, so saves on requests to Wikipedia. Once a title is returned by the RAG, a request can be made to an offline store of Wikipedia, or to wikipedia directly.

There are things like this, but somehow nothing quite like this. Other things require many HTTP requests to Wikipedia (like [this](https://llamahub.ai/l/readers/llama-index-readers-wikipedia?from=)).

Date of download of Wikipedia : April 10, 2025, from `https://dumps.wikimedia.org/other/pageviews/2024/2024-12/`.

I've uploaded the wikipedia RAG to HuggingFace for public consumption, [here](https://huggingface.co/royrin/wiki-rag/tree/main). 


## Notes about embedding:
The RAG is generated using embeddings on each Wikipedia page *in its entirety*; I experimented with embedding smaller parts of hte page and anecodotally found that this returns poorer results. 

## Quick Start:
To run locally, you can run `python wiki_rag/rag_server_api.py`, and then can test it out by calling `rag_server_client.py`.

You can see `notebooks/quick_start_notebook.ipynb` for a notebook version of this.

```
    from pathlib import Path
    from wiki_rag import rag

    # Get RAG from HuggingFace
    BAAI_embedding = rag.PromptedBGE(model_name="BAAI/bge-base-en") 
    faiss_name = "wiki_index__top_100000__2025-04-11"
    vectorstore = rag.download_and_build_rag_from_huggingface(
        embeddings=BAAI_embedding,
        rag_name=faiss_name,
        save_dir=Path("wiki_rag_data"))

    # Query RAG
    responses = vectorstore.similarity_search("Biochemistry", k=3)
    # Print Results
    for i, result in enumerate(responses[:10]):
        title = result.metadata["title"]
        print(f"{i+1}. Wiki Page: '{title}'\n\t{result.page_content[:50]}...\n")
```

### Docker Build + Run
Build image, for application
```
    ./scripts/build.sh python # build docker image 
    ./scripts/build.sh tee # build docker image specific for running in a TEE 
```

then to run the application
```
    ./scripts/run.sh # this just calls Docker run, with port 8000 open
```



## High-level outline of how this repo was made:

1. I downloaded Wikipedia into a cache (~22 GB, 2 hours to download). This takes time. I have done it locally, and extracted the first paragraph of each title into a new dataset, which is available here. 
2. Processes the Wikidump into a JSON (using WikiExtract)
3. Builds a RAG encoding a database of `{wiki-page: title}` for a given model embedding
4. Gives a simple API to extract the full wiki article (either through URL or locally) given a title.


## Do it for yourself, from Scratch
1. Download Wikipedia full (~22 GB, 2 hours to download over Wget, ~30 min using Aria2c)
    * `aria2c -x 16 -s 16 https://dumps.wikimedia.org/enwiki/latest/enwiki-latest-pages-articles.xml.bz2`
2. Extract Wikipedia into machine-readable code (JSON):
    * `python3 WikiExtractor.py ../enwiki-latest-pages-articles.xml.bz2 -o extracted --json`
    * `extract_wiki.slrm` does this in a slrm script (note - there are some hard-coded values)
3. Get list of top 100k or 1M articles, by page-views from
    `https://dumps.wikimedia.org/other/pageviews/2024/2024-12/`
4. load pages into RAG
    * Look to `wiki_rag/construct_faiss.py`, for assistance here (this calls `wiki_rag/wikipedia.py` and `wiki_rag/rag.py`)
    * `construct_faiss.slrm` does this in a slrm script (note - there are some hard-coded values)
5. Build a dockerfile that builds docker image with the FAISS RAG built into it, and serves a simple API.
    * Note: Dockerfile assumes that FAISS is placed in `data` dir, in the same directory, prior to building. It builds the FAISS directory into the docker image (this could instead be mounted at runtime).


## Helpful Links:
1. Wikipedia downloads: `https://dumps.wikimedia.org/enwiki/latest/`
2. Wikipedia page views: `https://dumps.wikimedia.org/other/pageviews/2024/2024-12/`
3. What is AWS Nitro, and how does it work `https://www.youtube.com/watch?v=t-XmYt2z5S8&ab_channel=AmazonWebServices`.
4. quick starting on AWS Nitro `https://docs.aws.amazon.com/enclaves/latest/user/getting-started.html`.


# File Structure:
```
wiki_rag
├── __init__.py
├── construct_faiss.py  - `Code to build FAISS from wikipedia (assumes local copy of wikipedia)`
├── rag.py - `helper code to construct FAISS code`
├── rag_server.py - `Give path to FAISS index, code to serve wikipedia entries 
├── example_rag_client.py - `simple function to poll the rag_server, given that the server is running locally in a docker-container or on your machine`
└── wikipedia.py - `helper code for interacting with a downloaded version of wikipedia`
```


# Misc:

RAG servers by default return `page.content` that can take up a lot of space. I provide `remove_faiss_metadata.py` to remove this extra content, if you just want the title of the page returned.



# Quick Download of wiki-rag RAG:
(from `https://huggingface.co/datasets/royrin/KLOM-models/tree/main`)
```
#!/bin/bash

REPO="royrin/wiki-rag"
FOLDER="faiss_index__top_100000__2025-04-11__title_only"

# Get list of all files in the repo
FILES=$(curl -s https://huggingface.co/api/models/$REPO | jq -r '.siblings[].rfilename')

# Filter files in the target folder
FILES_TO_DOWNLOAD=$(echo "$FILES" | grep "^$FOLDER/")

# Create local folder
mkdir -p $FOLDER
cd $FOLDER

# Download each file
for FILE in $FILES_TO_DOWNLOAD; do
    echo "Downloading $FILE"
    mkdir -p "$(dirname "$FILE")"
    curl -L -o "$FILE" "https://huggingface.co/$REPO/resolve/main/$FILE"
done

```

# Docker and Images
`Dockerfiles/Dockerfile.app` stores the dockerfile for the uvicorn API based RAG server


# Contextualizing Scores and numbers!

Here are what the distribution of scores can look like:
![rag_query_scores_2025-05-20_11-26-47](https://github.com/user-attachments/assets/f4cbc95c-2c14-4825-ab38-9143c3f4ef0b)

And here's an annotated version for responses associated with "Synthetic Biology"
![annontated_rag_query_scores_2025-05-20_11-26-47](https://github.com/user-attachments/assets/bdf7ba67-48ee-4a4f-af61-45e9b12fabc4)
(if you are wondering what DAVID is, it is this: https://en.wikipedia.org/wiki/DAVID; "DAVID (the database for annotation, visualization and integrated discovery) is a free online bioinformatics resource developed by the Laboratory of Human Retrovirology and Immunoinformatics")

# RAGs in TEEs (AWS nitro):
TEEs (Trusted Execution Environments) are hardware enabled execution environments for running software. AWS provides tooling to run your own TEEs through a system called **AWS Nitro**.

See branch `rr/enclave-rag` for how to set up this RAG to run within an AWS nitro instance.


# Code Notes:

Some of the code is hardcoded for my (Roy) computer or work environment, like the slurm scripts for a cluster I have access to. I include this to make it easy for people to adapt for themselves, even if it's not immediately plug-and-play (you need to update the scripts for your own server architecture and file structure).

# Contributing

To set up git hooks properly, please run
`git config core.hooksPath .githooks`
(once). This will enable hooks such as running `yapf` on all python files
