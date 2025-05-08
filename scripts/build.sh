#!/bin/bash
set -x
CWD=`pwd`

# Use first command-line argument as docker_type, default to "python"
docker_type=${1:-python}

BASE_DIR=${HOME}/code/research/private-RAG/wiki-rag/
DOCKERFILE=${BASE_DIR}dockerfiles/Dockerfile.${docker_type}

echo "Working directory: $CWD"
echo "Base directory: $BASE_DIR"
echo "Using Dockerfile: $DOCKERFILE"

docker build -f "$DOCKERFILE" -t wiki-rag-tiny "$BASE_DIR"