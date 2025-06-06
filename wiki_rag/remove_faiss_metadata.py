import pickle

print("Opening index.pkl...")
with open("index.pkl", "rb") as f:
    data = pickle.load(f)

print("Checking type of loaded object...")
print("Type:", type(data))

# If it's a tuple, inspect elements
if isinstance(data, tuple):
    print(f"Loaded tuple of length {len(data)}")
    for i, item in enumerate(data):
        print(f"Item {i}: type={type(item)}")

    # Try to find the InMemoryDocstore in the tuple
    for obj in data:
        if hasattr(obj, "_dict") or hasattr(obj, "dict"):
            docstore = obj
            break
    else:
        raise ValueError("No InMemoryDocstore found in the tuple.")

    remaining = [item for item in data if item is not docstore]
    save_as = (docstore, *remaining)  # maintain tuple structure
else:
    raise TypeError("Expected tuple from index.pkl")

print("Accessing internal document dictionary...")
doc_dict = getattr(docstore, "_dict", getattr(docstore, "dict", None))
if doc_dict is None:
    raise AttributeError("Couldn't find document dictionary in docstore")

print("Replacing metadata with just titles...")
for doc_id, doc in doc_dict.items():
    doc.metadata = {"title": doc.metadata.get("title", "Untitled")}
    doc.page_content = ""  # This is the big part

print("Saving modified docstore back to index.pkl...")
with open("index.pkl", "wb") as f:
    pickle.dump(save_as, f)

print("Done.")
