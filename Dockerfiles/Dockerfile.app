# Stage 1: Build layer
FROM python:3.10-slim as builder

WORKDIR /app/code

# Avoid Python buffering logs
ENV PYTHONUNBUFFERED=1

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml README.md ./
COPY wiki_rag ./wiki_rag

RUN pip install --upgrade pip \
    && pip install --prefix=/install .

##
# Stage 2: Final runtime image
##
FROM python:3.10-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1

# Copy dependencies and minimal installed packages from builder
COPY --from=builder /install /usr/local

# Copy essential runtime files
COPY README.md ./README.md
COPY wiki_rag ./wiki_rag

# Copy FAISS data (make sure this path exists and is correctly set up)
COPY data /app/data
ENV FAISS_PATH=/app/data

EXPOSE 8000

# Run the application
CMD ["uvicorn", "wiki_rag.rag_server:app", "--host", "0.0.0.0", "--port", "8000"]
