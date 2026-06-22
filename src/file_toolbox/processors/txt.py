from pathlib import Path
from typing import Callable

from file_toolbox.translator import Translator


def translate_txt_to_language(
    source: Path,
    output_dir: Path,
    translator: Translator,
    target_language: str = "English",
    source_language: str = "Auto-detect",
    target_suffix: str = "EN",
    progress_callback: Callable[[int, int], None] | None = None,
) -> Path:
    """\u7ffb\u8bd1 TXT \u6587\u4ef6\uff0c\u4fdd\u7559\u539f\u59cb\u683c\u5f0f\u3002"""
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / f"{source.stem}_{target_suffix}.txt"

    raw_text = source.read_text(encoding="utf-8", errors="replace")
    lines = raw_text.splitlines(keepends=True)
    total = len(lines)

    translated_lines = []
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if stripped:
            translated = translator.translate(stripped, target_language, source_language)
            # \u4fdd\u7559\u539f\u59cb\u6362\u884c\u7b26
            if line.endswith("\r\n"):
                translated_lines.append(translated + "\r\n")
            elif line.endswith("\n"):
                translated_lines.append(translated + "\n")
            else:
                translated_lines.append(translated)
        else:
            translated_lines.append(line)
        if progress_callback:
            progress_callback(idx + 1, total)

    output.write_text("".join(translated_lines), encoding="utf-8")
    return output
