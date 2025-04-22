# Stage 1: Build layer
FROM python:3.10-slim as builder

WORKDIR /app

# Avoid Python buffering logs
ENV PYTHONUNBUFFERED=1

# Install only what's needed for pip
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy code and install dependencies into a temp folder
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: Final runtime image
FROM python:3.10-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1

# Copy only installed dependencies and minimal source
COPY --from=builder /install /usr/local
COPY README.md wiki_rag .

# Copy FAISS data (note: this might be big—consider generating at runtime if possible)
COPY data /home/ec2-user/data

ENV FAISS_PATH=/home/ec2-user/data

EXPOSE 8000

# Define entrypoint or CMD here if needed, e.g.
# CMD ["python", "wiki_rag/server.py"]
CMD ["uvicorn", "wiki_rag.rag_server:app", "--host", "0.0.0.0", "--port", "8000"]


