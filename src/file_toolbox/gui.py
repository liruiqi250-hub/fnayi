from dataclasses import dataclass
from pathlib import Path
import sys
import logging
import traceback
import subprocess

from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QShortcut, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
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

from file_toolbox.config import ConfigError
from file_toolbox.languages import LANGUAGES, language_prompt_name, language_suffix
from file_toolbox.processors.excel import translate_xlsx_to_language
from file_toolbox.processors.pdf import PdfTextError, translate_pdf_text_to_language
from file_toolbox.processors.word import translate_docx_to_language
from file_toolbox.processors.organizer import organize_folder
from file_toolbox.reporting import ProcessResult, write_report
from file_toolbox.translator import DeepSeekTranslator, GoogleFreeTranslator, MyMemoryFreeTranslator
from file_toolbox.settings import AppSettings, SettingsDialog, load_settings, resolve_api_config


@dataclass(frozen=True)
class ToolOption:
    key: str
    label: str
    help_text: str
    choose_text: str
    file_filter: str | None
    uses_translation: bool
    uses_text_input: bool = False


TOOLS = [
    ToolOption("word", "Word 翻译", "选择多个 Word 文件，输出翻译后的 Word 文档。", "选择 Word 文件", "Word 文件 (*.doc *.docx)", True),
    ToolOption("excel", "Excel 翻译/整理", "选择多个 Excel 文件，输出翻译后的 Excel 文档。", "选择 Excel 文件", "Excel 文件 (*.xlsx *.xlsm)", True),
    ToolOption("pdf", "PDF 转文本/翻译", "选择多个文字型 PDF，输出翻译后的 Word 文档。", "选择 PDF 文件", "PDF 文件 (*.pdf)", True),
    ToolOption("organizer", "文件整理", "按类型自动分类整理文件到不同文件夹。", "选择文件夹", None, False),
    ToolOption("text", "文本翻译", "粘贴文字并翻译，支持多种翻译引擎。", "", None, True, True),
]


ENGINES = [
    ("google", "Google 翻译 (免费，无需 Key)"),
    ("mymemory", "MyMemory 翻译 (免费，无需 Key)"),
    ("custom", "自定义大模型 (需 API Key)"),
]

_TRANSLATOR_BUILDERS = {
    "google": lambda _s: GoogleFreeTranslator(),
    "mymemory": lambda _s: MyMemoryFreeTranslator(),
    }

_PROCESSOR_DISPATCH = {
    "word": lambda path, translator, src_lang, tgt_lang, suffix, cb:
        translate_docx_to_language(path, path.parent / "translated", translator,
            target_language=tgt_lang, source_language=src_lang, target_suffix=suffix, progress_callback=cb),
    "excel": lambda path, translator, src_lang, tgt_lang, suffix, cb:
        translate_xlsx_to_language(path, path.parent / "translated", translator,
            target_language=tgt_lang, source_language=src_lang, target_suffix=suffix, progress_callback=cb),
    "pdf": lambda path, translator, src_lang, tgt_lang, suffix, cb:
        translate_pdf_text_to_language(path, path.parent / "translated", translator,
            target_language=tgt_lang, source_language=src_lang, target_suffix=suffix, progress_callback=cb),
}

_TOOL_EXTENSIONS = {
    "word": {".doc", ".docx"},
    "excel": {".xlsx", ".xlsm"},
    "pdf": {".pdf"},
    "organizer": set(),
    "text": set(),
}


def _tool_extensions(tool):
    return _TOOL_EXTENSIONS.get(tool.key)


