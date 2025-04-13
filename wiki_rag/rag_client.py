import requests

query = "What are the symptoms of diabetes?"
response = requests.post("http://localhost:8000/query", json={"query": query, "k": 3})

for i, result in enumerate(response.json()["results"]):
    print(f"{i+1}. {result}\n")

