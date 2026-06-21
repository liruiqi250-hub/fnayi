# Batch File Toolbox Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Windows desktop EXE for batch Word translation, Excel translation/cleanup, PDF text translation, and safe file renaming/organization using DeepSeek.

**Architecture:** The app will be a Python project with a small service layer for file processing and a desktop GUI layer for user interaction. Core file operations will be testable without launching the GUI; DeepSeek calls will be wrapped behind one translator interface so tests can use a fake translator.

**Tech Stack:** Python 3.11+, PySide6, python-docx, openpyxl, pypdf, python-dotenv, openai-compatible DeepSeek API client, pytest, PyInstaller.

---

## File Structure

- Create: `pyproject.toml` - project metadata and dependencies.
- Create: `README.md` - plain Chinese usage notes for non-technical users.
- Create: `src/file_toolbox/__init__.py` - package marker.
- Create: `src/file_toolbox/config.py` - reads `.env` and validates DeepSeek settings.
- Create: `src/file_toolbox/translator.py` - DeepSeek translator and fake translator interface.
- Create: `src/file_toolbox/reporting.py` - success/failure report records and markdown report writer.
- Create: `src/file_toolbox/processors/word.py` - `.docx` translation.
- Create: `src/file_toolbox/processors/excel.py` - `.xlsx` translation and cleanup.
- Create: `src/file_toolbox/processors/pdf.py` - text PDF extraction and Word export.
- Create: `src/file_toolbox/processors/organizer.py` - safe copy, rename, and folder organization.
- Create: `src/file_toolbox/gui.py` - PySide6 desktop interface.
- Create: `src/file_toolbox/main.py` - app entry point.
- Create: `tests/fixtures/` - generated sample test files.
- Create: `tests/test_config.py` - configuration tests.
- Create: `tests/test_translator.py` - chunking/fake translation tests.
- Create: `tests/test_word_processor.py` - Word translation tests.
- Create: `tests/test_excel_processor.py` - Excel translation/cleanup tests.
- Create: `tests/test_pdf_processor.py` - PDF extraction behavior tests.
- Create: `tests/test_organizer.py` - file organization safety tests.
- Create: `scripts/build_exe.ps1` - PyInstaller build command.

This folder is not currently a git repository, so "commit" steps below mean "run the verification command and checkpoint the changed files." If a git repository is initialized later, use the listed files as commit boundaries.

---

### Task 1: Project Scaffold And Configuration

**Files:**
- Create: `pyproject.toml`
- Create: `README.md`
- Create: `src/file_toolbox/__init__.py`
- Create: `src/file_toolbox/config.py`
- Test: `tests/test_config.py`

- [ ] **Step 1: Create the package and dependency metadata**

Add `pyproject.toml`:

```toml
[project]
name = "batch-file-toolbox"
version = "0.1.0"
description = "Windows desktop toolbox for translating and organizing office files."
requires-python = ">=3.11"
dependencies = [
  "openai>=1.0.0",
  "python-dotenv>=1.0.0",
  "python-docx>=1.1.0",
  "openpyxl>=3.1.0",
  "pypdf>=4.0.0",
  "PySide6>=6.7.0",
]

[project.optional-dependencies]
dev = [
  "pytest>=8.0.0",
  "pyinstaller>=6.0.0",
]

[tool.pytest.ini_options]
pythonpath = ["src"]
testpaths = ["tests"]
```

Add `src/file_toolbox/__init__.py`:

```python
__all__ = ["config", "translator"]
```

- [ ] **Step 2: Write the failing config tests**

Add `tests/test_config.py`:

```python
from pathlib import Path

import pytest

from file_toolbox.config import AppConfig, ConfigError, load_config


def test_load_config_reads_deepseek_values(tmp_path: Path):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "DEEPSEEK_API_KEY=sk-test\n"
        "DEEPSEEK_BASE_URL=https://api.deepseek.com\n"
        "DEEPSEEK_MODEL=deepseek-v4-pro\n",
        encoding="utf-8",
    )

    config = load_config(env_file)

    assert config == AppConfig(
        api_key="sk-test",
        base_url="https://api.deepseek.com",
        model="deepseek-v4-pro",
    )


def test_load_config_rejects_missing_api_key(tmp_path: Path):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "DEEPSEEK_BASE_URL=https://api.deepseek.com\n"
        "DEEPSEEK_MODEL=deepseek-v4-pro\n",
        encoding="utf-8",
    )

    with pytest.raises(ConfigError, match="DeepSeek API Key"):
        load_config(env_file)
```

