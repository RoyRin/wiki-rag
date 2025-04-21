# Base image with Python
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Avoid Python buffering logs
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update 


RUN    apt-get install -y --fix-missing  \
    && apt update \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
#RUN    build-essential 


# Copy requirements and install
#COPY requirements.txt .
#-r requirements.txt

# Copy server code
COPY README.md .
COPY wiki_rag .
COPY pyproject.toml .
COPY poetry.lock .


#COPY pyproject.toml .

RUN pip install --upgrade pip && pip install .


# Optional: Copy other files like FAISS index if needed

# /Users/roy/code/research/private-RAG/wiki-rag
# /Users/roy/data/wikipedia/hugging_face/wiki-rag
#COPY data/wiki_index__top_100000__2025-04-11 /app/data/
#

COPY data /app/data/

ENV FAISS_PATH=/app/data/

# Expose port
EXPOSE 8000

# Start server
CMD ["uvicorn", "wiki_rag.rag_server:app", "--host", "0.0.0.0", "--port", "8000"]

