#!/bin/bash
#docker build -t enclave-server .

nitro-cli build-enclave --docker-uri enclave-server --output-file enclave-server.eif

