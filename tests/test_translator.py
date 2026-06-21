from file_toolbox.translator import chunk_text, _map_google_code, _prompt_name_to_code
from conftest import FakeTranslator


def test_chunk_text_keeps_short_text_as_one_chunk():
    assert chunk_text("hello", max_chars=10) == ["hello"]


def test_chunk_text_splits_on_paragraph_boundaries():
    text = "one\n\ntwo\n\nthree"
    assert chunk_text(text, max_chars=8) == ["one\ntwo", "three"]


def test_fake_translator_marks_output():
    translator = FakeTranslator(prefix="[EN] ")
    assert translator.translate("hello") == "[EN] hello"


def test_chunk_text_splits_single_oversized_paragraph():
    chunks = chunk_text("abcdefghij", max_chars=4)
    assert chunks == ["abcd", "efgh", "ij"]


def test_code_map_helpers():
    assert _map_google_code("zh") == "zh-CN"
    assert _map_google_code("en") == "en"
    assert _map_google_code("auto") == "auto"
