import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.embeddings import EmbeddingGenerator


def main():

    generator = EmbeddingGenerator()

    texts = [
        "Transformers use self-attention mechanisms.",
        "PostgreSQL can store vector embeddings.",
        "Cats are domestic animals.",
    ]

    print("Generating embeddings...\n")

    embeddings = generator.generate_embeddings(
        texts,
        show_progress=True,
    )

    print("\nResults:")
    print(
        f"Shape: {embeddings.shape}"
    )

    print(
        f"Data type: {embeddings.dtype}"
    )

    print(
        f"Model dimension: "
        f"{generator.embedding_dimension}"
    )

    print("\nFirst vector:")
    print(
        embeddings[0]
    )

    query_embedding = (
        generator.generate_query_embedding(
            "How do transformer models work?"
        )
    )

    print(
        "\nQuery embedding shape:"
    )

    print(
        query_embedding.shape
    )


if __name__ == "__main__":
    main()