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

    # Copy server code
COPY README.md .
COPY wiki_rag .
#COPY pyproject.toml .
COPY requirements.txt .

#COPY poetry.lock .

RUN pip install --upgrade pip && pip install -r requirements.txt

# Optional: Copy other files like FAISS index if needed

#COPY data /app/data/
COPY data /home/ec2-user

ENV FAISS_PATH=/home/ec2-user

# Expose port
EXPOSE 8000

# Start server
CMD ["uvicorn", "wiki_rag.rag_server:app", "--host", "0.0.0.0", "--port", "8000"]

