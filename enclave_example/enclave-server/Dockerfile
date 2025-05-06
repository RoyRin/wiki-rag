FROM python:3.10  
# Note: NOT slim

WORKDIR /app
COPY server.py .

RUN python --version && which python
RUN pip install --no-cache-dir --upgrade pip

ENTRYPOINT ["python", "server.py"]

