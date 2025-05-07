#!/bin/bash
set -x
CWD=`pwd`

BASE_DIR=${HOME}/code/wiki-rag/

# Use first command-line argument as docker_type, default to "python"
docker_type=${1:-python}

DOCKERFILE=${BASE_DIR}/dockerfiles/dockerfile.${docker_type}

echo "Working directory: $CWD"
echo "Base directory: $BASE_DIR"
echo "Using Dockerfile: $DOCKERFILE"

docker build -f "$DOCKERFILE" -t wiki-rag-tiny "$BASE_DIR"