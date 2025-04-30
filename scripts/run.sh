#!/bin/bash
set -x
# Usage: ./run_docker.sh [host_data_path]

IMAGE_NAME="wiki-rag-tiny"
DEFAULT_PATH="/Users/roy/data/wikipedia/hugging_face/faiss_index__top_100000__2025-04-11"

# Use $1 if provided, otherwise fallback to DEFAULT_PATH
HOST_PATH="${1:-$DEFAULT_PATH}"

docker run -p 8000:8000 -v "$HOST_PATH":/home/ec2-user/data "$IMAGE_NAME"