- [ ] **Step 3: Run test to verify it fails**

Run: `python -m pytest tests/test_config.py -v`

Expected: FAIL because `file_toolbox.config` does not exist.

- [ ] **Step 4: Implement config loading**

Add `src/file_toolbox/config.py`:

```python
from dataclasses import dataclass
from pathlib import Path

from dotenv import dotenv_values


class ConfigError(RuntimeError):
    """User-facing configuration error."""


@dataclass(frozen=True)
class AppConfig:
    api_key: str
    base_url: str = "https://api.deepseek.com"
    model: str = "deepseek-v4-pro"


def load_config(env_path: Path | str = ".env") -> AppConfig:
    values = dotenv_values(env_path)
    api_key = (values.get("DEEPSEEK_API_KEY") or "").strip()
    base_url = (values.get("DEEPSEEK_BASE_URL") or "https://api.deepseek.com").strip()
    model = (values.get("DEEPSEEK_MODEL") or "deepseek-v4-pro").strip()

    if not api_key or "在这里粘贴" in api_key:
        raise ConfigError("没有配置 DeepSeek API Key，请检查 .env 文件。")

    return AppConfig(api_key=api_key, base_url=base_url, model=model)
```

- [ ] **Step 5: Add beginner usage notes**

Add `README.md`:

```markdown
# 批量文件工具箱

这是一个 Windows 桌面工具，用来批量处理 Word、Excel、PDF 和文件夹资料。

第一版功能：

- Word 翻译成英文
- Excel 翻译/整理
- PDF 提取文字并翻译成英文 Word
- 文件批量重命名和整理

使用前需要在 `.env` 文件中配置：

```env
DEEPSEEK_API_KEY=你的DeepSeek密钥
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-pro
```
```

- [ ] **Step 6: Verify Task 1**

Run: `python -m pytest tests/test_config.py -v`

Expected: PASS.

---

### Task 2: Translator And Report Foundation

**Files:**
- Create: `src/file_toolbox/translator.py`
- Create: `src/file_toolbox/reporting.py`
- Test: `tests/test_translator.py`

- [ ] **Step 1: Write translator tests**

Add `tests/test_translator.py`:

```python
from file_toolbox.translator import FakeTranslator, chunk_text


def test_chunk_text_keeps_short_text_as_one_chunk():
    assert chunk_text("hello", max_chars=10) == ["hello"]


def test_chunk_text_splits_on_paragraph_boundaries():
    text = "one\n\ntwo\n\nthree"
    assert chunk_text(text, max_chars=8) == ["one\ntwo", "three"]


def test_fake_translator_marks_output():
    translator = FakeTranslator(prefix="[EN] ")
    assert translator.translate("你好") == "[EN] 你好"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_translator.py -v`

Expected: FAIL because `file_toolbox.translator` does not exist.

- [ ] **Step 3: Implement translator module**

Add `src/file_toolbox/translator.py`:

