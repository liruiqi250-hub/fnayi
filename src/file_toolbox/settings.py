import json
import os
import logging
from dataclasses import dataclass, asdict
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from file_toolbox.config import AppConfig, ConfigError, load_config


SETTINGS_DIR = Path(os.environ.get("APPDATA", Path.home() / ".config")) / "FileTranslator"
SETTINGS_FILE = SETTINGS_DIR / "settings.json"
LOG_FILE = SETTINGS_DIR / "toolbox.log"
SETTINGS_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class AppSettings:
    api_key: str = ""
    base_url: str = "https://api.deepseek.com"
    model: str = "deepseek-v4-pro"
    output_dir: str = ""
    open_output_after_done: bool = True
    max_file_size_mb: int = 200
    theme: str = "auto"
    google_vpn_warned: bool = False
    github_repo: str = "liruiqi250-hub/fnayi"


def _ensure_settings_dir():
    SETTINGS_DIR.mkdir(parents=True, exist_ok=True)


def load_settings() -> AppSettings:
    if not SETTINGS_FILE.exists():
        return AppSettings()
    try:
        data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        return AppSettings(**{k: data.get(k, v) for k, v in AppSettings().__dict__.items()})
    except (json.JSONDecodeError, TypeError):
        return AppSettings()


def save_settings(settings: AppSettings) -> None:
    _ensure_settings_dir()
    SETTINGS_FILE.write_text(
        json.dumps(asdict(settings), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def resolve_api_config(settings: AppSettings) -> AppConfig:
    """Resolve API configuration with priority: settings JSON > .env > defaults."""
    if settings.api_key.strip():
        return AppConfig(
            api_key=settings.api_key.strip(),
            base_url=settings.base_url.strip() or "https://api.deepseek.com",
            model=settings.model.strip() or "deepseek-v4-pro",
        )
    try:
        return load_config()
    except ConfigError as exc:
        logging.getLogger("file_toolbox").warning(
            "No API key in settings or .env, falling back: %s", exc
        )
        return AppConfig(api_key="", base_url="https://api.deepseek.com", model="deepseek-v4-pro")


class SettingsDialog(QDialog):
    def __init__(self, settings: AppSettings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.setMinimumWidth(480)
        self._settings = settings
        self._build_ui()

    def _build_ui(self):
        tabs = QTabWidget()

        # ---------- 通用设置 ----------
        general = QWidget()
        form = QFormLayout(general)
        form.setLabelAlignment(Qt.AlignRight)

        self._output_dir_input = QLineEdit(self._settings.output_dir)
        self._output_dir_input.setPlaceholderText("留空则输出到文件同目录下的 translated 文件夹")
        browse_btn = QPushButton("浏览...")
        browse_btn.clicked.connect(self._browse_output)
        row = QHBoxLayout()
        row.addWidget(self._output_dir_input, 1)
        row.addWidget(browse_btn)
        form.addRow("输出目录", row)

        self._open_check = QCheckBox("处理完成后打开输出文件夹")
        self._open_check.setChecked(self._settings.open_output_after_done)
        form.addRow("", self._open_check)

        self._max_size_input = QSpinBox()
        self._max_size_input.setRange(10, 2000)
        self._max_size_input.setValue(self._settings.max_file_size_mb)
        self._max_size_input.setSuffix(" MB")
        form.addRow("最大文件大小", self._max_size_input)

        self._theme_combo = QComboBox()
        self._theme_combo.addItem("自动", "auto")
        self._theme_combo.addItem("浅色", "light")
        self._theme_combo.addItem("深色", "dark")
        idx = self._theme_combo.findData(self._settings.theme)
        if idx >= 0:
            self._theme_combo.setCurrentIndex(idx)
        form.addRow("显示主题", self._theme_combo)

        self._repo_input = QLineEdit(self._settings.github_repo)
        self._repo_input.setPlaceholderText("例如：你的用户名/文件翻译工具箱")
        form.addRow("GitHub 仓库", self._repo_input)

        tabs.addTab(general, "通用设置")

        # ---------- API 设置 ----------
        api = QWidget()
        api_form = QFormLayout(api)
        api_form.setLabelAlignment(Qt.AlignRight)

        self._api_key_input = QLineEdit(self._settings.api_key)
        self._api_key_input.setEchoMode(QLineEdit.Password)
        self._api_key_input.setPlaceholderText("输入 API Key")
        api_form.addRow("API Key", self._api_key_input)

        self._base_url_input = QLineEdit(self._settings.base_url)
        self._base_url_input.setPlaceholderText("https://api.deepseek.com")
        api_form.addRow("Base URL", self._base_url_input)

        self._model_input = QLineEdit(self._settings.model)
        self._model_input.setPlaceholderText("deepseek-v4-pro")
        api_form.addRow("模型名称", self._model_input)

        tabs.addTab(api, "API 设置")

        # ---------- 其他 ----------
        other = QWidget()
        other_layout = QVBoxLayout(other)
        _ensure_settings_dir()

        log_group = QGroupBox("日志")
        log_inner = QVBoxLayout(log_group)
        log_label = QLabel("日志文件记录了每次操作的详细信息和错误。")
        log_label.setWordWrap(True)
        download_log_btn = QPushButton("下载日志")
        download_log_btn.clicked.connect(self._download_log)
        log_inner.addWidget(log_label)
        log_inner.addWidget(download_log_btn)
        other_layout.addWidget(log_group)

        update_group = QGroupBox("软件更新")
        update_inner = QVBoxLayout(update_group)
        update_label = QLabel("检查是否有新版本可用。")
        update_label.setWordWrap(True)
        check_update_btn = QPushButton("检查更新")
        check_update_btn.clicked.connect(self._check_update)
        update_inner.addWidget(update_label)
        update_inner.addWidget(check_update_btn)
        other_layout.addWidget(update_group)

        feedback_group = QGroupBox("意见反馈")
        feedback_inner = QVBoxLayout(feedback_group)
        feedback_label = QLabel("扫码添加微信，直接反馈问题或建议。")
        feedback_label.setWordWrap(True)
        feedback_label.setAlignment(Qt.AlignCenter)
        feedback_inner.addWidget(feedback_label)
        qr_path = Path(__file__).resolve().parent / "wechat_qr.jpg"
        if qr_path.exists():
            pixmap = QPixmap(str(qr_path))
            qr_label = QLabel()
            qr_label.setPixmap(pixmap.scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            qr_label.setAlignment(Qt.AlignCenter)
            feedback_inner.addWidget(qr_label)
        else:
            fallback = QLabel("二维码图片未找到，请直接联系开发者。")
            fallback.setWordWrap(True)
            fallback.setAlignment(Qt.AlignCenter)
            feedback_inner.addWidget(fallback)
        other_layout.addWidget(feedback_group)

        other_layout.addStretch()
        tabs.addTab(other, "其他")

        save_btn = QPushButton("保存")
        save_btn.clicked.connect(self._save)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_row.addWidget(save_btn)
        btn_row.addWidget(cancel_btn)

        root = QVBoxLayout(self)
        root.addWidget(tabs)
        root.addLayout(btn_row)

    def _browse_output(self):
        folder = QFileDialog.getExistingDirectory(self, "选择默认输出目录")
        if folder:
            self._output_dir_input.setText(folder)

    def _check_update(self):
        from file_toolbox.updater import check_for_update
        check_for_update(self, repo=self._settings.github_repo, silent=False)

    def _download_log(self):
        if not LOG_FILE.exists():
            QMessageBox.information(self, "提示", "日志文件不存在，请先执行一次操作。")
            return
        save_path, _ = QFileDialog.getSaveFileName(
            self, "保存日志文件", str(Path.home() / "Desktop" / "toolbox.log"),
            "日志文件 (*.log);;所有文件 (*.*)",
        )
        if save_path:
            try:
                Path(save_path).write_bytes(LOG_FILE.read_bytes())
                QMessageBox.information(self, "完成", f"日志已保存到：\n{save_path}")
            except Exception as e:
                QMessageBox.warning(self, "错误", f"保存日志失败：{e}")

    def _save(self):
        self._settings.output_dir = self._output_dir_input.text().strip()
        self._settings.open_output_after_done = self._open_check.isChecked()
        self._settings.max_file_size_mb = self._max_size_input.value()
        self._settings.theme = self._theme_combo.currentData()
        self._settings.github_repo = self._repo_input.text().strip()
        self._settings.api_key = self._api_key_input.text().strip()
        self._settings.base_url = self._base_url_input.text().strip()
        self._settings.model = self._model_input.text().strip()
        save_settings(self._settings)
        self.accept()

    @property
    def settings(self) -> AppSettings:
        return self._settings
