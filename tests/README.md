# Wiki-RAG Tests

This directory contains the test suite for the Wiki-RAG project.

## Test Structure

- `test_wikipedia.py`: Unit tests for Wikipedia data processing functions
- `test_encryption.py`: Unit tests for encryption/decryption functionality
- `test_rag.py`: Unit tests for core RAG functionality (embeddings, FAISS operations)
- `test_rag_server_api.py`: Unit tests for the FastAPI server endpoints
- `test_integration.py`: Integration tests for end-to-end workflows
- `conftest.py`: Shared pytest fixtures

## Running Tests

Install test dependencies:
```bash
pip install -e ".[dev]"
```

Run all tests:
```bash
pytest
```

Run with coverage:
```bash
pytest --cov=wiki_rag --cov-report=html
```

Run only unit tests:
```bash
pytest -m "not integration"
```

Run only integration tests:
```bash
pytest -m integration
```

Run tests in verbose mode:
```bash
pytest -v
```

## Test Categories

### Unit Tests
- Test individual functions and classes in isolation
- Use mocks to avoid external dependencies
- Fast execution

### Integration Tests
- Test interaction between multiple components
- May use temporary files and directories
- Test realistic workflows

## Writing New Tests

1. Place unit tests in files named `test_<module>.py`
2. Use the `@pytest.mark.integration` decorator for integration tests
3. Use fixtures from `conftest.py` for common test data
4. Mock external dependencies (models, APIs) in unit tests
5. Follow the existing test patterns for consistency