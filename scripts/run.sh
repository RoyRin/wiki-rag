#!/bin/bash
set -x
# Usage: ./run_docker.sh [host_data_path]

IMAGE_NAME="wiki-rag-tiny"

# Default mount option
if [ -n "$1" ]; then
  docker run -p 8000:8000 -v "$1":/home/ec2-user/data "$IMAGE_NAME" 
  #/bin/bash
else
  docker run  -p 8000:8000 "$IMAGE_NAME"
fi
