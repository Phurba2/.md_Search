import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.paper_processor import create_default_processor


def main():
    processor = create_default_processor(
        max_workers=2,
    )

    stats = processor.ingest_pdfs()

    print("\nProcessing results:")
    print(f"  Found:      {stats['found']}")
    print(f"  New:        {stats['new']}")
    print(f"  Existing:   {stats['existing']}")
    print(f"  Failed:     {stats['failed']}")


if __name__ == "__main__":
    main()