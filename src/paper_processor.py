import logging
from pathlib import Path
from typing import Optional

import psycopg2
from psycopg2.extras import RealDictCursor

from config.settings import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
from src.pdf_processor import PDFStorage

logger = logging.getLogger(__name__)


class PaperProcessor:
    """Register PDFs already present in the configured PDF folder."""

    def __init__(self, db_config: dict, pdf_storage: Optional[PDFStorage] = None):
        self.db_config = db_config
        self.pdf_storage = pdf_storage or PDFStorage()

    def _get_connection(self):
        return psycopg2.connect(**self.db_config)

    def ingest_pdfs(self) -> dict:
        pdfs = [p for p in self.pdf_storage.list_pdfs() if self.pdf_storage.validate_pdf(p)]
        conn = self._get_connection()
        new = 0
        existing = 0
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                for pdf_path in pdfs:
                    filename = pdf_path.name
                    title = pdf_path.stem.replace("_", " ")
                    cursor.execute(
                        """
                        INSERT INTO papers (filename, title, pdf_path)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (filename) DO UPDATE SET
                            title = EXCLUDED.title,
                            pdf_path = EXCLUDED.pdf_path,
                            updated_at = CURRENT_TIMESTAMP
                        RETURNING (xmax = 0) AS inserted
                        """,
                        (filename, title, str(pdf_path)),
                    )
                    if cursor.fetchone()["inserted"]:
                        new += 1
                    else:
                        existing += 1
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
        return {"found": len(pdfs), "new": new, "existing": existing, "failed": 0}


def create_default_processor() -> PaperProcessor:
    return PaperProcessor(
        db_config={
            "host": DB_HOST,
            "port": DB_PORT,
            "dbname": DB_NAME,
            "user": DB_USER,
            "password": DB_PASSWORD,
        }
    )
