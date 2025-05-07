FROM amazonlinux:2

# Install essential build dependencies
RUN yum update -y && \
    yum install -y gcc openssl-devel bzip2-devel libffi-devel zlib-devel wget make tar gzip && \
    yum clean all

# Download and build Python 3.9
WORKDIR /usr/src
RUN wget https://www.python.org/ftp/python/3.9.19/Python-3.9.19.tgz && \
    tar xzf Python-3.9.19.tgz

WORKDIR /usr/src/Python-3.9.19
RUN ./configure --enable-optimizations && \
    make altinstall

# Set Python path
ENV PATH="/usr/local/bin:${PATH}"



# Install Python dependencies
COPY pyproject.toml README.md ./
COPY wiki_rag ./wiki_rag

