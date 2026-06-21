from pathlib import Path
from typing import Callable

from docx import Document
from pypdf import PdfReader
from pypdf.errors import PdfReadError

from file_toolbox.translator import Translator, chunk_text


class PdfTextError(RuntimeError):
    """Raised when a PDF has no extractable text."""


def translate_pdf_text(source: Path, output_dir: Path, translator: Translator) -> Path:
    return translate_pdf_text_to_language(source, output_dir, translator)


def translate_pdf_text_to_language(
    source: Path,
    output_dir: Path,
    translator: Translator,
    target_language: str = "English",
    source_language: str = "Auto-detect",
    target_suffix: str = "EN",
    progress_callback: Callable[[int, int], None] | None = None,
) -> Path:
    try:
        reader = PdfReader(str(source))
    except PdfReadError as exc:
        raise PdfTextError("PDF 没有可提取文字，可能是扫描版 PDF。") from exc
    text_parts = [(page.extract_text() or "").strip() for page in reader.pages]
    text = "\n\n".join(part for part in text_parts if part)
    if not text.strip():
        raise PdfTextError("PDF 没有可提取文字，可能是扫描版 PDF。")

    chunks = chunk_text(text)
    total = len(chunks)

    output_dir.mkdir(parents=True, exist_ok=True)
    document = Document()
    for idx, chunk in enumerate(chunks, 1):
        document.add_paragraph(translator.translate(chunk, target_language, source_language))
        if progress_callback:
            progress_callback(idx, total)
    output = output_dir / f"{source.stem}_{target_suffix}.docx"
    document.save(output)
    return output
