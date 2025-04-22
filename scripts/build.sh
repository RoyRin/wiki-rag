#!/bin/bash
set -x
CWD=`pwd`

BASE_DIR=${HOME}/code/research/private-RAG/wiki-rag/

echo $CWD

echo $BASE_DIR

docker build -t wiki-rag-tiny $BASE_DIR
