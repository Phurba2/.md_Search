import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

import fitz


logger = logging.getLogger(__name__)


@dataclass
class ExtractedPage:
    """Structured representation of extracted page content."""

    page_num: int
    text: str
    blocks: List[Dict]
    has_columns: bool
    has_math: bool
    has_tables: bool
    confidence: float


class PDFExtractor:
    """Advanced PDF text extraction for academic papers."""

    def __init__(self):
        pass

    def extract_paper_text(
        self,
        pdf_path: str,
    ) -> Dict[str, object]:
        """Extract complete text from a PDF."""

        pdf_path = Path(pdf_path)

        if not pdf_path.exists():
            raise FileNotFoundError(
                f"PDF not found: {pdf_path}"
            )

        pages: List[ExtractedPage] = []

        document = fitz.open(pdf_path)

        try:
            for page_index, page in enumerate(document):
                page_num = page_index + 1

                extracted_page = self._extract_page(
                    page,
                    page_num,
                )

                pages.append(extracted_page)

        finally:
            document.close()

        full_text = "\n\n".join(
            page.text
            for page in pages
            if page.text.strip()
        )

        full_text = self._clean_extracted_text(
            full_text
        )

        sections = self._identify_sections(
            full_text
        )

        confidence = self._calculate_confidence(
            pages
        )

        return {
            "text": full_text,
            "pages": pages,
            "sections": sections,
            "page_count": len(pages),
            "confidence": confidence,
        }

    def _extract_page(
        self,
        page,
        page_num: int,
    ) -> ExtractedPage:
        """Extract text from one page with layout analysis."""

        raw_blocks = page.get_text(
            "blocks",
            sort=True,
        )

        blocks = []

        for block in raw_blocks:

            if len(block) < 5:
                continue

            x0, y0, x1, y1, text = block[:5]

            text = self._extract_block_text(
                {
                    "x0": x0,
                    "y0": y0,
                    "x1": x1,
                    "y1": y1,
                    "text": text,
                }
            )

            if not text:
                continue

            if self._is_noise(text):
                continue

            block_type = self._classify_block(
                text
            )

            blocks.append(
                {
                    "x0": x0,
                    "y0": y0,
                    "x1": x1,
                    "y1": y1,
                    "text": text,
                    "type": block_type,
                }
            )

        has_columns = self._detect_columns(
            blocks
        )

        if has_columns:
            ordered_blocks = self._extract_multicolumn(
                blocks
            )
        else:
            ordered_blocks = self._extract_singlecolumn(
                blocks
            )

        text = self._combine_blocks(
            ordered_blocks
        )

        has_math = any(
            block["type"] == "math"
            for block in ordered_blocks
        )

        has_tables = self._detect_tables(
            ordered_blocks
        )

        confidence = self._calculate_page_confidence(
            text,
            has_columns,
            page_num,
        )

        return ExtractedPage(
            page_num=page_num,
            text=text,
            blocks=ordered_blocks,
            has_columns=has_columns,
            has_math=has_math,
            has_tables=has_tables,
            confidence=confidence,
        )

    def _detect_columns(
        self,
        blocks: List[Dict],
    ) -> bool:
        """Detect whether a page probably has multiple columns."""

        if len(blocks) < 4:
            return False

        page_width = max(
            block["x1"]
            for block in blocks
        )

        if page_width <= 0:
            return False

        left_blocks = 0
        right_blocks = 0

        midpoint = page_width / 2

        for block in blocks:

            center_x = (
                block["x0"] + block["x1"]
            ) / 2

            if center_x < midpoint:
                left_blocks += 1
            else:
                right_blocks += 1

        return (
            left_blocks >= 2
            and right_blocks >= 2
        )

    def _extract_multicolumn(
        self,
        blocks: List[Dict],
    ) -> List[Dict]:
        """Order blocks from left column to right column."""

        columns = self._group_by_columns(
            blocks
        )

        ordered = []

        for column in columns:
            column.sort(
                key=lambda block: block["y0"]
            )

            ordered.extend(column)

        return ordered

    def _extract_singlecolumn(
        self,
        blocks: List[Dict],
    ) -> List[Dict]:
        """Order blocks vertically."""

        return sorted(
            blocks,
            key=lambda block: (
                block["y0"],
                block["x0"],
            ),
        )

    def _extract_block_text(
        self,
        block: Dict,
    ) -> str:
        """Clean text from an individual block."""

        text = block.get(
            "text",
            "",
        )

        text = text.replace(
            "\x00",
            "",
        )

        text = re.sub(
            r"[ \t]+",
            " ",
            text,
        )

        text = re.sub(
            r"\n{3,}",
            "\n\n",
            text,
        )

        return text.strip()

    def _group_by_columns(
        self,
        blocks: List[Dict],
    ) -> List[List[Dict]]:
        """Group blocks into approximate columns."""

        if not blocks:
            return []

        page_left = min(
            block["x0"]
            for block in blocks
        )

        page_right = max(
            block["x1"]
            for block in blocks
        )

        midpoint = (
            page_left + page_right
        ) / 2

        left = []
        right = []

        for block in blocks:

            center_x = (
                block["x0"] + block["x1"]
            ) / 2

            if center_x < midpoint:
                left.append(block)
            else:
                right.append(block)

        columns = []

        if left:
            columns.append(left)

        if right:
            columns.append(right)

        return columns

    def _combine_blocks(
        self,
        blocks: List[Dict],
    ) -> str:
        """Combine blocks into continuous text."""

        parts = []

        for block in blocks:

            text = block["text"].strip()

            if not text:
                continue

            parts.append(text)

        return "\n\n".join(parts)

    def _is_noise(
        self,
        text: str,
    ) -> bool:
        """Detect obvious headers, footers, and page numbers."""

        text = text.strip()

        if not text:
            return True

        # A block consisting only of a page number.
        if re.fullmatch(
            r"(page\s*)?\d+",
            text,
            flags=re.IGNORECASE,
        ):
            return True

        # Very short standalone noise.
        if len(text) <= 2:
            return True

        return False

    def _classify_block(
        self,
        text: str,
    ) -> str:
        """Classify a text block."""

        stripped = text.strip()

        # Common academic section headings.
        if re.match(
            r"^(abstract|introduction|background|"
            r"related work|methodology|methods|"
            r"experiments|results|discussion|"
            r"conclusion|conclusions|references)"
            r"\s*$",
            stripped,
            flags=re.IGNORECASE,
        ):
            return "heading"

        # Numbered headings such as:
        # 1 Introduction
        # 2.1 Dataset
        if re.match(
            r"^\d+(\.\d+)*\.?\s+\S+",
            stripped,
        ):
            if len(stripped) < 150:
                return "heading"

        # Simple mathematical-looking blocks.
        math_patterns = [
            r"\$.*\$",
            r"\\frac",
            r"\\sum",
            r"\\alpha",
            r"\\beta",
            r"∑",
            r"∫",
            r"≤",
            r"≥",
            r"≈",
        ]

        if any(
            re.search(pattern, stripped)
            for pattern in math_patterns
        ):
            return "math"

        # Figure/table captions.
        if re.match(
            r"^(figure|fig\.|table)\s+\d+",
            stripped,
            flags=re.IGNORECASE,
        ):
            return "caption"

        return "body"

    def _detect_tables(
        self,
        blocks: List[Dict],
    ) -> bool:
        """Heuristically detect tables."""

        table_keywords = re.compile(
            r"\b(table|column|row)\b",
            flags=re.IGNORECASE,
        )

        for block in blocks:

            if block["type"] == "caption":
                if re.match(
                    r"^table",
                    block["text"],
                    flags=re.IGNORECASE,
                ):
                    return True

            if table_keywords.search(
                block["text"]
            ):
                return True

        return False

    def _identify_sections(
        self,
        text: str,
    ) -> List[Dict]:
        """Identify likely document sections."""

        lines = text.splitlines()

        sections = []

        current_section = "Unknown"
        current_start = 0

        heading_pattern = re.compile(
            r"^(?:"
            r"\d+(?:\.\d+)*\.?\s+)?"
            r"(abstract|introduction|background|"
            r"related work|methods?|methodology|"
            r"experiments?|results?|discussion|"
            r"conclusions?|references)"
            r"$",
            flags=re.IGNORECASE,
        )

        position = 0

        for line in lines:

            stripped = line.strip()

            if not stripped:
                position += len(line) + 1
                continue

            if heading_pattern.match(
                stripped
            ):
                if current_start < position:
                    sections.append(
                        {
                            "name": current_section,
                            "start": current_start,
                            "end": position,
                        }
                    )

                current_section = stripped
                current_start = position

            position += len(line) + 1

        if current_start < len(text):
            sections.append(
                {
                    "name": current_section,
                    "start": current_start,
                    "end": len(text),
                }
            )

        return sections

    def _clean_extracted_text(
        self,
        text: str,
    ) -> str:
        """Clean extracted text for downstream processing."""

        # Remove excessive whitespace.
        text = re.sub(
            r"[ \t]+",
            " ",
            text,
        )

        # Normalize excessive blank lines.
        text = re.sub(
            r"\n{3,}",
            "\n\n",
            text,
        )

        # Fix spaces before punctuation.
        text = re.sub(
            r"\s+([,.;:!?])",
            r"\1",
            text,
        )

        return text.strip()

    def _calculate_page_confidence(
        self,
        text: str,
        has_columns: bool,
        page_num: int,
    ) -> float:
        """Calculate a simple page extraction confidence score."""

        if not text.strip():
            return 0.0

        score = 1.0

        # Very little text may indicate a problematic page.
        if len(text) < 100:
            score -= 0.25

        # Replacement characters often indicate encoding issues.
        replacement_count = text.count("�")

        if replacement_count:
            score -= min(
                0.5,
                replacement_count * 0.05,
            )

        # Column detection is not itself bad,
        # but adds complexity.
        if has_columns:
            score -= 0.05

        return max(
            0.0,
            min(1.0, score),
        )

    def _calculate_confidence(
        self,
        pages: List[ExtractedPage],
    ) -> float:
        """Calculate overall extraction confidence."""

        if not pages:
            return 0.0

        return round(
            sum(
                page.confidence
                for page in pages
            ) / len(pages),
            3,
        )