import json
import logging
import urllib.request
import urllib.error
import webbrowser

from PySide6.QtWidgets import QMessageBox

from file_toolbox import __version__


def _parse_version(version_str: str) -> tuple:
    try:
        parts = version_str.strip().lstrip("vV").split(".")
        return tuple(int(p) for p in parts[:3])
    except (ValueError, IndexError):
        return (0, 0, 0)


def check_for_update(parent_widget=None, repo: str = "", silent: bool = False) -> None:
    """Check GitHub Releases for updates.
    silent=True: only log errors, no dialogs at all.
    """
    if not repo:
        if not silent:
            QMessageBox.information(
                parent_widget, "检查更新",
                "请先在 设置 → 通用设置 中填写 GitHub 仓库名。\n格式：用户名/仓库名"
            )
        return

    logger = logging.getLogger("file_toolbox")
    api_url = f"https://api.github.com/repos/{repo}/releases/latest"

    try:
        req = urllib.request.Request(
            api_url,
            headers={
                "User-Agent": "FileTranslator/" + __version__,
                "Accept": "application/json",
            },
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        latest_tag = data.get("tag_name", "").lstrip("vV")
        download_url = data.get("html_url", "")
        body = data.get("body", "")

        if not latest_tag:
            return

        latest_parsed = _parse_version(latest_tag)
        current_parsed = _parse_version(__version__)

        if latest_parsed > current_parsed:
            notes = body[:500] + "..." if len(body) > 500 else body
            msg = (
                f"发现新版本 v{latest_tag}\n\n"
                f"当前版本：v{__version__}\n"
                f"最新版本：v{latest_tag}\n\n"
                f"更新内容：\n{notes}\n\n"
                f"是否前往下载？"
            )
            reply = QMessageBox.question(
                parent_widget, "发现新版本", msg,
                QMessageBox.Yes | QMessageBox.No,
            )
            if reply == QMessageBox.Yes and download_url:
                webbrowser.open(download_url)
        else:
            if not silent:
                QMessageBox.information(
                    parent_widget, "检查更新", f"当前已是最新版本（v{__version__}）。"
                )

    except urllib.error.HTTPError as e:
        logger.warning("Update check HTTP error: %s", e)
        if not silent:
            msg = "检查更新失败" + (
                "：仓库不存在或没有 Release" if e.code == 404 else f"：HTTP {e.code}"
            )
            QMessageBox.warning(parent_widget, "检查更新", msg + "\n请检查仓库名设置。")
    except Exception as e:
        logger.warning("Update check failed: %s", e)
        if not silent:
            QMessageBox.warning(parent_widget, "检查更新", f"检查更新失败：{e}\n请检查网络连接。")


def fetch_release_notes(repo: str) -> str:
    """Fetch the latest release body text. Returns empty string on failure."""
    try:
        req = urllib.request.Request(
            f"https://api.github.com/repos/{repo}/releases/latest",
            headers={"User-Agent": "FileTranslator", "Accept": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data.get("body", "")
    except Exception:
        return ""
