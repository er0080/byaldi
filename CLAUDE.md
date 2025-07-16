# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Byaldi is a Python library that provides a simple wrapper around the ColPali multi-modal retrieval system. It enables late-interaction multi-modal models like ColPali and ColQwen2 to be used for document retrieval with minimal code. The library is designed to be RAGatouille's "mini sister project" with a familiar API.

## Development Commands

### Testing
```bash
# Run all tests
python tests/all.py

# Run specific test files
python -m pytest tests/test_colpali.py
python -m pytest tests/test_colqwen.py  
python -m pytest tests/test_e2e_rag.py

# Run tests with pytest (if available)
pytest tests/
```

### Code Quality
```bash
# Format and lint code
ruff format .
ruff check .

# Check specific issues
ruff check --select F401,E722,ARG,B,I .
```

### Building
```bash
# Build package
python -m build

# Install in development mode
pip install -e .

# Install with optional dependencies
pip install -e ".[dev]"
pip install -e ".[server]"
pip install -e ".[langchain]"
```

## Architecture Overview

### Core Components

1. **RAGMultiModalModel** (`byaldi/RAGModel.py`): Main user-facing class that provides high-level API for model loading, indexing, and searching.

2. **ColPaliModel** (`byaldi/colpali.py`): Lower-level implementation handling ColPali and ColQwen2 models, embedding generation, and index management.

3. **Result** (`byaldi/objects.py`): Data class representing search results with doc_id, page_num, score, metadata, and optional base64 encoded content.

4. **LangChain Integration** (`byaldi/integrations/_langchain.py`): Optional retriever interface for LangChain compatibility.

### Key Design Patterns

- **Factory Pattern**: `RAGMultiModalModel.from_pretrained()` and `from_index()` class methods for model instantiation
- **Wrapper Pattern**: `RAGMultiModalModel` wraps `ColPaliModel` to provide simplified interface
- **Builder Pattern**: Index creation with configurable options via `index()` method

### Model Support

The library currently supports:
- ColPali models (e.g., "vidore/colpali-v1.2")
- ColQwen2 models (e.g., "vidore/colqwen2-v1.0")

Model detection is done via string matching in the model name.

### Index Management

- Indexes are stored in `.byaldi/` directory by default
- Support for both in-memory and persistent storage
- Documents can be added incrementally with `add_to_index()`
- Metadata and base64 encoding are optional features

### Document Processing

- PDF files are converted to images using `pdf2image` library
- Images are processed directly
- Directory indexing processes all supported files recursively
- Page numbering is 1-indexed for user-friendliness

## Development Notes

### Dependencies

Core dependencies include:
- `colpali-engine` for the underlying ColPali implementation
- `torch` and `transformers` for model inference
- `pdf2image` for PDF processing
- `PIL` for image handling
- `srsly` for serialization

### Testing Strategy

Tests are located in `tests/` directory:
- `test_colpali.py` - Tests for ColPali model functionality
- `test_colqwen.py` - Tests for ColQwen2 model functionality  
- `test_e2e_rag.py` - End-to-end retrieval tests
- `all.py` - Comprehensive test suite

### Hardware Requirements

- GPU recommended for optimal performance
- CUDA support preferred, with fallback to MPS/CPU
- Multi-GPU support available via `n_gpu` parameter

### Common Development Patterns

When extending the library:
1. Add new model support in `ColPaliModel.__init__()`
2. Implement model-specific loading logic following existing patterns
3. Ensure backward compatibility with existing index format
4. Add comprehensive tests for new functionality
5. Update documentation and examples accordingly