STYLESHEET_LIGHT = """QMainWindow {
    background-color: #f1f5f9;
    color: #0f172a;
}
QDialog {
    background-color: #ffffff;
    color: #0f172a;
}
QMessageBox {
    background-color: #ffffff;
    color: #0f172a;
}
QMessageBox QLabel {
    color: #0f172a;
}
QLabel {
    color: #0f172a;
}
QCheckBox {
    color: #0f172a;
}
QComboBox {
    color: #0f172a;
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    padding: 4px 8px;
    border-radius: 4px;
}
QComboBox QAbstractItemView {
    color: #0f172a;
    background-color: #ffffff;
    selection-background-color: #2563eb;
    selection-color: #ffffff;
}
QTextEdit {
    color: #0f172a;
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 4px;
}
QProgressBar {
    color: #0f172a;
    border: 1px solid #cbd5e1;
    border-radius: 4px;
    text-align: center;
}
QProgressBar::chunk {
    background-color: #2563eb;
    border-radius: 3px;
}
QListWidget {
    border: none;
    background: transparent;
    font-size: 14px;
    color: #0f172a;
}
QListWidget::item {
    padding: 10px 16px;
    border-radius: 6px;
    margin: 2px 0;
}
QListWidget::item:selected {
    background-color: #2563eb;
    color: white;
}
QListWidget::item:hover:!selected {
    background-color: #e2e8f0;
}
QLabel#title {
    font-size: 22px;
    font-weight: bold;
    color: #0f172a;
    padding: 8px 0;
}
QLabel#help {
    font-size: 13px;
    color: #475569;
    padding: 0 0 12px 0;
}
QPushButton {
    background-color: #2563eb;
    color: white;
    border: none;
    padding: 10px 24px;
    border-radius: 6px;
    font-size: 14px;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #1d4ed8;
}
QPushButton:disabled {
    background-color: #93c5fd;
}
QPushButton#choose_button {
    background-color: #e2e8f0;
    color: #1e293b;
}
QPushButton#choose_button:hover {
    background-color: #cbd5e1;
}
QPushButton#settings_button {
    background-color: transparent;
    color: #64748b;
    font-size: 18px;
    padding: 6px;
}
QPushButton#settings_button:hover {
    color: #0f172a;
}
QPushButton#swap_button {
    background-color: transparent;
    color: #64748b;
    border: 1px solid #cbd5e1;
    padding: 4px 12px;
    font-size: 12px;
    min-width: 30px;
}
QPushButton#swap_button:hover {
    background-color: #e2e8f0;
}
QPushButton#theme_button {
    background-color: transparent;
    color: #64748b;
    font-size: 18px;
    padding: 6px;
    border: none;
}
QPushButton#theme_button:hover {
    color: #0f172a;
}
QPushButton#save_word_btn {
    background-color: #22c55e;
    color: white;
    border: none;
    padding: 6px 12px;
    border-radius: 4px;
    font-size: 12px;
}
QPushButton#save_word_btn:hover {
    background-color: #16a34a;
}
QPushButton#stop_button {
    background-color: #ef4444;
    color: white;
    border: none;
    padding: 10px 24px;
    border-radius: 6px;
    font-size: 14px;
    font-weight: bold;
}
QPushButton#stop_button:hover {
    background-color: #dc2626;
}
QPushButton#stop_button:disabled {
    background-color: #fca5a5;
}
QPushButton#text_translate_btn {
    background-color: #2563eb;
    color: white;
    border: none;
    padding: 8px 32px;
    border-radius: 8px;
    font-size: 16px;
    font-weight: bold;
}
QPushButton#text_translate_btn:hover {
    background-color: #1d4ed8;
}
QPushButton#clear_input_btn, QPushButton#copy_output_btn, QPushButton#swap_back_btn {
    background-color: #e2e8f0;
    color: #1e293b;
    border: none;
    padding: 6px 12px;
    border-radius: 4px;
    font-size: 12px;
}
QPushButton#clear_input_btn:hover, QPushButton#copy_output_btn:hover, QPushButton#swap_back_btn:hover {
    background-color: #cbd5e1;
}
QDialog QLabel {
    color: #0f172a;
}
QDialog QLineEdit {
    color: #0f172a;
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 4px;
    padding: 4px 8px;
}
QDialog QComboBox {
    color: #0f172a;
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    padding: 4px 8px;
    border-radius: 4px;
}
QDialog QSpinBox {
    color: #0f172a;
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 4px;
    padding: 4px;
}
QDialog QCheckBox {
    color: #0f172a;
}
QDialog QPushButton {
    color: #ffffff;
    background-color: #2563eb;
    border: none;
    padding: 8px 20px;
    border-radius: 4px;
    font-weight: bold;
}
QDialog QTabBar::tab {
    color: #0f172a;
    background-color: #f1f5f9;
    padding: 6px 16px;
    border: 1px solid #e2e8f0;
    border-bottom: none;
}
QDialog QTabBar::tab:selected {
    background-color: #ffffff;
}
QGroupBox#feedback_group {
    color: #0f172a;
}"""

