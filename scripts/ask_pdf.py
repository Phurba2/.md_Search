#!/usr/bin/env python3
"""Ask a question against the locally indexed PDFs."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
from src.embeddings import EmbeddingGenerator
from src.search import PaperSearchEngine, SearchMode


QUESTION = (
    "What is the difference between getting wealthy and staying wealthy, "
    "and how does the concept of survival relate to the psychology of money "
    "according to Morgan Housel?"
)


def main():
    question = " ".join(sys.argv[1:]).strip() or QUESTION

    db_config = {
        "host": DB_HOST,
        "port": DB_PORT,
        "dbname": DB_NAME,
        "user": DB_USER,
        "password": DB_PASSWORD,
    }

    engine = PaperSearchEngine(
        db_config=db_config,
        embedding_generator=EmbeddingGenerator(),
    )

    results = engine.search(
        query=question,
        mode=SearchMode.HYBRID,
        limit=1,
    )

    print(f"Question: {question}\n")

    if not results:
        print("No matching PDF chunks found.")
        return

    result = results[0]
    print(f"File: {result.filename}")
    print(f"Score: {result.score:.4f}\n")

    for index, chunk in enumerate(result.matched_chunks, start=1):
        print(f"--- Match {index} ---")
        print(chunk["text"])
        print()


if __name__ == "__main__":
    main()
