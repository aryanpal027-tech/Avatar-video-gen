from __future__ import annotations

from pathlib import Path

import fitz
import requests
import trafilatura
from bs4 import BeautifulSoup


def extract_from_url(url: str, timeout: int = 30) -> str:
    downloaded = trafilatura.fetch_url(url)
    if downloaded:
        text = trafilatura.extract(downloaded, include_comments=False, include_tables=False)
        if text and text.strip():
            return text.strip()

    response = requests.get(
        url,
        timeout=timeout,
        headers={"User-Agent": "Mozilla/5.0 AvatarVideoGen/1.0"},
    )
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "aside"]):
        tag.decompose()
    text = "\n".join(line.strip() for line in soup.get_text("\n").splitlines() if line.strip())
    if not text:
        raise ValueError("Could not extract readable text from URL.")
    return text


def extract_from_pdf(pdf_path: str | Path) -> str:
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(pdf_path)
    doc = fitz.open(pdf_path)
    pages = [page.get_text("text") for page in doc]
    text = "\n\n".join(page.strip() for page in pages if page.strip())
    if not text:
        raise ValueError("No extractable text found in PDF. Scanned PDFs may require OCR.")
    return text


def save_text(text: str, output_path: str | Path) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(text, encoding="utf-8")
    return output_path