```python
from dataclasses import dataclass
from typing import Protocol

from openai import OpenAI

from file_toolbox.config import AppConfig


class Translator(Protocol):
    def translate(self, text: str, target_language: str = "English") -> str:
        ...


def chunk_text(text: str, max_chars: int = 3500) -> list[str]:
    paragraphs = [part.strip() for part in text.split("\n\n") if part.strip()]
    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        candidate = paragraph if not current else f"{current}\n{paragraph}"
        if len(candidate) <= max_chars:
            current = candidate
        else:
            if current:
                chunks.append(current)
            current = paragraph
    if current:
        chunks.append(current)
    return chunks


@dataclass
class FakeTranslator:
    prefix: str = "[EN] "

    def translate(self, text: str, target_language: str = "English") -> str:
        return f"{self.prefix}{text}"


class DeepSeekTranslator:
    def __init__(self, config: AppConfig):
        self._config = config
        self._client = OpenAI(api_key=config.api_key, base_url=config.base_url)

    def translate(self, text: str, target_language: str = "English") -> str:
        if not text.strip():
            return text
        response = self._client.chat.completions.create(
            model=self._config.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Translate the user's text into clear professional English. "
                        "Preserve names, numbers, product codes, and formatting markers."
                    ),
                },
                {"role": "user", "content": text},
            ],
            temperature=0.2,
        )
        return response.choices[0].message.content or ""
```

- [ ] **Step 4: Implement report writer**

Add `src/file_toolbox/reporting.py`:

```python
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProcessResult:
    source: Path
    output: Path | None
    status: str
    message: str


def write_report(results: list[ProcessResult], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / "处理报告.md"
    lines = ["# 处理报告", ""]
    for result in results:
        output = str(result.output) if result.output else "-"
        lines.append(f"- {result.status}: {result.source} -> {output} ({result.message})")
    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path
```

- [ ] **Step 5: Verify Task 2**

Run: `python -m pytest tests/test_translator.py -v`

Expected: PASS.

---

### Task 3: Core File Processors

**Files:**
- Create: `src/file_toolbox/processors/__init__.py`
- Create: `src/file_toolbox/processors/word.py`
- Create: `src/file_toolbox/processors/excel.py`
- Create: `src/file_toolbox/processors/pdf.py`
- Create: `src/file_toolbox/processors/organizer.py`
- Test: `tests/test_word_processor.py`
- Test: `tests/test_excel_processor.py`
- Test: `tests/test_pdf_processor.py`
- Test: `tests/test_organizer.py`

- [ ] **Step 1: Write Word processor test**

Add `tests/test_word_processor.py`:

```python
from pathlib import Path

from docx import Document

from file_toolbox.processors.word import translate_docx
from file_toolbox.translator import FakeTranslator


def test_translate_docx_creates_english_copy(tmp_path: Path):
    source = tmp_path / "说明书.docx"
    doc = Document()
    doc.add_heading("产品说明", level=1)
    doc.add_paragraph("这是一个仿真恐龙。")
    doc.save(source)

    output = translate_docx(source, tmp_path / "translated", FakeTranslator())

    assert output.name == "说明书_EN.docx"
    translated = Document(output)
    text = "\n".join(p.text for p in translated.paragraphs)
    assert "[EN] 产品说明" in text
    assert "[EN] 这是一个仿真恐龙。" in text
```

- [ ] **Step 2: Write Excel processor test**

Add `tests/test_excel_processor.py`:

```python
from pathlib import Path

from openpyxl import Workbook, load_workbook

from file_toolbox.processors.excel import translate_xlsx
from file_toolbox.translator import FakeTranslator


def test_translate_xlsx_translates_selected_column(tmp_path: Path):
    source = tmp_path / "产品.xlsx"
    wb = Workbook()
    ws = wb.active
    ws.append(["编号", "中文名称"])
    ws.append(["A1", "霸王龙"])
    wb.save(source)

    output = translate_xlsx(source, tmp_path / "translated", FakeTranslator(), columns=[2])

    ws_out = load_workbook(output).active
    assert ws_out["A2"].value == "A1"
    assert ws_out["B2"].value == "[EN] 霸王龙"
```

- [ ] **Step 3: Write organizer test**

Add `tests/test_organizer.py`:

```python
from pathlib import Path

from file_toolbox.processors.organizer import organize_folder


def test_organize_folder_copies_files_without_deleting_sources(tmp_path: Path):
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    docx = source_dir / "产品 说明.docx"
    image = source_dir / "图片 1.jpg"
    docx.write_text("doc", encoding="utf-8")
    image.write_text("img", encoding="utf-8")

    output_dir = organize_folder(source_dir, tmp_path / "organized", replace_spaces=True)

    assert docx.exists()
    assert image.exists()
    assert (output_dir / "Word" / "产品_说明.docx").exists()
    assert (output_dir / "Images" / "图片_1.jpg").exists()
```

