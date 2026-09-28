import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.pdf_extractor import PDFExtractor
from src.text_chunker import TextChunker


def main():
    pdf_directory = (
        PROJECT_ROOT / "data" / "pdfs"
    )

    pdf_files = list(
        pdf_directory.rglob("*.pdf")
    )

    if not pdf_files:
        print("No PDF files found.")
        return

    pdf_path = pdf_files[0]

    extractor = PDFExtractor()

    result = extractor.extract_paper_text(
        str(pdf_path)
    )

    chunker = TextChunker(
        target_chunk_size=768,
        min_chunk_size=256,
        max_chunk_size=1024,
        overlap_size=128,
    )

    chunks = chunker.chunk_paper(
        text=result["text"],
        sections=result["sections"],
    )

    print("=" * 60)
    print("Chunking results")
    print("=" * 60)

    print(
        f"PDF: {pdf_path.name}"
    )

    print(
        f"Chunks: {len(chunks)}"
    )

    for index, chunk in enumerate(
        chunks[:5]
    ):
        print("\n" + "=" * 60)
        print(
            f"Chunk {index}"
        )
        print(
            f"Section: {chunk['section_name']}"
        )
        print(
            f"Estimated tokens: "
            f"{chunk['token_count']}"
        )
        print("-" * 60)
        print(
            chunk["text"][:1000]
        )


if __name__ == "__main__":
    main()