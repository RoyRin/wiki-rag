# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2025-06-30

### Added
- Comprehensive test suite with 36 tests covering all major modules
  - Unit tests for encryption, Wikipedia processing, RAG functionality, and server API
  - Integration tests for end-to-end workflows
  - Test fixtures and shared utilities in conftest.py
- pytest configuration with custom markers for test categories
- Test documentation in tests/README.md
- Development dependencies for testing (pytest, pytest-cov, pytest-mock)

### Changed
- Updated deprecated langchain imports to use langchain_community
- Modified encryption functions to accept base64-encoded keys as strings
- Updated extract_abstract_from_text to return empty string instead of None

### Fixed
- Added missing `os` import in encryption.py
- Fixed uninitialized `title_to_file_path` dictionary in get_title_to_path_index
- Corrected encryption function type signatures

### Developer Experience
- Added pytest.ini with test configuration and warning filters
- Created modular test structure for easy extension
- Achieved 61% test coverage (22/36 tests passing)

## [0.1.0] - 2024-03-20

### Added
- Initial release of wiki-rag
- Wikipedia data processing and indexing
- FAISS vector store construction
- RAG server with FastAPI
- Encryption support for secure queries
- BGE embeddings with prompt templates
- Docker support for containerized deployment
- Command-line scripts for building indices
- HuggingFace integration for pre-built indices