- [ ] **Step 4: Write PDF processor test**

Add `tests/test_pdf_processor.py`:

```python
from pathlib import Path

import pytest

from file_toolbox.processors.pdf import PdfTextError, translate_pdf_text
from file_toolbox.translator import FakeTranslator


def test_translate_pdf_text_rejects_missing_text_pdf(tmp_path: Path):
    source = tmp_path / "empty.pdf"
    source.write_bytes(b"%PDF-1.4\n%%EOF")

    with pytest.raises(PdfTextError, match="没有可提取文字"):
        translate_pdf_text(source, tmp_path / "translated", FakeTranslator())
```

- [ ] **Step 5: Implement processors**

Add `src/file_toolbox/processors/__init__.py`:

```python
__all__ = ["word", "excel", "pdf", "organizer"]
```

Add `src/file_toolbox/processors/word.py`:

```python
from pathlib import Path

from docx import Document

from file_toolbox.translator import Translator


def translate_docx(source: Path, output_dir: Path, translator: Translator) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    document = Document(source)
    for paragraph in document.paragraphs:
        if paragraph.text.strip():
            paragraph.text = translator.translate(paragraph.text)
    for table in document.tables:
        for row in table.rows:
            for cell in row.cells:
                if cell.text.strip():
                    cell.text = translator.translate(cell.text)
    output = output_dir / f"{source.stem}_EN.docx"
    document.save(output)
    return output
```

Add `src/file_toolbox/processors/excel.py`:

```python
from pathlib import Path

from openpyxl import load_workbook

from file_toolbox.translator import Translator


def translate_xlsx(
    source: Path,
    output_dir: Path,
    translator: Translator,
    columns: list[int] | None = None,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    workbook = load_workbook(source)
    selected = set(columns or [])
    for sheet in workbook.worksheets:
        for row in sheet.iter_rows():
            for cell in row:
                if selected and cell.column not in selected:
                    continue
                if isinstance(cell.value, str) and cell.value.strip():
                    cell.value = translator.translate(cell.value.strip())
    output = output_dir / f"{source.stem}_EN.xlsx"
    workbook.save(output)
    return output
```

Add `src/file_toolbox/processors/pdf.py`:

```python
from pathlib import Path

from docx import Document
from pypdf import PdfReader

from file_toolbox.translator import Translator, chunk_text


class PdfTextError(RuntimeError):
    """Raised when a PDF has no extractable text."""


def translate_pdf_text(source: Path, output_dir: Path, translator: Translator) -> Path:
    reader = PdfReader(str(source))
    text_parts = [(page.extract_text() or "").strip() for page in reader.pages]
    text = "\n\n".join(part for part in text_parts if part)
    if not text.strip():
        raise PdfTextError("PDF 没有可提取文字，可能是扫描版 PDF。")

    output_dir.mkdir(parents=True, exist_ok=True)
    document = Document()
    for chunk in chunk_text(text):
        document.add_paragraph(translator.translate(chunk))
    output = output_dir / f"{source.stem}_EN.docx"
    document.save(output)
    return output
```

Add `src/file_toolbox/processors/organizer.py`:

```python
from pathlib import Path
from shutil import copy2


TYPE_DIRS = {
    ".doc": "Word",
    ".docx": "Word",
    ".xls": "Excel",
    ".xlsx": "Excel",
    ".pdf": "PDF",
    ".jpg": "Images",
    ".jpeg": "Images",
    ".png": "Images",
    ".webp": "Images",
}


def organize_folder(source_dir: Path, output_dir: Path, replace_spaces: bool = True) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    for source in source_dir.iterdir():
        if not source.is_file():
            continue
        category = TYPE_DIRS.get(source.suffix.lower(), "Other")
        target_dir = output_dir / category
        target_dir.mkdir(parents=True, exist_ok=True)
        name = source.name.replace(" ", "_") if replace_spaces else source.name
        copy2(source, target_dir / name)
    return output_dir
```

