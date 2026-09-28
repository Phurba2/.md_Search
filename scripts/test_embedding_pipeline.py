import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.embedding_pipeline import create_default_pipeline


def main():
    pipeline = create_default_pipeline()

    result = pipeline.process_pending_papers(limit=3)

    print("\nEmbedding pipeline results:")
    print("=" * 50)

    for key, value in result.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
