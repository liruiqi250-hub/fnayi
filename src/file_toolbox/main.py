import logging
import sys
from pathlib import Path

from file_toolbox.settings import LOG_FILE
from file_toolbox.gui import run_app


def main():
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
