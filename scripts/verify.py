#!/usr/bin/env python3

"""Verify the local PDF search environment."""

import sys
from pathlib import Path

# Add the project root to Python's import path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

def check_imports():
    """Check required Python packages."""

    packages = {
        "PyMuPDF": "fitz",
        "psycopg2": "psycopg2",
        "sentence-transformers": "sentence_transformers",
        "requests": "requests",
        "numpy": "numpy",
        "tqdm": "tqdm",
        "python-dotenv": "dotenv",
        "pgvector": "pgvector",
    }

    print("Checking Python packages...")

    failed = []

    for name, module in packages.items():
        try:
            __import__(module)
            print(f"  OK  {name}")
        except ImportError as e:
            print(f"  FAIL {name}: {e}")
            failed.append(name)

    return len(failed) == 0


def check_postgresql():
    """Check PostgreSQL and pgvector."""

    import psycopg2

    from config.settings import (
        DB_HOST,
        DB_PORT,
        DB_NAME,
        DB_USER,
        DB_PASSWORD,
    )

    print("\nChecking PostgreSQL...")

    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
        )

        print("  OK  PostgreSQL connection")

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT extversion
            FROM pg_extension
            WHERE extname = 'vector';
            """
        )

        result = cursor.fetchone()

        if result:
            print(f"  OK  pgvector {result[0]}")
        else:
            print("  FAIL pgvector extension is not enabled")
            conn.close()
            return False

        cursor.close()
        conn.close()

        return True

    except Exception as e:
        print(f"  FAIL PostgreSQL: {e}")
        return False


def check_model_download():
    """Check that the embedding model can be loaded."""

    print("\nChecking embedding model...")

    from config.settings import (
        EMBEDDING_MODEL,
        EMBEDDING_DEVICE,
    )

    print(f"  Model: {EMBEDDING_MODEL}")
    print(f"  Device: {EMBEDDING_DEVICE}")

    try:
        from sentence_transformers import SentenceTransformer

        model = SentenceTransformer(
            EMBEDDING_MODEL,
            device=EMBEDDING_DEVICE,
        )

        dimension = model.get_sentence_embedding_dimension()

        print("  OK  Model loaded")
        print(f"  OK  Embedding dimension: {dimension}")

        return True

    except Exception as e:
        print(f"  FAIL Model: {e}")
        return False


def main():
    """Run all checks."""

    print("=" * 50)
    print("Local PDF Search Environment Verification")
    print("=" * 50)

    results = [
        check_imports(),
        check_postgresql(),
        check_model_download(),
    ]

    print("\n" + "=" * 50)

    if all(results):
        print("ALL CHECKS PASSED")
        return 0

    print("SOME CHECKS FAILED")
    return 1


if __name__ == "__main__":
    sys.exit(main())