STYLESHEET_DARK = """QMainWindow {
    background-color: #0f172a;
    color: #e2e8f0;
}
QDialog {
    background-color: #1e293b;
    color: #e2e8f0;
}
QMessageBox {
    background-color: #1e293b;
    color: #e2e8f0;
}
QMessageBox QLabel {
    color: #e2e8f0;
}
QLabel {
    color: #e2e8f0;
}
QCheckBox {
    color: #e2e8f0;
}
QComboBox {
    color: #e2e8f0;
    background-color: #1e293b;
    border: 1px solid #334155;
    padding: 4px 8px;
    border-radius: 4px;
}
QComboBox QAbstractItemView {
    color: #e2e8f0;
    background-color: #1e293b;
    selection-background-color: #3b82f6;
    selection-color: #ffffff;
}
QTextEdit {
    color: #e2e8f0;
    background-color: #1e293b;
    border: 1px solid #334155;
    border-radius: 4px;
}
QProgressBar {
    color: #e2e8f0;
    border: 1px solid #334155;
    border-radius: 4px;
    text-align: center;
}
QProgressBar::chunk {
    background-color: #3b82f6;
    border-radius: 3px;
}
QListWidget {
    border: none;
    background: transparent;
    font-size: 14px;
    color: #e2e8f0;
}
QListWidget::item {
    padding: 10px 16px;
    border-radius: 6px;
    margin: 2px 0;
}
QListWidget::item:selected {
    background-color: #3b82f6;
    color: white;
}
QListWidget::item:hover:!selected {
    background-color: #1e293b;
}
QLabel#title {
    font-size: 22px;
    font-weight: bold;
    color: #f1f5f9;
    padding: 8px 0;
}
QLabel#help {
    font-size: 13px;
    color: #94a3b8;
    padding: 0 0 12px 0;
}
QPushButton {
    background-color: #3b82f6;
    color: white;
    border: none;
    padding: 10px 24px;
    border-radius: 6px;
    font-size: 14px;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #2563eb;
}
QPushButton:disabled {
    background-color: #1e3a5f;
    color: #64748b;
}
QPushButton#choose_button {
    background-color: #334155;
    color: #e2e8f0;
}
QPushButton#choose_button:hover {
    background-color: #475569;
}
QPushButton#settings_button {
    background-color: transparent;
    color: #64748b;
    font-size: 18px;
    padding: 6px;
}
QPushButton#settings_button:hover {
    color: #e2e8f0;
}
QPushButton#swap_button {
    background-color: transparent;
    color: #64748b;
    border: 1px solid #334155;
    padding: 4px 12px;
    font-size: 12px;
    min-width: 30px;
}
QPushButton#swap_button:hover {
    background-color: #334155;
}
QPushButton#theme_button {
    background-color: transparent;
    color: #e2e8f0;
    font-size: 18px;
    padding: 6px;
    border: none;
}
QPushButton#theme_button:hover {
    color: #ffffff;
}
QPushButton#save_word_btn {
    background-color: #22c55e;
    color: white;
    border: none;
    padding: 6px 12px;
    border-radius: 4px;
    font-size: 12px;
}
QPushButton#save_word_btn:hover {
    background-color: #16a34a;
}
QPushButton#save_word_btn {
    background-color: #16a34a;
    color: white;
    border: none;
    padding: 6px 12px;
    border-radius: 4px;
    font-size: 12px;
}
QPushButton#save_word_btn:hover {
    background-color: #15803d;
}
QPushButton#stop_button {
    background-color: #ef4444;
    color: white;
    border: none;
    padding: 10px 24px;
    border-radius: 6px;
    font-size: 14px;
    font-weight: bold;
}
QPushButton#stop_button:hover {
    background-color: #dc2626;
}
QPushButton#stop_button:disabled {
    background-color: #7f1d1d;
}
QPushButton#text_translate_btn {
    background-color: #3b82f6;
    color: white;
    border: none;
    padding: 8px 32px;
    border-radius: 8px;
    font-size: 16px;
    font-weight: bold;
}
QPushButton#text_translate_btn:hover {
    background-color: #2563eb;
}
QPushButton#clear_input_btn, QPushButton#copy_output_btn, QPushButton#swap_back_btn {
    background-color: #334155;
    color: #e2e8f0;
    border: none;
    padding: 6px 12px;
    border-radius: 4px;
    font-size: 12px;
}
QPushButton#clear_input_btn:hover, QPushButton#copy_output_btn:hover, QPushButton#swap_back_btn:hover {
    background-color: #475569;
}
QDialog QLabel {
    color: #e2e8f0;
}
QDialog QLineEdit {
    color: #e2e8f0;
    background-color: #1e293b;
    border: 1px solid #334155;
    border-radius: 4px;
    padding: 4px 8px;
}
QDialog QComboBox {
    color: #e2e8f0;
    background-color: #1e293b;
    border: 1px solid #334155;
    padding: 4px 8px;
    border-radius: 4px;
}
QDialog QSpinBox {
    color: #e2e8f0;
    background-color: #1e293b;
    border: 1px solid #334155;
    border-radius: 4px;
    padding: 4px;
}
QDialog QCheckBox {
    color: #e2e8f0;
}
QDialog QPushButton {
    color: #ffffff;
    background-color: #3b82f6;
    border: none;
    padding: 8px 20px;
    border-radius: 4px;
    font-weight: bold;
}
QDialog QTabBar::tab {
    color: #e2e8f0;
    background-color: #0f172a;
    padding: 6px 16px;
    border: 1px solid #334155;
    border-bottom: none;
}
QDialog QTabBar::tab:selected {
    background-color: #1e293b;
}
QGroupBox#feedback_group {
    color: #e2e8f0;
}"""


class TextTranslationWorker(QThread):
    finished = Signal(str)
    failed = Signal(str)
    progress = Signal(str)

    def __init__(self, text, source_lang, target_lang, engine, settings):
        super().__init__()
        self.text = text
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.engine = engine
        self.settings = settings

    def run(self):
        try:
            if self.engine == "custom":
                config = resolve_api_config(self.settings)
                if not config.api_key:
                    self.failed.emit("未配置 API Key，请在设置中填写")
                    return
                translator = DeepSeekTranslator(config)
            else:
                builder = _TRANSLATOR_BUILDERS.get(self.engine)
                if builder is None:
                    self.failed.emit(f"未知翻译引擎: {self.engine}")
                    return
                translator = builder(self.settings)

            result = translator.translate(self.text, self.target_lang, self.source_lang)
            self.finished.emit(result)
        except Exception as exc:
            traceback.print_exc()
            self.failed.emit(f"翻译失败：{exc}")


