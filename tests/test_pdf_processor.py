from pathlib import Path

import pytest

from file_toolbox.processors.pdf import PdfTextError, translate_pdf_text
from conftest import FakeTranslator


def test_translate_pdf_text_rejects_missing_text_pdf(tmp_path: Path):
    source = tmp_path / "empty.pdf"
    source.write_bytes(b"%PDF-1.4\n%%EOF")

    with pytest.raises(PdfTextError, match="没有可提取文字"):
        translate_pdf_text(source, tmp_path / "translated", FakeTranslator())


def test_translate_pdf_text_creates_docx_with_fake_translator(tmp_path):
    from fpdf import FPDF

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    pdf.cell(text="Hello World from PDF")
    source = tmp_path / "test_hello.pdf"
    pdf.output(str(source))

    output = translate_pdf_text(source, tmp_path / "translated", FakeTranslator())

    assert output.suffix == ".docx"
    assert output.exists()
    import zipfile
    with zipfile.ZipFile(output) as z:
        assert any(n.startswith("word/") for n in z.namelist())
