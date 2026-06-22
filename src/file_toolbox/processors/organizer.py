from pathlib import Path
from shutil import move
from typing import Callable


TYPE_DIRS = {
    # Documents
    ".doc": "Word",
    ".docx": "Word",
    ".rtf": "Word",
    ".odt": "Word",
    ".xls": "Excel",
    ".xlsx": "Excel",
    ".xlsm": "Excel",
    ".csv": "Excel",
    ".ods": "Excel",
    ".pdf": "PDF",
    ".ppt": "PowerPoint",
    ".pptx": "PowerPoint",
    ".txt": "Text",
    ".md": "Text",
    ".json": "Data",
    ".xml": "Data",
    ".yaml": "Data",
    ".yml": "Data",
    ".toml": "Data",
    # Images
    ".jpg": "Images",
    ".jpeg": "Images",
    ".png": "Images",
    ".webp": "Images",
    ".gif": "Images",
    ".svg": "Images",
    ".bmp": "Images",
    ".ico": "Images",
    # Audio / Video
    ".mp3": "Audio",
    ".wav": "Audio",
    ".flac": "Audio",
    ".aac": "Audio",
    ".mp4": "Video",
    ".mkv": "Video",
    ".avi": "Video",
    ".mov": "Video",
    ".webm": "Video",
    # Archives
    ".zip": "Archives",
    ".rar": "Archives",
    ".7z": "Archives",
    ".tar": "Archives",
    ".gz": "Archives",
    # Code
    ".py": "Code",
    ".js": "Code",
    ".ts": "Code",
    ".html": "Code",
    ".css": "Code",
    ".java": "Code",
    ".cpp": "Code",
    ".c": "Code",
    ".h": "Code",
    ".rs": "Code",
    ".go": "Code",
    ".sh": "Code",
    ".bat": "Code",
    ".ps1": "Code",
}


def organize_folder(
    source_dir: Path,
    output_dir: Path,
    replace_spaces: bool = True,
    progress_callback: Callable[[int, int], None] | None = None,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    files = [f for f in source_dir.iterdir() if f.is_file()]
    total = len(files)
    for idx, source in enumerate(files, 1):
        category = TYPE_DIRS.get(source.suffix.lower(), "Other")
        target_dir = output_dir / category
        target_dir.mkdir(parents=True, exist_ok=True)
        name = source.name.replace(" ", "_") if replace_spaces else source.name
        try:
            move(str(source), str(target_dir / name))
        except Exception as _e:
            import logging
            logging.getLogger("file_toolbox").warning("移动文件失败 %s: %s", source.name, _e)
        if progress_callback:
            progress_callback(idx, total)
    return output_dir
