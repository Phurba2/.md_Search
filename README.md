# PDF Semantic Search with PostgreSQL and pgvector

A minimal local PDF semantic-search system. Place PDFs in `pdf/`, register them in PostgreSQL, extract and chunk their text, generate embeddings with `all-MiniLM-L6-v2`, and search using vector, keyword, or hybrid ranking.

## Stack

- PostgreSQL with `pgvector` and `pg_trgm`
- Python 3.12+
- PyMuPDF for PDF extraction
- `all-MiniLM-L6-v2` from Sentence Transformers
- 384-dimensional embeddings

## Setup

Enable pgvector as a PostgreSQL administrator:

```bash
sudo -u postgres psql -d pdf_vector -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

Initialize the schema from the project directory:

```bash
PGPASSWORD='your-password' psql -h localhost -U furba -d pdf_vector -f schema.sql
```

The database defaults are configured in `config/settings.py` and can be overridden with environment variables.

## Index PDFs

Place one or more PDFs in `pdf/`. From Python, run:

```python
from index import ingest_and_embed

print(ingest_and_embed())
```

This registers valid PDFs, extracts their text, creates chunks, and stores 384-dimensional embeddings in PostgreSQL.

## Search PDFs

```python
from index import search

results = search("What does the document say about avoiding financial ruin?")

for result in results:
    print(result.filename, result.score)
    for chunk in result.matched_chunks:
        print(chunk["text"])
```

Use a specific search mode when needed:

```python
from index import search
from src.search import SearchMode

vector_results = search("your question", mode=SearchMode.VECTOR)
keyword_results = search("your terms", mode=SearchMode.KEYWORD)
hybrid_results = search("your question", mode=SearchMode.HYBRID)
```

## Database tables

- `papers`: registered PDF filenames, paths, titles, and processing status
- `paper_chunks`: extracted chunks, metadata, and 384-dimensional embeddings
