# PDF Semantic Search with PostgreSQL and pgvector

This project lets you search your own PDF files using normal questions.

You place PDFs in the `pdf/` folder. The application then:

1. Finds the PDFs.
2. Extracts their text.
3. Splits the text into smaller chunks.
4. Converts each chunk into a vector embedding.
5. Stores the chunks and embeddings in PostgreSQL.
6. Searches the stored content using vector, keyword, or hybrid search.

The project does not download papers from ArXiv or any other website.

## How it works

The embedding model is **`all-MiniLM-L6-v2`** from Sentence Transformers. It converts text into **384-number vectors**. PostgreSQL uses the `pgvector` extension to compare the question vector with the stored chunk vectors.

The search modes are:

- **Vector search**: finds text with a similar meaning.
- **Keyword search**: finds text with similar words using PostgreSQL trigram search.
- **Hybrid search**: combines both methods. This is the default and is usually the best choice.

## Requirements

Install or have these tools available:

- Python 3.12 or newer
- PostgreSQL
- PostgreSQL `pgvector` extension
- PostgreSQL `pg_trgm` extension
- Git, if cloning the project

The Python packages are listed in [`requirements.txt`](requirements.txt).

## 1. Get the project

Clone the repository and enter the project folder:

```bash
git clone https://github.com/Phurba2/Pdf_Search.git
cd Pdf_Search
```

## 2. Create and activate the Python environment

This project uses a virtual environment named `env`:

```bash
python3 -m venv env
source env/bin/activate
```

On Windows PowerShell, use:

```powershell
python -m venv env
.\env\Scripts\Activate.ps1
```

Check that the environment is active:

```bash
which python
```

On Linux or macOS, the output should end with:

```text
Pdf_Search/env/bin/python
```

## 3. Install Python packages

With the virtual environment active, run:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

The first time the embedding model is used, Sentence Transformers downloads `all-MiniLM-L6-v2`. This may take a few minutes.

## 4. Configure the database

Create a file named `.env` in the project root:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=pdf_vector
DB_USER=furba
DB_PASSWORD=furba
```

Change the values if your PostgreSQL username, password, host, or port are different.

The `.env` file is ignored by Git and should not be uploaded to GitHub.

## 5. Create the PostgreSQL database

Create the database if it does not exist:

```bash
sudo -u postgres createdb pdf_vector
```

If the database already exists, PostgreSQL may print an error. That is safe to ignore.

Give your PostgreSQL user access to the database if needed:

```bash
sudo -u postgres psql -c "ALTER DATABASE pdf_vector OWNER TO furba;"
```

## 6. Enable PostgreSQL extensions

The `vector` extension usually needs to be enabled by a PostgreSQL administrator:

```bash
sudo -u postgres psql -d pdf_vector \
  -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

The project schema enables `pg_trgm` automatically. You can also enable it manually:

```bash
sudo -u postgres psql -d pdf_vector \
  -c "CREATE EXTENSION IF NOT EXISTS pg_trgm;"
```

## 7. Create the tables

Run this command from the project root:

```bash
python setup_db.py
```

You should see:

```text
Schema initialized in database: pdf_vector
```

The schema creates two tables:

- `papers`: one row for each PDF file.
- `paper_chunks`: extracted text chunks and their embeddings.

## 8. Add your PDFs

Copy your PDF files into the `pdf/` folder:

```text
Pdf_Search/
└── pdf/
    ├── paper-one.pdf
    └── paper-two.pdf
```

PDF files are ignored by Git so that private or large documents are not uploaded to GitHub.

## 9. Register, chunk, and embed the PDFs

Run this Python command from the project root:

```bash
python - <<'PY'
from index import ingest_and_embed

result = ingest_and_embed()
print(result)
PY
```

This performs the complete indexing process:

- Registers PDFs in the `papers` table.
- Extracts text with PyMuPDF.
- Splits text into chunks.
- Generates embeddings with `all-MiniLM-L6-v2`.
- Stores chunks and embeddings in `paper_chunks`.

A successful result looks similar to:

```text
{'registration': {'found': 1, 'new': 1, 'existing': 0, 'failed': 0},
 'processing': {'requested': 100, 'found': 1, 'processed': 1, 'failed': 0}}
```

