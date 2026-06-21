from pathlib import Path

from file_toolbox.reporting import ProcessResult, write_report


def test_write_report_creates_markdown(tmp_path):
    results = [
        ProcessResult(source=Path("a.docx"), output=Path("a_EN.docx"), status="成功", message=""),
        ProcessResult(source=Path("b.docx"), output=Path("b_EN.docx"), status="成功", message=""),
    ]
    report_path = write_report(results, tmp_path)
    assert report_path.exists()
    text = report_path.read_text(encoding="utf-8")
    assert "a.docx" in text
    assert "b_EN.docx" in text
    assert "成功" in text


def test_write_report_handles_empty_list(tmp_path):
    report_path = write_report([], tmp_path)
    assert report_path.exists()
    text = report_path.read_text(encoding="utf-8")
    assert "处理报告" in text
