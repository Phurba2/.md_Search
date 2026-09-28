#!/usr/bin/env python3

import sys
from pathlib import Path

# Add the project root to Python's import path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import psycopg2

from config.settings import (
    DB_HOST,
    DB_PORT,
    DB_NAME,
    DB_USER,
    DB_PASSWORD,
)


def main():
    """Create the local PDF database schema."""

    project_root = Path(__file__).resolve().parent.parent
    schema_file = project_root / "schema.sql"

    print("Connecting to PostgreSQL...")

    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
    )

    print("Connected.")

    schema = schema_file.read_text()

    with conn.cursor() as cursor:
        cursor.execute(schema)

    conn.commit()
    conn.close()

    print("Database schema created successfully.")


if __name__ == "__main__":
    main()