import logging
from pathlib import Path
from typing import Dict

from config.settings import PDF_STORAGE_PATH

logger = logging.getLogger(__name__)


class PDFStorage:
    """Discover and validate PDFs supplied by the user."""

    def __init__(self, storage_path: str = str(PDF_STORAGE_PATH)):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

    def list_pdfs(self):
        return sorted(self.storage_path.rglob("*.pdf"))

    @staticmethod
    def validate_pdf(pdf_path: Path) -> bool:
        try:
            return (
                pdf_path.is_file()
                and pdf_path.stat().st_size >= 100
                and pdf_path.open("rb").read(5) == b"%PDF-"
            )
        except OSError:
            return False

    def get_storage_stats(self) -> Dict[str, object]:
        files = [path for path in self.list_pdfs() if self.validate_pdf(path)]
        total_bytes = sum(path.stat().st_size for path in files)
        return {
            "total_files": len(files),
            "total_bytes": total_bytes,
            "total_mb": round(total_bytes / (1024 * 1024), 2),
        }


# Backwards-compatible name for callers that only use storage statistics.
PDFDownloader = PDFStorage
