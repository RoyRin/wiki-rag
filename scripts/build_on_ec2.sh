#!/bin/bash
set -x
CWD=`pwd`

BASE_DIR=${HOME}/code/wiki-rag/
#/home/ec2-user/code/wiki-rag/

echo $CWD

echo $BASE_DIR

docker build -t wiki-rag-tiny $BASE_DIR