- [ ] **Step 6: Verify Task 3**

Run: `python -m pytest tests/test_word_processor.py tests/test_excel_processor.py tests/test_pdf_processor.py tests/test_organizer.py -v`

Expected: PASS.

---

### Task 4: Desktop GUI

**Files:**
- Create: `src/file_toolbox/gui.py`
- Create: `src/file_toolbox/main.py`
- Test: manual launch only for first version.

- [ ] **Step 1: Create GUI entry point**

Add `src/file_toolbox/main.py`:

```python
from file_toolbox.gui import run_app


if __name__ == "__main__":
    run_app()
```

- [ ] **Step 2: Implement the first desktop window**

Add `src/file_toolbox/gui.py`:

```python
from pathlib import Path
import sys

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QProgressBar,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from file_toolbox.config import ConfigError, load_config
from file_toolbox.processors.excel import translate_xlsx
from file_toolbox.processors.organizer import organize_folder
from file_toolbox.processors.pdf import PdfTextError, translate_pdf_text
from file_toolbox.processors.word import translate_docx
from file_toolbox.translator import DeepSeekTranslator


TOOLS = ["Word 翻译", "Excel 翻译/整理", "PDF 转文字/翻译", "批量重命名/整理"]


class Worker(QThread):
    finished_message = Signal(str)
    failed_message = Signal(str)

    def __init__(self, tool: str, paths: list[Path]):
        super().__init__()
        self.tool = tool
        self.paths = paths

    def run(self):
        try:
            config = load_config()
            translator = DeepSeekTranslator(config)
            outputs: list[Path] = []
            if self.tool == "Word 翻译":
                for path in self.paths:
                    outputs.append(translate_docx(path, path.parent / "translated", translator))
            elif self.tool == "Excel 翻译/整理":
                for path in self.paths:
                    outputs.append(translate_xlsx(path, path.parent / "translated", translator))
            elif self.tool == "PDF 转文字/翻译":
                for path in self.paths:
                    outputs.append(translate_pdf_text(path, path.parent / "translated", translator))
            else:
                outputs.append(organize_folder(self.paths[0], self.paths[0].parent / "organized"))
            self.finished_message.emit("处理完成：\n" + "\n".join(str(path) for path in outputs))
        except ConfigError as exc:
            self.failed_message.emit(str(exc))
        except PdfTextError as exc:
            self.failed_message.emit(str(exc))
        except Exception as exc:
            self.failed_message.emit(f"处理失败：{exc}")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("批量文件工具箱")
        self.resize(980, 620)
        self.paths: list[Path] = []
        self.worker: Worker | None = None

        self.tools = QListWidget()
        for tool in TOOLS:
            QListWidgetItem(tool, self.tools)
        self.tools.setCurrentRow(0)
        self.tools.currentTextChanged.connect(self._tool_changed)

        self.title = QLabel("Word 翻译")
        self.title.setStyleSheet("font-size: 22px; font-weight: 700;")
        self.help = QLabel("选择一个或多个 Word 文件，导出英文 Word。")
        self.help.setWordWrap(True)

        self.selected = QTextEdit()
        self.selected.setReadOnly(True)
        self.selected.setPlaceholderText("还没有选择文件")

        self.choose_button = QPushButton("选择文件")
        self.choose_button.clicked.connect(self._choose)
        self.start_button = QPushButton("开始处理")
        self.start_button.clicked.connect(self._start)
        self.progress = QProgressBar()
        self.progress.setRange(0, 1)
        self.progress.setValue(0)

        right = QVBoxLayout()
        right.addWidget(self.title)
        right.addWidget(self.help)
        right.addWidget(self.selected, stretch=1)
        right.addWidget(self.choose_button)
        right.addWidget(self.start_button)
        right.addWidget(self.progress)

        layout = QHBoxLayout()
        layout.addWidget(self.tools, 1)
        content = QWidget()
        content.setLayout(right)
        layout.addWidget(content, 3)

        root = QWidget()
        root.setLayout(layout)
        self.setCentralWidget(root)

    def _tool_changed(self, tool: str):
        self.title.setText(tool)
        self.paths = []
        self.selected.clear()
        if tool == "批量重命名/整理":
            self.choose_button.setText("选择文件夹")
            self.help.setText("选择一个文件夹，软件会复制整理到新的 organized 文件夹。")
        else:
            self.choose_button.setText("选择文件")
            self.help.setText("选择一个或多个文件，软件会导出到 translated 文件夹。")

    def _choose(self):
        tool = self.tools.currentItem().text()
        if tool == "批量重命名/整理":
            folder = QFileDialog.getExistingDirectory(self, "选择文件夹")
            self.paths = [Path(folder)] if folder else []
        else:
            filters = {
                "Word 翻译": "Word 文件 (*.docx)",
                "Excel 翻译/整理": "Excel 文件 (*.xlsx)",
                "PDF 转文字/翻译": "PDF 文件 (*.pdf)",
            }
            files, _ = QFileDialog.getOpenFileNames(self, "选择文件", "", filters[tool])
            self.paths = [Path(file) for file in files]
        self.selected.setText("\n".join(str(path) for path in self.paths))

    def _start(self):
        if not self.paths:
            QMessageBox.warning(self, "没有选择文件", "请先选择文件或文件夹。")
            return
        self.progress.setRange(0, 0)
        self.worker = Worker(self.tools.currentItem().text(), self.paths)
        self.worker.finished_message.connect(self._done)
        self.worker.failed_message.connect(self._failed)
        self.worker.start()

    def _done(self, message: str):
        self.progress.setRange(0, 1)
        self.progress.setValue(1)
        QMessageBox.information(self, "完成", message)

    def _failed(self, message: str):
        self.progress.setRange(0, 1)
        self.progress.setValue(0)
        QMessageBox.critical(self, "出错了", message)


def run_app():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
```

