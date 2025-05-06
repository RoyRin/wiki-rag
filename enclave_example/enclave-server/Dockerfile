FROM python:3.10-slim

WORKDIR /app

COPY server.py .

RUN pip install --no-cache-dir --upgrade pip

# Entry point is the enclave logic
ENTRYPOINT ["python", "server.py"]

