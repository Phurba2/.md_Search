import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import (
    DB_HOST,
    DB_PORT,
    DB_NAME,
    DB_USER,
    DB_PASSWORD,
)

from src.embeddings import EmbeddingGenerator
from src.search import PaperSearchEngine, SearchMode


def main():

    db_config = {
        "host": DB_HOST,
        "port": DB_PORT,
        "dbname": DB_NAME,
        "user": DB_USER,
        "password": DB_PASSWORD,
    }

    embedding_generator = EmbeddingGenerator()

    search_engine = PaperSearchEngine(
        db_config=db_config,
        embedding_generator=embedding_generator,
    )

    query = "What does a LoRA-generating hypernetwork produce as output on a user's device?"

    print("\nSearching...")
    print("=" * 70)
    print(f"Query: {query}")

    results = search_engine.search(
        query=query,
        mode=SearchMode.VECTOR,
        limit=5,
    )

    print("\nResults:")
    print("=" * 70)

    for i, result in enumerate(results, start=1):

        print(f"\n{i}. {result.title}")
        print(f"   File:     {result.filename}")
        print(f"   Score:    {result.score:.4f}")

        if result.matched_chunks:
            chunk = result.matched_chunks[0]

            print(f"   Section:  {chunk['section_name']}")
            print(f"   Page:     {chunk['page_number']}")

            text = chunk["text"].replace("\n", " ")

            print(f"   Match:    {text[:300]}...")


if __name__ == "__main__":
    main()