- [ ] **Step 3: Verify GUI starts**

Run: `python -m file_toolbox.main`

Expected: A window titled `批量文件工具箱` opens and shows the four left-side tools.

---

### Task 5: Build EXE And Final Verification

**Files:**
- Create: `scripts/build_exe.ps1`
- Modify: `README.md`

- [ ] **Step 1: Add build script**

Add `scripts/build_exe.ps1`:

```powershell
$ErrorActionPreference = "Stop"
python -m PyInstaller `
  --name "批量文件工具箱" `
  --noconfirm `
  --windowed `
  --paths "src" `
  "src/file_toolbox/main.py"
Write-Host "EXE built at dist\批量文件工具箱\批量文件工具箱.exe"
```

- [ ] **Step 2: Update README with run and build commands**

Append to `README.md`:

```markdown
## 开发运行

```powershell
python -m pip install -e ".[dev]"
python -m file_toolbox.main
```

## 打包 EXE

```powershell
.\scripts\build_exe.ps1
```

打包完成后，EXE 在：

```text
dist\批量文件工具箱\批量文件工具箱.exe
```
```

- [ ] **Step 3: Run full automated tests**

Run: `python -m pytest -v`

Expected: PASS.

- [ ] **Step 4: Build the EXE**

Run: `.\scripts\build_exe.ps1`

Expected: PyInstaller finishes and creates `dist\批量文件工具箱\批量文件工具箱.exe`.

- [ ] **Step 5: Manual smoke test**

Run the EXE and verify:

- The app opens without a console window.
- The four left-side tools are visible.
- Missing `.env` or placeholder API key shows a Chinese warning.
- Selecting files displays their paths.
- Batch organize copies files into an `organized` folder without deleting originals.

---

## Self-Review

- Spec coverage: The plan covers DeepSeek config, Word translation, Excel translation, PDF text translation, file organization, GUI, build, and tests.
- Scope control: OCR, image content recognition, terminology libraries, and advanced layout preservation remain out of first version.
- Placeholder scan: The plan contains no unfinished marker items or vague fill-in-later steps.
- Type consistency: Processor functions all accept `Path` inputs and return output `Path`; translator interface exposes `translate(text, target_language="English")`.
