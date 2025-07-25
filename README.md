# Welcome to Byaldi
_Did you know? In the movie RAGatouille, the dish Remy makes is not actually a ratatouille, but a refined version of the dish called "Confit Byaldi"._

<p align="center"><img width=350 alt="The Byaldi logo, it's a cheerful rat using a magnifying glass to look at a complex document. It says 'byaldi' in the middle of a circle around the rat." src="byaldi.webp"/></p>

🔧 This is a fork which refines and adds new functionality to Byaldi. See [TODO.md](TODO.md) for current and planned development activities.

Byaldi is [RAGatouille](https://github.com/answerdotai/ragatouille)'s mini sister project. It is a simple wrapper around the [ColPali](https://github.com/illuin-tech/colpali) repository to make it easy to use late-interaction multi-modal models such as ColPALI with a familiar API.

## Getting started

First, a warning: This is a pre-release library, using uncompressed indexes and lacking other kinds of refinements.

Currently, we support all models supported by the underlying [colpali-engine](https://github.com/illuin-tech/colpali), including the newer, and better, ColQwen2 checkpoints, such as `vidore/colqwen2-v1.0`.  Broadly, the aim is for byaldi to support all ColVLM models.

Additional backends will be supported in future updates. As byaldi exists to facilitate the adoption of multi-modal retrievers, we intend to also add support for models such as [VisRAG](https://github.com/openbmb/visrag).

Eventually, we'll add an HNSW indexing mechanism, pooling, and, who knows, maybe 2-bit quantization?

It will get updated as the multi-modal ecosystem develops further!

For current development priorities and planned features, see [TODO.md](TODO.md).

### Development Environment Setup

For development work, it's recommended to use a virtual environment:

```bash
# Create virtual environment
python3 -m venv byaldi-env

# Activate virtual environment
source byaldi-env/bin/activate  # On Linux/Mac
# or
byaldi-env\Scripts\activate     # On Windows

# Install in development mode
pip install -e .
```

**Important**: Always activate the `byaldi-env` virtual environment before developing or testing to ensure consistent dependencies and avoid conflicts with your system Python packages.

### Pre-requisites

#### Poppler

To convert pdf to images with a friendly license, we use the `pdf2image` library. This library requires `poppler` to be installed on your system. Poppler is very easy to install by following the instructions [on their website](https://poppler.freedesktop.org/). The tl;dr is:

__MacOS with homebrew__

```bash
brew install poppler
```

__Debian/Ubuntu__

```bash
sudo apt-get install -y poppler-utils
```

#### Flash-Attention

Gemma uses a recent version of flash attention. To make things run as smoothly as possible, we'd recommend that you install it after installing the library:

```bash
pip install --upgrade byaldi
pip install flash-attn
```


#### Hardware

ColPali uses multi-billion parameter models to encode documents. We recommend using a GPU for smooth operations, though weak/older GPUs are perfectly fine! Encoding your collection would suffer from poor performance on CPU or MPS.

## Using `byaldi`

Byaldi is largely modeled after RAGatouille, meaning that everything is designed to take the fewest lines of code possible, so you can very quickly build on top of it rather than spending time figuring out how to create a retrieval pipeline.

### Loading a model

Loading a model with `byaldi` is extremely straightforward:

```python3
from byaldi import RAGMultiModalModel
# Optionally, you can specify an `index_root`, which is where it'll save the index. It defaults to ".byaldi/".
RAG = RAGMultiModalModel.from_pretrained("vidore/colqwen2-v1.0")
```

If you've already got an index, and wish to load it along with the model necessary to query it, you can do so just as easily:

```python3
from byaldi import RAGMultiModalModel
# Optionally, you can specify an `index_root`, which is where it'll look for the index. It defaults to ".byaldi/".
RAG = RAGMultiModalModel.from_index("your_index_name")
```

### Creating an index
Creating an index with `byaldi` is simple and flexible. **You can index a single PDF file, a single image file, or a directory containing multiple of those**. Here's how to create an index:

```python3
from byaldi import RAGMultiModalModel
# Optionally, you can specify an `index_root`, which is where it'll save the index. It defaults to ".byaldi/".
RAG = RAGMultiModalModel.from_pretrained("vidore/colqwen2-v1.0")
RAG.index(
    input_path="docs/", # The path to your documents
    index_name=index_name, # The name you want to give to your index. It'll be saved at `index_root/index_name/`.
    store_collection_with_index=False, # Whether the index should store the base64 encoded documents.
    doc_ids=[0, 1, 2], # Optionally, you can specify a list of document IDs. They must be integers and match the number of documents you're passing. Otherwise, doc_ids will be automatically created.
    metadata=[{"author": "John Doe", "date": "2021-01-01"}], # Optionally, you can specify a list of metadata for each document. They must be a list of dictionaries, with the same length as the number of documents you're passing.
    overwrite=True # Whether to overwrite an index if it already exists. If False, it'll return None and do nothing if `index_root/index_name` exists.
)
```

And that's it! The model will start spinning and create your index, exporting all the necessary information to disk when it's done. You can then use the `RAGMultiModalModel.from_index("your_index_name")` method presented above to load it whenever needed (you don't need to do this right after creating it -- it's already loaded in memory and ready to go!).

The main decision you'll have to make here is whether you want to set `store_collection_with_index` to True or not. If set to true, it greatly simplifies your workflow: the base64-encoded version of relevant documents will be returned as part of the query results, so you can immediately pipe it to your LLM. However, it adds considerable memory and storage requirements to your index, so you might want to set it to False (the default setting) if you're short on those resources, and create the base64 encoded versions yourself whenever needed.

#### Automatic PDF Rotation Correction

This fork includes automatic PDF rotation detection and correction functionality that is applied during document indexing. When processing PDF documents, the system can automatically detect and correct rotated pages using two strategies:

1. **PDF-level rotation detection** using PyMuPDF (fast and accurate for standard PDF rotations)
2. **Image-level rotation detection** using Tesseract OCR (handles complex rotations in scanned content)

The rotation correction is enabled by default and configured when loading the model:

```python3
# Load model with default rotation correction settings (enabled)
RAG = RAGMultiModalModel.from_pretrained("vidore/colqwen2-v1.0")
RAG.index(
    input_path="docs/",
    index_name="my_index",
    store_collection_with_index=False,
    overwrite=True
)

# Load model with rotation correction disabled
RAG = RAGMultiModalModel.from_pretrained(
    "vidore/colqwen2-v1.0",
    auto_rotate=False  # Disable automatic rotation correction
)
RAG.index(input_path="docs/", index_name="my_index", overwrite=True)

# Load model with fine-tuned rotation detection settings
RAG = RAGMultiModalModel.from_pretrained(
    "vidore/colqwen2-v1.0",
    auto_rotate=True,
    rotation_confidence_threshold=3.0,  # Higher confidence requirement for Tesseract
    use_pdf_rotation=True,              # Use PDF-level detection first
    use_tesseract_fallback=False        # Skip Tesseract fallback for faster processing
)
RAG.index(input_path="docs/", index_name="my_index", overwrite=True)
```

### Searching

Once you've created or loaded an index, you can start searching for relevant documents. Again, it's a single, very straightforward command:

```python3
results = RAG.search(query, k=3)
```

Results will be a list of `Result` objects, which you can also treat as normal dictionaries. Each result will be in this format:
```python3
[
    {
        "doc_id": 0,
        "page_num": 10,
        "score": 12.875,
        "metadata": {},
        "base64": None
    },
    ...
]
```

`page_num` are 1-indexed, while doc_ids are 0-indexed. This is to make simpler to operate with other PDF manipulation tools, where the 1st page is generally page 1. `page_num` for images and single-page PDFs will always be 1, it's only useful for longer PDFs.

If you've passed metadata or encoded with the flag to store the base64 versions, these fields will be populated. Results are sorted by score, so item 0 from the list will always be the most relevant document, etc...

### Adding documents to an existing index

Since indexes are in-memory, they're addition-friendly! If you need to ingest some new pdfs, just load your index with `from_index`, and then, call `add_to_index`, with similar parameters to the original `index()` method:

```python3
RAG.add_to_index("path_to_new_docs",
        store_collection_with_index: bool = False,
        ...
    )
```
