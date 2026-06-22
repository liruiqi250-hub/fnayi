import logging
import sys
import ctypes
from pathlib import Path

from file_toolbox.settings import LOG_FILE
from file_toolbox.gui import run_app


# Windows DPI \u81ea\u9002\u5e94\uff08\u8001\u8bbe\u5907\u6e05\u6670\u5ea6\u4f18\u5316\uff09
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

# \u68c0\u67e5\u7cfb\u7edf\u7248\u672c\uff0cWin7 \u53ca\u4ee5\u4e0b\u663e\u793a\u63d0\u793a
try:
    ver = sys.getwindowsversion()
    if ver.major < 6 or (ver.major == 6 and ver.minor < 1):
        from PySide6.QtWidgets import QMessageBox
        import sys as _sys
        _app = __import__('PySide6.QtWidgets', fromlist=['QApplication']).QApplication(_sys.argv)
        QMessageBox.critical(None, "\u7cfb\u7edf\u4e0d\u652f\u6301",
            "\u60a8\u7684\u64cd\u4f5c\u7cfb\u7edf\u7248\u672c\u592a\u65e7\uff0c\u8bf7\u81f3\u5c11\u4f7f\u7528 Windows 7 SP1\u3002\n\n"
            "\u5982\u679c\u662f Windows 7\uff0c\u8bf7\u5b89\u88c5 KB2999226 \u66f4\u65b0\u540e\u518d\u8fd0\u884c\u3002")
        _sys.exit(1)
except Exception:
    pass


def main():
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
            logging.StreamHandler(sys.stderr),
        ],
    )
    logging.getLogger("file_toolbox").info("Application started")
    run_app()


if __name__ == "__main__":
    main()

