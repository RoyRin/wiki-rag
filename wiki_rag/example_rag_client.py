import requests

query = "What are the symptoms of diabetes?"

response = requests.post("http://localhost:8000/rag",
                         json={"encrypted_query": query})

print(response)
for i, result in enumerate(response.json()["results"]):
    print(f"{i+1}. {result}\n")
