# Wiki-RAG

Quick start to download entire Wikipedia and load it into a RAG for you. This RAG code gives you a RAG that directly gives you the relevant wikipedia article. It's entirely offline, so saves on requests to Wikipedia. Once a title is returned by the RAG, a request can be made to an offline store of Wikipedia, or to wikipedia directly.

There are things like this, but somehow nothing quite like this. Other things require many HTTP requests to Wikipedia (like this https://llamahub.ai/l/readers/llama-index-readers-wikipedia?from=).

Date of download of Wikipedia : April 10, 2025, from `https://dumps.wikimedia.org/other/pageviews/2024/2024-12/`.

I've uploaded the wikipedia RAG to HuggingFace for public consumption, here: https://huggingface.co/royrin/wiki-rag/tree/main. 


## Notes about embedding:
The RAG is generated using embeddings on each Wikipedia page *in its entirety*; I experimented with embedding smaller parts of hte page and anecodotally found that this returns poorer results. 

## Quick Start:
To run locally, you can run `python wiki_rag/rag_server_api.py`, and then can test it out by calling `rag_server_client.py`.

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




# RAGs in TEEs (AWS nitro):
TEEs (Trusted Execution Environments) are hardware enabled execution environments for running software. AWS provides tooling to run your own TEEs through a system called **AWS Nitro**.

You can run AWS nitro from a regular EC2 instance (though not every EC2 instance), there are 5 commands:
1. `build-enclave` - converts docker-image into enclave image (`.eif`)
1. `run-enclave` - runs `.eif` file on Nitro-enabled system.
1. `descibe-enclave`
1. `console`
1. `terminate-enclave`


We include `enclave_example` as code for helping someone get spun up on running *an* image inside of a TEE.
```
.
├── enclave-server
│   ├── Dockerfile           # Defines the enclave server environment
│   ├── build_docker.sh      # Builds the Docker image
│   ├── build_eif.sh         # Converts the Docker image to a .eif file
│   ├── enclave_config.json  # Configuration file for the enclave
│   ├── run_eif.sh           # Launches the enclave using Nitro CLI
│   └── server.py            # A simple server that listens over vsock
└── parent-client
    └── client.py            # Client to query the enclave server

```
This is simple code to do:

1. Runs a Python server that listens over vsock (the communication interface within a Nitro Enclave).
2. Builds a Docker image (based on Amazon Linux 2) that contains this server.
3. Converts the Docker image into a Nitro Enclave Image File (.eif).
4. Launches the enclave image on your EC2 instance using the Nitro CLI.
5. Provides a simple client (client.py) that you can run with python client.py to send a request to the server running inside the enclave.


## Setting up a TEE for *private* RAG:
Now, AWS Nitro can be somewhat difficult to set up, so here I describe the process of setting up an AWS-Nitro backed EC2 instance. (For example, it seems crucial to build a docker image from `AmazonLinux` even though the documentation does not say this).

As a loose outline, one needs to do the following steps:
1. connect to Nitro-backed EC2 instance.
2. create docker image that will run rag_server (or pull from some container registry, like ECR).
2. Create an AWS nitro image from the docker image (it is a `.eif` file).
4. Run AWS nitro image as a server on the EC2 instance.


To start, spin up a EC2 instance; note that it must be backed by AWS Nitro firmware/hardware, so here are the EC2 instances that allow nitro: https://docs.aws.amazon.com/ec2/latest/instancetypes/ec2-nitro-instances.html . At the time of writing, here is a snippet of the AWS requirements to run an AWS Nitro Enclave. 
* Parent instance requirements:
    * Intel or AMD-based instances with at least 4 vCPUs, excluding c7i.24xlarge, c7i.48xlarge, G4ad, m7i.24xlarge, m7i.48xlarge, M7i-Flex, r7i.24xlarge, r7i.4 8xlarge, R7iz, T3, T3a, Trn1, Trn1n, U-*, VT1
    * AWS Graviton-based instances with at least 2 vCPUs, excluding A1, C7gd, C7gn, G5g, Hpc7g, Im4gn, Is4gen, M7g, M7gd, R7g, R7gd, T4g
    * Linux or Windows (2016 or later) operating system
* Enclave requirements: Linux operating system only

**Note**: when initializing the EC2 instance, make sure to "enable Nitro" (by default, I am running `m5.xlarge` with 4 vCPUs).


Once you have SSH-ed into the machine, here is the code to run on the EC2 instance ( AWS linux AMI): 

```
    # install misc packages

    sudo yum install -y aws-nitro-enclaves-cli
    sudo yum install -y aws-nitro-enclaves-cli-devel # see https://github.com/aws/aws-nitro-enclaves-cli/issues/513
    sudo yum install -y git


    # Start docker
    
    sudo systemctl start docker
    sudo usermod -aG docker ec2-user
    newgrp docker

    # set up Nitro

    sudo usermod -aG ne ec2-user
    newgrp ne
    sudo systemctl start nitro-enclaves-allocator.service
    sudo systemctl enable nitro-enclaves-allocator.service

    # Set up docker image  (locally or pulling from ECR):

    ####  local
    docker build -t wiki-rag-teeny .

    nitro-cli build-enclave \
        --docker-uri wiki-rag-teeny:latest \
        --output-file rag-enclave.eif

    #### from ECR

    ## login to AWS and to AWS ECR
    aws configure
    aws ecr get-login-password | docker login --username AWS --password-stdin <ECR-INSTANCE-ID>.dkr.ecr.us-east-1.amazonaws.com/wiki-rag
    docker pull <ECR-INSTANCE-ID>.dkr.ecr.us-east-1.amazonaws.com/wiki-rag 

    nitro-cli build-enclave \
        --docker-uri 108871799768.dkr.ecr.us-east-1.amazonaws.com/wiki-rag:latest \
        --output-file rag-enclave.eif

    # Systems-level Fixes :

    ## You may need to make the enclave memory bigger:
    sudo vim /etc/nitro_enclaves/allocator.yaml
    sudo systemctl restart nitro-enclaves-allocator.service

    
    # Run Enclave 
    nitro-cli run-enclave   --cpu-count 2   --memory 1024   --enclave-cid 16   --eif-path rag-enclave.eif
```


