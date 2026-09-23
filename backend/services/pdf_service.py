from pathlib import Path
from pypdf import PdfReader
import re

from core.config import MAX_PDF_PAGES


def normalize_extracted_text(text: str) -> str:
    if not text:
        return ""

    text = text.replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    lines = [line.strip() for line in text.split("\n")]
    cleaned_lines = []

    for line in lines:
        if not line:
            continue
        if len(line) == 1:
            continue
        cleaned_lines.append(line)

    text = "\n".join(cleaned_lines).strip()
    text = re.sub(r"[ ]{2,}", " ", text)

    return text


def extract_text_from_pdf(file_path: Path, max_pages: int = MAX_PDF_PAGES) -> tuple:
    """(metin, işlenen sayfa sayısı, toplam sayfa sayısı) döndürür."""
    reader = PdfReader(str(file_path))
    total_pages = len(reader.pages)
    pages = reader.pages[:max_pages]
    processed_pages = len(pages)

    parts = []
    for page in pages:
        txt = page.extract_text() or ""
        if txt.strip():
            parts.append(txt)

    raw_text = "\n".join(parts).strip()
    return normalize_extracted_text(raw_text), processed_pages, total_pages