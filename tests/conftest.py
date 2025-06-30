import pytest
import tempfile
import shutil
from pathlib import Path


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path)


@pytest.fixture
def mock_wikipedia_data(temp_dir):
    """Create mock Wikipedia data files for testing."""
    import json
    
    # Create a sample Wikipedia JSON file
    wiki_file = temp_dir / "wikipedia_sample.jsonl"
    
    articles = [
        {
            "id": "1",
            "url": "https://en.wikipedia.org/wiki/Python_(programming_language)",
            "title": "Python (programming language)",
            "text": "Python is a high-level, interpreted programming language. It emphasizes code readability and has a simple syntax."
        },
        {
            "id": "2",
            "url": "https://en.wikipedia.org/wiki/Machine_learning",
            "title": "Machine learning",
            "text": "Machine learning is a subset of artificial intelligence that enables systems to learn from data."
        },
        {
            "id": "3",
            "url": "https://en.wikipedia.org/wiki/Natural_language_processing",
            "title": "Natural language processing",
            "text": "Natural language processing (NLP) is a subfield of linguistics and computer science concerned with computer-human language interaction."
        }
    ]
    
    with open(wiki_file, 'w') as f:
        for article in articles:
            f.write(json.dumps(article) + '\n')
    
    return wiki_file


@pytest.fixture
def mock_faiss_index(temp_dir):
    """Create a mock FAISS index directory structure."""
    index_dir = temp_dir / "faiss_index"
    index_dir.mkdir()
    
    # Create dummy files that FAISS would create
    (index_dir / "index.faiss").write_text("dummy faiss index")
    (index_dir / "index.pkl").write_text("dummy pickle data")
    
    return index_dir