class Worker(QThread):
    finished_message = Signal(str)
    failed_message = Signal(str)
    progress_signal = Signal(str)

    def __init__(self, tool, paths, source_code, target_code, engine, settings, replace_spaces=True):
        super().__init__()
        self.tool = tool
        self.paths = paths
        self.source_code = source_code
        self.target_code = target_code
        self.engine = engine
        self.settings = settings
        self.replace_spaces = replace_spaces

    def run(self):
        try:
            outputs = self._process()
            if outputs is None:
                return
            results = [ProcessResult(source=src, output=out, status="成功", message="") for src, out in zip(self.paths, outputs)]
            report_dir = outputs[0].parent if outputs else Path.cwd()
            report_path = write_report(results, report_dir)
            count = len(outputs)
            msg = f"处理完成：{count} 个文件\n\n"
            msg += "\n".join(str(p) for p in outputs)
            msg += f"\n\n报告文件：{report_path}"
            self.finished_message.emit(msg)
        except ConfigError as exc:
            self.failed_message.emit(str(exc))
        except PdfTextError as exc:
            self.failed_message.emit(str(exc))
        except Exception as exc:
            traceback.print_exc()
            self.failed_message.emit(f"处理失败：{exc}")

    def _process(self):
        if self.engine == "custom":
            config = resolve_api_config(self.settings)
            if not config.api_key:
                self.progress_signal.emit("未配置 API Key，请在设置中填写")
                return None
            translator = DeepSeekTranslator(config)
        else:
            builder = _TRANSLATOR_BUILDERS.get(self.engine)
            if builder is None:
                raise ValueError(f"未知翻译引擎: {self.engine}")
            translator = builder(self.settings)

        source_language = language_prompt_name(self.source_code)
        target_language = language_prompt_name(self.target_code)
        suffix = language_suffix(self.target_code)
        total_files = len(self.paths)

        if self.tool.key == "organizer":
            source_dir = self.paths[0]
            out_dir = source_dir.parent / f"{source_dir.name}_organized"
            result_dir = organize_folder(source_dir, out_dir, replace_spaces=self.replace_spaces)
            return [result_dir]

        processor = _PROCESSOR_DISPATCH.get(self.tool.key)
        if processor is None:
            raise ValueError(f"未知工具类型: {self.tool.key}")

        outputs = []
        for i, path in enumerate(self.paths):
            self.progress_signal.emit(f"file:{i+1}/{total_files}|{path.name}")

            def make_callback(idx, path=path):
                def cb(current, total):
                    self.progress_signal.emit(
                        f"step:{current}/{total}|{idx+1}/{total_files}|{path.name}"
                    )
                return cb

            outputs.append(processor(
                path, translator, source_language, target_language, suffix, make_callback(i),
            ))
        return outputs


