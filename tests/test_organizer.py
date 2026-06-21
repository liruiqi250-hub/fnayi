from pathlib import Path

from file_toolbox.processors.organizer import organize_folder


def test_organize_folder_moves_files_and_deletes_sources(tmp_path: Path):
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    docx = source_dir / "产品 说明.docx"
    image = source_dir / "图片 1.jpg"
    docx.write_text("doc", encoding="utf-8")
    image.write_text("img", encoding="utf-8")

    output_dir = organize_folder(source_dir, tmp_path / "organized", replace_spaces=True)

    # Files should be moved (not copied) from source
    assert not docx.exists()
    assert not image.exists()
    assert (output_dir / "Word" / "产品_说明.docx").exists()
    assert (output_dir / "Images" / "图片_1.jpg").exists()


def test_organize_folder_handles_empty_directory(tmp_path):
    source_dir = tmp_path / "empty"
    source_dir.mkdir()
    output_dir = organize_folder(source_dir, tmp_path / "organized")
    assert output_dir.exists()
    assert not any(output_dir.iterdir())


def test_organize_folder_moves_unknown_extension_to_other(tmp_path):
    source_dir = tmp_path / "mixed"
    source_dir.mkdir()
    weird = source_dir / "data.xyz"
    weird.write_text("unknown")
    normal = source_dir / "readme.abc"
    normal.write_text("text")

    output_dir = organize_folder(source_dir, tmp_path / "organized", replace_spaces=False)

    assert (output_dir / "Other" / "data.xyz").exists()
    assert (output_dir / "Other" / "readme.abc").exists()
    # Source files should be gone (moved)
    assert not weird.exists()
    assert not normal.exists()


def test_organize_folder_moves_known_types_to_correct_categories(tmp_path):
    source_dir = tmp_path / "typed"
    source_dir.mkdir()
    (source_dir / "script.py").write_text("x")
    (source_dir / "archive.zip").write_text("x")
    (source_dir / "audio.mp3").write_text("x")
    (source_dir / "readme.txt").write_text("x")

    output_dir = organize_folder(source_dir, tmp_path / "out", replace_spaces=False)

    assert (output_dir / "Code" / "script.py").exists()
    assert (output_dir / "Archives" / "archive.zip").exists()
    assert (output_dir / "Audio" / "audio.mp3").exists()
    assert (output_dir / "Text" / "readme.txt").exists()


def test_organize_folder_preserves_spaces_when_disabled(tmp_path):
    source_dir = tmp_path / "src"
    source_dir.mkdir()
    f = source_dir / "my file.docx"
    f.write_bytes(b"")

    output_dir = organize_folder(source_dir, tmp_path / "out", replace_spaces=False)

    assert (output_dir / "Word" / "my file.docx").exists()
