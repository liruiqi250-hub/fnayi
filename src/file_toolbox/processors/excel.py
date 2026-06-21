from pathlib import Path
from typing import Callable

from openpyxl import load_workbook

from file_toolbox.translator import Translator


def translate_xlsx(
    source: Path,
    output_dir: Path,
    translator: Translator,
    columns: list[int] | None = None,
    progress_callback: Callable[[int, int], None] | None = None,
) -> Path:
    return translate_xlsx_to_language(
        source, output_dir, translator,
        columns=columns, progress_callback=progress_callback,
    )


def _count_translatable_cells(workbook, selected: set[int]) -> int:
    total = 0
    for sheet in workbook.worksheets:
        for row in sheet.iter_rows():
            for cell in row:
                if selected and cell.column not in selected:
                    continue
                if isinstance(cell.value, str) and cell.value.strip():
                    total += 1
    return total


def translate_xlsx_to_language(
    source: Path,
    output_dir: Path,
    translator: Translator,
    columns: list[int] | None = None,
    target_language: str = "English",
    source_language: str = "Auto-detect",
    target_suffix: str = "EN",
    progress_callback: Callable[[int, int], None] | None = None,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    suffix = source.suffix.lower()
    workbook = load_workbook(source, keep_vba=True)
    output = output_dir / f"{source.stem}_{target_suffix}{suffix}"

    selected = set(columns or [])
    total = _count_translatable_cells(workbook, selected) if progress_callback else 0

    # Translation cache: avoid re-translating the same cell text
    translation_cache: dict[str, str] = {}

    done = 0
    for sheet in workbook.worksheets:
        for row in sheet.iter_rows():
            for cell in row:
                if selected and cell.column not in selected:
                    continue
                if isinstance(cell.value, str) and cell.value.strip():
                    original = cell.value.strip()
                    if original not in translation_cache:
                        translation_cache[original] = translator.translate(
                            original, target_language, source_language
                        )
                    cell.value = translation_cache[original]
                    done += 1
                    if progress_callback:
                        progress_callback(done, total)

    try:
        workbook.save(output)
    finally:
        workbook.close()
    return output
