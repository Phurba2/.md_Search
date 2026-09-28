import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.pdf_processor import PDFDownloader


def main():
    downloader = PDFDownloader()

    stats = downloader.get_storage_stats()

    print("PDF storage statistics:")
    print(f"  Files: {stats['total_files']}")
    print(f"  Size:  {stats['total_mb']} MB")


if __name__ == "__main__":
    main()