class MainWindow(QMainWindow):
    def __init__(self, app):
        super().__init__()
        self._app = app
        self.setWindowTitle("文件翻译工具箱")
        self.setMinimumSize(880, 660)
        self.settings = load_settings()
        self.paths: list[Path] = []
        self.worker: Worker | None = None
        self.text_worker: TextTranslationWorker | None = None
        self._current_theme = self.settings.theme
        self._build_ui()
        self._apply_theme()
        from file_toolbox.updater import check_for_update
        check_for_update(self, repo=self.settings.github_repo, silent=True)
        self.text_input.textChanged.connect(self._update_char_count)
        self.text_input_shortcut = QShortcut(QKeySequence("Ctrl+Return"), self)
        self.text_input_shortcut.activated.connect(self._trigger_text_translate)

    @staticmethod
    def _detect_system_theme() -> str:
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
            value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            winreg.CloseKey(key)
            return "light" if value == 1 else "dark"
        except Exception:
            return "light"

    def _resolve_theme(self) -> str:
        theme = self._current_theme
        if theme == "auto":
            return self._detect_system_theme()
        return theme

    def _apply_theme(self):
        resolved = self._resolve_theme()
        ss = STYLESHEET_DARK if resolved == "dark" else STYLESHEET_LIGHT
        self._app.setStyleSheet(ss)
        theme_icon = "☀" if resolved == "dark" else "☾"
        self.theme_button.setText(theme_icon)
        self.theme_button.setToolTip("切换主题模式（浅色 / 深色 / 自动）")

    def _toggle_theme(self):
        cycle = {"light": "dark", "dark": "auto", "auto": "light"}
        self._current_theme = cycle.get(self._current_theme, "light")
        self.settings.theme = self._current_theme
        from file_toolbox.settings import save_settings
        save_settings(self.settings)
        self._apply_theme()

    def _build_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(12)

        # Header row
        header = QHBoxLayout()
        self.title = QLabel("文件翻译工具箱")
        self.title.setObjectName("title")
        header.addWidget(self.title)
        header.addStretch()

        self.theme_button = QPushButton("☾")
        self.theme_button.setObjectName("theme_button")
        self.theme_button.setFixedSize(36, 36)
        self.theme_button.clicked.connect(self._toggle_theme)
        header.addWidget(self.theme_button)

        settings_btn = QPushButton("⚙")
        settings_btn.setObjectName("settings_button")
        settings_btn.setFixedSize(36, 36)
        settings_btn.clicked.connect(self._open_settings)
        header.addWidget(settings_btn)
        layout.addLayout(header)

        # Body
        body = QHBoxLayout()

        # Left: tool list
        self.tools = QListWidget()
        self.tools.setFixedWidth(160)
        for i, tool in enumerate(TOOLS):
            item = QListWidgetItem(tool.label)
            item.setData(999, tool.key)
            self.tools.addItem(item)
        self.tools.currentRowChanged.connect(self._tool_changed)
        body.addWidget(self.tools)

        # Right: content area
        content = QVBoxLayout()

        self.help = QLabel()
        self.help.setObjectName("help")
        self.help.setWordWrap(True)
        content.addWidget(self.help)

        # --- Translation controls (for word/excel/pdf/text) ---
        self.translation_panel = QWidget()
        tpanel = QVBoxLayout(self.translation_panel)
        tpanel.setContentsMargins(0, 0, 0, 0)

        # Engine row
        engine_row = QHBoxLayout()
        engine_row.addWidget(QLabel("翻译引擎:"))
        self.engine_combo = QComboBox()
        for code, label in ENGINES:
            self.engine_combo.addItem(label, code)
        self.engine_combo.currentIndexChanged.connect(self._engine_changed)
        engine_row.addWidget(self.engine_combo, 1)
        tpanel.addLayout(engine_row)

        # Language row
        lang_row = QHBoxLayout()
        lang_row.addWidget(QLabel("源语言:"))
        self.source_combo = QComboBox()
        for code, lang in LANGUAGES.items():
            self.source_combo.addItem(lang.label, code)
        lang_row.addWidget(self.source_combo, 1)

        self.swap_button = QPushButton("⇄")
        self.swap_button.setObjectName("swap_button")
        self.swap_button.setFixedWidth(36)
        self.swap_button.clicked.connect(self._swap_languages)
        lang_row.addWidget(self.swap_button)

        lang_row.addWidget(QLabel("目标语言:"))
        self.target_combo = QComboBox()
        for code, lang in LANGUAGES.items():
            self.target_combo.addItem(lang.label, code)
        self.target_combo.setCurrentIndex(1)
        lang_row.addWidget(self.target_combo, 1)
        tpanel.addLayout(lang_row)
        content.addWidget(self.translation_panel, 1)

        # --- Organizer options ---
        self.organizer_panel = QWidget()
        opanel = QVBoxLayout(self.organizer_panel)
        opanel.setContentsMargins(0, 0, 0, 0)
        self.replace_spaces_check = QCheckBox("替换空格为下划线")
        self.replace_spaces_check.setChecked(True)
        opanel.addWidget(self.replace_spaces_check)
        content.addWidget(self.organizer_panel)
        self.organizer_panel.setVisible(False)

        # --- File selection (for translate tools + organizer) ---
        self.file_section = QWidget()
        fpanel = QVBoxLayout(self.file_section)
        fpanel.setContentsMargins(0, 0, 0, 0)
        fpanel.addWidget(QLabel("已选择："))
        self.selected = QTextEdit()
        self.selected.setReadOnly(True)
        self.selected.setMinimumHeight(60)
        fpanel.addWidget(self.selected)

        action_row = QHBoxLayout()
        self.choose_button = QPushButton()
        self.choose_button.setObjectName("choose_button")
        self.choose_button.clicked.connect(self._choose)
        action_row.addWidget(self.choose_button)
        action_row.addStretch()
        fpanel.addLayout(action_row)

        start_row = QHBoxLayout()
        start_row.addStretch()
        self.start_button = QPushButton("开始处理")
        self.start_button.clicked.connect(self._start)
        start_row.addWidget(self.start_button)
        self.stop_button = QPushButton("停止")
        self.stop_button.setObjectName("stop_button")
        self.stop_button.setVisible(False)
        self.stop_button.clicked.connect(self._stop_processing)
        start_row.addWidget(self.stop_button)
        fpanel.addLayout(start_row)

        content.addWidget(self.file_section, 1)

        # --- Text translation panel ---
        self.text_panel = QWidget()
        txl = QVBoxLayout(self.text_panel)
        txl.setContentsMargins(0, 0, 0, 0)
        txl.setSpacing(6)

        # Input section
        input_header = QHBoxLayout()
        input_title = QLabel("原文")
        input_title.setStyleSheet("font-weight: bold; font-size: 13px; color: #475569;")
        input_header.addWidget(input_title)
        input_header.addStretch()
        self.char_count_label = QLabel("字数: 0")
        self.char_count_label.setStyleSheet("color: #94a3b8; font-size: 11px;")
        input_header.addWidget(self.char_count_label)
        txl.addLayout(input_header)

        self.text_input = QTextEdit()
        self.text_input.setPlaceholderText("在此输入或粘贴要翻译的文字...")
        self.text_input.setMinimumHeight(100)
        txl.addWidget(self.text_input, 1)

        self.clear_input_btn = QPushButton("清空原文")
        self.clear_input_btn.setObjectName("clear_input_btn")
        self.clear_input_btn.setFixedWidth(90)
        self.clear_input_btn.clicked.connect(self._clear_text_input)
        # Align right
        clear_row = QHBoxLayout()
        clear_row.addStretch()
        clear_row.addWidget(self.clear_input_btn)
        txl.addLayout(clear_row)

        # Translate button (centered, prominent)
        translate_center = QHBoxLayout()
        translate_center.addStretch()
        self.text_translate_btn = QPushButton("翻  译")
        self.text_translate_btn.setObjectName("text_translate_btn")
        self.text_translate_btn.setMinimumWidth(200)
        self.text_translate_btn.setMinimumHeight(42)
        self.text_translate_btn.clicked.connect(self._toggle_text_translate)
        translate_center.addWidget(self.text_translate_btn)
        translate_center.addStretch()
        txl.addLayout(translate_center)

        # Output section
        output_header = QHBoxLayout()
        output_title = QLabel("译文")
        output_title.setStyleSheet("font-weight: bold; font-size: 13px; color: #475569;")
        output_header.addWidget(output_title)
        output_header.addStretch()
        txl.addLayout(output_header)

        self.text_output = QTextEdit()
        self.text_output.setMinimumHeight(100)
        self.text_output.setPlaceholderText("翻译结果将显示在这里...")
        txl.addWidget(self.text_output, 1)

        # Output actions
        output_actions = QHBoxLayout()
        self.copy_output_btn = QPushButton("复制译文")
        self.copy_output_btn.setObjectName("copy_output_btn")
        self.copy_output_btn.setFixedWidth(100)
        self.copy_output_btn.clicked.connect(self._copy_text_output)
        output_actions.addWidget(self.copy_output_btn)
        self.save_word_btn = QPushButton("保存Word")
        self.save_word_btn.setObjectName("save_word_btn")
        self.save_word_btn.setFixedWidth(100)
        self.save_word_btn.clicked.connect(self._save_text_as_word)
        output_actions.addWidget(self.save_word_btn)
        output_actions.addStretch()
        self.swap_back_btn = QPushButton("↑↓ 互换翻译")
        self.swap_back_btn.setObjectName("swap_back_btn")
        self.swap_back_btn.setFixedWidth(120)
        self.swap_back_btn.clicked.connect(self._swap_text_back)
        output_actions.addWidget(self.swap_back_btn)
        txl.addLayout(output_actions)

        content.addWidget(self.text_panel)
        self.text_panel.setVisible(False)

        # --- Progress & status ---
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #64748b; font-size: 12px;")
        content.addWidget(self.status_label)

        self.progress = QProgressBar()
        self.progress.setFixedHeight(20)
        self.progress.setTextVisible(True)
        content.addWidget(self.progress)

        content.addStretch()
        body.addLayout(content, 1)
        layout.addLayout(body, 1)

        root = QWidget()
        root.setLayout(layout)
        self.setCentralWidget(root)
        self._tool_changed(0)

    def _open_settings(self):
        dialog = SettingsDialog(self.settings, self)
        if dialog.exec() == QDialog.Accepted:
            self.settings = dialog.settings
            if self.settings.theme != self._current_theme:
                self._current_theme = self.settings.theme
                self._apply_theme()
            logging.getLogger("file_toolbox").info("设置已更新")

    def _current_tool(self):
        row = self.tools.currentRow()
        return TOOLS[row if row >= 0 else 0]

    def _tool_changed(self, row):
        tool = TOOLS[row if row >= 0 else 0]
        self.title.setText(tool.label)
        self.help.setText(tool.help_text)

        is_translate = tool.uses_translation and not tool.uses_text_input
        is_organizer = tool.key == "organizer"
        is_text = tool.uses_text_input

        # Show/hide panels
        self.translation_panel.setVisible(is_translate or is_text)
        self.organizer_panel.setVisible(is_organizer)
        self.file_section.setVisible(is_translate or is_organizer)
        self.text_panel.setVisible(is_text)
        self.progress.setVisible(is_translate or is_organizer)

        if is_organizer:
            self.choose_button.setText("选择文件夹")
        elif is_translate:
            self.choose_button.setText("选择文件")
        elif is_text:
            self.choose_button.setText("")

        self.engine_combo.setEnabled(is_translate or is_text)
        self.source_combo.setEnabled(is_translate or is_text)
        self.target_combo.setEnabled(is_translate or is_text)
        self.swap_button.setEnabled(is_translate or is_text)

        if self.worker is not None and self.worker.isRunning():
            self.worker.stop()
            self.worker.quit()
            self.worker.wait(500)
            self.start_button.setVisible(True)
            self.stop_button.setVisible(False)
        if self.text_worker is not None and self.text_worker.isRunning():
            self.text_worker.stop()
            self.text_worker.terminate()
            self.text_worker.wait(500)
            self.text_translate_btn.setText("翻 译")
            self.text_translate_btn.setEnabled(True)
        self.paths = []
        self.selected.clear()
        self.status_label.setText("")
        self.progress.setRange(0, 100)
        self.progress.setValue(0)

    def _engine_changed(self, idx):
        code = self.engine_combo.itemData(idx)
        if code == "google" and not self.settings.google_vpn_warned:
            QMessageBox.information(
                self, "注意",
                "Google 翻译需要挂 VPN 才能使用。如果翻译失败，请检查网络连接。"
            )
            self.settings.google_vpn_warned = True
            from file_toolbox.settings import save_settings
            save_settings(self.settings)
        if code == "custom" and not self.settings.api_key:
            reply = QMessageBox.question(
                self, "需要 API Key",
                "使用自定义大模型需要先配置 API Key，是否前往设置？",
                QMessageBox.Yes | QMessageBox.No,
            )
            if reply == QMessageBox.Yes:
                self._open_settings()

    def _swap_languages(self):
        src_code = self.source_combo.currentData()
        if src_code == "auto":
            QMessageBox.information(self, "提示", "自动识别模式下不能交换，请先选择源语言。")
            return
        src_idx = self.source_combo.currentIndex()
        tgt_idx = self.target_combo.currentIndex()
        self.source_combo.setCurrentIndex(tgt_idx)
        self.target_combo.setCurrentIndex(src_idx)

    def _toggle_text_translate(self):
        """Toggle between translate and stop."""
        if self.text_translate_btn.text() == "停止":
            if self.text_worker is not None and self.text_worker.isRunning():
                self.text_worker.stop()
                self.text_worker.terminate()
                self.text_worker.wait(1000)
            self.text_translate_btn.setText("翻 译")
            self.text_translate_btn.setEnabled(True)
            self.status_label.setText("翻译已停止")
            return

        text = self.text_input.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "没有内容", "请先输入或粘贴要翻译的文字。")
            return

        self.text_translate_btn.setText("停止")
        self.text_output.clear()
        self.status_label.setText("正在翻译...")

        source_lang = language_prompt_name(self.source_combo.currentData())
        target_lang = language_prompt_name(self.target_combo.currentData())
        engine = self.engine_combo.currentData()

        self.text_worker = TextTranslationWorker(
            text, source_lang, target_lang, engine, self.settings
        )
        self.text_worker.finished.connect(self._on_text_translated)
        self.text_worker.failed.connect(self._on_text_failed)
        self.text_worker.progress.connect(self.status_label.setText)
        self.text_worker.start()

    def _on_text_translated(self, result):
        self.text_output.setText(result)
        self.text_translate_btn.setText("翻 译")
        self.text_translate_btn.setEnabled(True)
        self.status_label.setText("翻译完成")

    def _on_text_failed(self, message):
        self.text_translate_btn.setText("翻 译")
        self.text_translate_btn.setEnabled(True)
        self.status_label.setText("翻译失败")
        logging.getLogger("file_toolbox").error("%s", message)
        QMessageBox.critical(self, "出错了", message)

    def _trigger_text_translate(self):
        if self.text_panel.isVisible():
            self._toggle_text_translate()

    def _clear_text_input(self):
        self.text_input.clear()
        self.text_input.setFocus()

    def _save_text_as_word(self):
        text = self.text_output.toPlainText()
        if not text:
            QMessageBox.information(self, "提示", "译文为空，无法保存。")
            return
        save_path, _ = QFileDialog.getSaveFileName(
            self, "保存翻译结果", "", "Word 文档 (*.docx)"
        )
        if not save_path:
            return
        try:
            from docx import Document
            doc = Document()
            doc.add_paragraph(text)
            doc.save(save_path)
            self.status_label.setText(f"已保存到: {save_path}")
            QMessageBox.information(self, "保存完成", f"翻译结果已保存到：\n{save_path}")
        except Exception as e:
            QMessageBox.critical(self, "保存失败", f"保存 Word 失败：{e}")

    def _copy_text_output(self):
        text = self.text_output.toPlainText()
        if text:
            QApplication.clipboard().setText(text)
            self.status_label.setText("译文已复制")
        else:
            self.status_label.setText("译文为空，无法复制")

    def _swap_text_back(self):
        output_text = self.text_output.toPlainText().strip()
        if not output_text:
            QMessageBox.information(self, "提示", "请先翻译内容再互换。")
            return
        src_code = self.source_combo.currentData()
        if src_code == "auto":
            QMessageBox.information(self, "提示", "自动识别模式下不能交换，请先选择源语言。")
            return
        self.text_input.setText(output_text)
        src_idx = self.source_combo.currentIndex()
        tgt_idx = self.target_combo.currentIndex()
        self.source_combo.setCurrentIndex(tgt_idx)
        self.target_combo.setCurrentIndex(src_idx)
        self.text_output.clear()
        self.status_label.setText("已互换，可以翻译回去了")

    def _update_char_count(self):
        count = len(self.text_input.toPlainText())
        self.char_count_label.setText("字数: " + str(count))

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        paths = [Path(u.toLocalFile()) for u in event.mimeData().urls()]
        ext = paths[0].suffix.lower() if paths else ""
        tool_map = {"word": {".doc", ".docx"}, "excel": {".xlsx", ".xlsm"}, "pdf": {".pdf"}}
        matched_tool = None
        for tool_key, exts in tool_map.items():
            if ext in exts:
                matched_tool = tool_key
                break
        if matched_tool:
            for i in range(self.tools.count()):
                if self.tools.item(i).data(999) == matched_tool:
                    self.tools.setCurrentRow(i)
                    break
            tool = TOOLS[self.tools.currentRow()]
            exts2 = _tool_extensions(tool)
            dropped = [p for p in paths if p.suffix.lower() in exts2]
        else:
            tool = self._current_tool()
            exts2 = _tool_extensions(tool)
            dropped = [p for p in paths if exts2 is None or p.suffix.lower() in exts2]
        if not dropped:
            QMessageBox.warning(self, "不支持的文件", "拖放的文件中没有当前工具支持的格式。")
            return

        max_bytes = self.settings.max_file_size_mb * 1024 * 1024
        oversized = [p for p in dropped if p.stat().st_size > max_bytes]
        if oversized:
            names = "\n".join(f"{p.name} ({p.stat().st_size / 1024 / 1024:.0f} MB)" for p in oversized[:5])
            reply = QMessageBox.question(
                self, "文件过大",
                f"以下文件超过 {self.settings.max_file_size_mb} MB 限制，是否仍然继续？\n{names}",
                QMessageBox.Yes | QMessageBox.No,
            )
            if reply == QMessageBox.No:
                return

        self.paths = dropped
        lines = [f"[{i+1}] {p.name}" for i, p in enumerate(self.paths)]
        self.selected.setText("\n".join(lines))
        event.acceptProposedAction()

    def _choose(self):
        tool = self._current_tool()
        if tool.key == "organizer":
            folder = QFileDialog.getExistingDirectory(self, "选择要整理的文件夹")
            if folder:
                folder_path = Path(folder)
                self.paths = [folder_path]
                self.selected.setText(f"[1] {folder_path.name}\n  ({folder})")
            return
        files, _ = QFileDialog.getOpenFileNames(self, "选择文件", "", tool.file_filter or "所有文件(*.*)")
        self.paths = [Path(file) for file in files]
        lines = [f"[{i+1}] {p.name}" for i, p in enumerate(self.paths)]
        self.selected.setText("\n".join(lines))

    def _start(self):
        if not self.paths:
            QMessageBox.warning(self, "没有选择文件", "请先选择文件。")
            return

        max_bytes = self.settings.max_file_size_mb * 1024 * 1024
        oversized = [p for p in self.paths if p.stat().st_size > max_bytes]
        if oversized:
            names = "\n".join(f"{p.name} ({p.stat().st_size / 1024 / 1024:.0f} MB)" for p in oversized[:5])
            reply = QMessageBox.question(
                self, "文件过大",
                f"以下文件超过 {self.settings.max_file_size_mb} MB 限制，是否仍然继续？\n{names}",
                QMessageBox.Yes | QMessageBox.No,
            )
            if reply == QMessageBox.No:
                return

        self.start_button.setEnabled(False)
        self.stop_button.setVisible(True)
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setFormat("准备中...")
        self.status_label.setText("正在处理...")
        self.worker = Worker(
            self._current_tool(), self.paths,
            self.source_combo.currentData(), self.target_combo.currentData(),
            self.engine_combo.currentData(), self.settings,
            replace_spaces=self.replace_spaces_check.isChecked(),
        )
        self.worker.finished_message.connect(self._done)
        self.worker.failed_message.connect(self._failed)
        self.worker.progress_signal.connect(self._on_progress)
        self.worker.start()

    def _stop_processing(self):
        if self.worker is not None and self.worker.isRunning():
            self.worker.stop()
            self.worker.quit()
            self.worker.wait(1000)
            self.start_button.setEnabled(True)
            self.start_button.setVisible(True)
            self.stop_button.setVisible(False)
            self.status_label.setText("操作已停止")
            self.progress.setValue(0)
            self.progress.setFormat("")
        if self.text_worker is not None and self.text_worker.isRunning():
            self.text_worker.stop()
            self.text_worker.terminate()
            self.text_worker.wait(1000)
            self.text_translate_btn.setText("翻 译")
            self.text_translate_btn.setEnabled(True)
            self.status_label.setText("翻译已停止")

    def _on_progress(self, msg):
        if msg.startswith("step:"):
            parts = msg[5:].split("|")
            step_part = parts[0]
            file_part = parts[1] if len(parts) > 1 else "1/1"
            name_part = parts[2] if len(parts) > 2 else ""
            cur_step, total_step = step_part.split("/")
            cur_file, total_file = file_part.split("/")
            cur_step = int(cur_step)
            total_step = int(total_step)
            cur_file = int(cur_file)
            total_file = int(total_file)

            if total_step > 0 and total_file > 0:
                completed_files = cur_file - 1
                overall_total = total_step * total_file
                overall_done = completed_files * total_step + cur_step
                pct = int(overall_done * 100 / overall_total)
                self.progress.setRange(0, 100)
                self.progress.setValue(pct)
                self.progress.setFormat(f"{pct}% - {name_part}")
            self.status_label.setText(f"[{cur_file}/{total_file}] {name_part}")
        elif msg.startswith("file:"):
            self.status_label.setText(msg[5:])
        else:
            self.status_label.setText(msg)

    def _done(self, message):
        self.start_button.setEnabled(True)
        self.stop_button.setVisible(False)
        self.progress.setRange(0, 100)
        self.progress.setValue(100)
        self.progress.setFormat("100%")
        self.status_label.setText("处理完成")
        reply = QMessageBox.information(self, "完成", message + "\n\n是否打开输出文件夹?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes and self.paths:
            if self.settings.output_dir:
                output_dir = Path(self.settings.output_dir)
            elif self._current_tool().key == "organizer":
                output_dir = self.paths[0].parent / f"{self.paths[0].name}_organized"
            else:
                output_dir = self.paths[0].parent / "translated"
            if output_dir.exists():
                try:
                    subprocess.Popen(["explorer.exe", str(output_dir)])
                except Exception as e:
                    logging.getLogger("file_toolbox").warning("打开输出文件夹失败: %s", e)

    def _failed(self, message):
        self.start_button.setEnabled(True)
        self.stop_button.setVisible(False)
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setFormat("")
        self.status_label.setText("处理失败")
        logging.getLogger("file_toolbox").error("%s", message)
        QMessageBox.critical(self, "出错了", message)


def run_app():
    app = QApplication(sys.argv)
    # Load Chinese translation for Qt built-in menus (右键复制/粘贴等)
    from PySide6.QtCore import QTranslator
    import PySide6
    _qt_trans = QTranslator()
    _qm_path = Path(PySide6.__file__).parent / "translations" / "qt_zh_CN.qm"
    if _qm_path.exists():
        _qt_trans.load(str(_qm_path))
        app.installTranslator(_qt_trans)
    window = MainWindow(app)
    window.show()
    sys.exit(app.exec())