If you add another PDF later, copy it into `pdf/` and run the same command again.

## 10. Search the PDFs

Create a file named `ask.py` in the project root with this code:

```python
from index import search

question = "What does the document say about avoiding financial ruin?"
results = search(question)

for result in results:
    print(f"File: {result.filename}")
    print(f"Score: {result.score:.4f}")

    for number, chunk in enumerate(result.matched_chunks, start=1):
        print(f"\n--- Match {number} ---")
        print(chunk["text"])
```

Run it:

```bash
python ask.py
```

You can also pass a question from the command line. Replace `ask.py` with:

```python
import sys
from index import search

question = " ".join(sys.argv[1:])
if not question:
    question = "What is the main idea of the document?"

for result in search(question):
    print(f"\nFile: {result.filename}")
    print(f"Score: {result.score:.4f}")
    for chunk in result.matched_chunks:
        print(f"\n{chunk['text']}")
```

Then run:

```bash
python ask.py "What does Morgan Housel say about avoiding financial ruin?"
```

## 11. Choose a search mode

Hybrid search is the default:

```python
from index import search

results = search("your question")
```

Vector-only search:

```python
from index import search
from src.search import SearchMode

results = search("your question", mode=SearchMode.VECTOR)
```

Keyword-only search:

```python
from index import search
from src.search import SearchMode

results = search("your terms", mode=SearchMode.KEYWORD)
```

Hybrid search:

```python
from index import search
from src.search import SearchMode

results = search("your question", mode=SearchMode.HYBRID)
```

## 12. Check the database manually

Check registered PDFs:

```bash
psql -h localhost -U furba -d pdf_vector \
  -c "SELECT id, filename, pdf_path, embedding_generated FROM papers;"
```

Check chunk counts and embeddings:

```bash
psql -h localhost -U furba -d pdf_vector -c "
SELECT
    p.filename,
    COUNT(c.id) AS total_chunks,
    COUNT(c.embedding) AS total_embeddings
FROM papers p
LEFT JOIN paper_chunks c ON c.paper_id = p.id
GROUP BY p.filename;
"
```

View the text chunks for one PDF:

```bash
psql -h localhost -U furba -d pdf_vector -P pager=off -c "
SELECT
    c.chunk_index,
    c.chunk_text,
    c.page_number,
    c.embedding IS NOT NULL AS has_embedding
FROM paper_chunks c
JOIN papers p ON p.id = c.paper_id
WHERE p.filename = 'your-file.pdf'
ORDER BY c.chunk_index;
"
```

## Project structure

```text
.
├── config/settings.py       # Database, model, and PDF folder settings
├── index.py                 # Main Python functions: indexing and search
├── setup_db.py              # Creates the database tables
├── schema.sql               # PostgreSQL schema and indexes
├── requirements.txt         # Python dependencies
├── pdf/                     # Put your PDF files here
└── src/
    ├── paper_processor.py   # Registers local PDFs
    ├── pdf_processor.py     # Finds and validates PDFs
    ├── pdf_extractor.py     # Extracts PDF text
    ├── text_chunker.py      # Splits text into chunks
    ├── embeddings.py        # Creates 384-dimensional embeddings
    ├── embedding_pipeline.py# Stores chunks and embeddings
    └── search.py             # Vector, keyword, and hybrid search
```

## Common problems

### `schema.sql: No such file or directory`

Run the command from the project directory:

```bash
cd /path/to/Pdf_Search
python setup_db.py
```

### PostgreSQL asks for a password

Make sure the password in `.env` matches your PostgreSQL password. You can test the connection with:

```bash
psql -h localhost -U furba -d pdf_vector
```

### `type "vector" does not exist`

Enable pgvector as the PostgreSQL administrator:

```bash
sudo -u postgres psql -d pdf_vector \
  -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

### No results are returned

Make sure you ran indexing after copying the PDF into `pdf/`:

```bash
python - <<'PY'
from index import ingest_and_embed
print(ingest_and_embed())
PY
```

Then confirm that `paper_chunks` contains rows with embeddings.

### A scanned PDF has little or no text

This project extracts selectable text. Image-only scanned PDFs need OCR before they can be searched.
