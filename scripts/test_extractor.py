import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.pdf_extractor import PDFExtractor


def main():
    pdf_directory = (
        PROJECT_ROOT / "data" / "pdfs"
    )

    pdf_files = list(
        pdf_directory.rglob("*.pdf")
    )

    if not pdf_files:
        print("No PDF files found.")
        print(
            "Run the paper processor first "
            "to download some papers."
        )
        return

    pdf_path = pdf_files[0]

    print(
        f"Testing PDF:\n{pdf_path}\n"
    )

    extractor = PDFExtractor()

    result = extractor.extract_paper_text(
        str(pdf_path)
    )

    print("=" * 60)
    print("Extraction results")
    print("=" * 60)

    print(
        f"Pages:      {result['page_count']}"
    )

    print(
        f"Confidence: {result['confidence']}"
    )

    print(
        f"Sections:   {len(result['sections'])}"
    )

    print("\nDetected sections:")

    for section in result["sections"]:
        print(
            f"  - {section['name']}"
        )

    print("\nFirst 2000 characters:")
    print("-" * 60)
    print(
        result["text"][:2000]
    )


if __name__ == "__main__":
    main()