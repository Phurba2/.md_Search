# PDF Semantic Search with PostgreSQL and pgvector

A local PDF semantic-search pipeline. Put PDF files in `pdf/`, register them in PostgreSQL, extract and chunk their text, generate embeddings with `all-MiniLM-L6-v2`, and search using vector, keyword, or hybrid ranking.

## Stack

- PostgreSQL with `pgvector` and `pg_trgm`
- Python 3.12+
- PyMuPDF for PDF extraction
- `all-MiniLM-L6-v2` from Sentence Transformers
- 384-dimensional embeddings

## Setup

Create the database and enable pgvector as a PostgreSQL administrator:

```bash
sudo -u postgres psql -d pdf_vector -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

Initialize the schema from the project directory:

```bash
PGPASSWORD='your-password' psql -h localhost -U furba -d pdf_vector -f schema.sql
```

The application defaults are configured in `config/settings.py` and can be overridden with environment variables.

## Index and search a PDF

Place a PDF in `pdf/`, then register it:

```bash
PGPASSWORD='your-password' ./env/bin/python scripts/cli.py ingest
```

Create chunks and embeddings:

```bash
PGPASSWORD='your-password' ./env/bin/python - <<'PY'
from src.embedding_pipeline import create_default_pipeline
print(create_default_pipeline().process_pending_papers())
PY
```

Ask a question with hybrid semantic and keyword search:

```bash
PGPASSWORD='your-password' ./env/bin/python scripts/ask_pdf.py \
  "What does the document say about avoiding financial ruin?"
```

Search modes are available through the CLI:

```bash
./env/bin/python scripts/cli.py search --query "your question" --mode vector
./env/bin/python scripts/cli.py search --query "your terms" --mode keyword
./env/bin/python scripts/cli.py search --query "your question" --mode hybrid
```

## Database tables

- `papers`: registered PDF filenames, paths, titles, and processing status
- `paper_chunks`: extracted chunks, metadata, and 384-dimensional embeddings

The project intentionally does not fetch papers from ArXiv or any other external paper repository.
