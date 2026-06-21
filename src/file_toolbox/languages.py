from dataclasses import dataclass


@dataclass(frozen=True)
class LanguageOption:
    code: str
    label: str
    prompt_name: str
    suffix: str


LANGUAGES = {
    "auto": LanguageOption("auto", "自动识别", "Auto-detect", "AUTO"),
    "zh": LanguageOption("zh", "中文", "Chinese", "ZH"),
    "en": LanguageOption("en", "英文", "English", "EN"),
    "es": LanguageOption("es", "西班牙语", "Spanish", "ES"),
    "pt": LanguageOption("pt", "葡萄牙语", "Portuguese", "PT"),
    "fr": LanguageOption("fr", "法语", "French", "FR"),
    "de": LanguageOption("de", "德语", "German", "DE"),
    "ja": LanguageOption("ja", "日语", "Japanese", "JA"),
    "ko": LanguageOption("ko", "韩语", "Korean", "KO"),
    "ru": LanguageOption("ru", "俄语", "Russian", "RU"),
}


def get_language(code: str) -> LanguageOption:
    try:
        return LANGUAGES[code]
    except KeyError:
        raise ValueError(f"Unsupported language code: {code}")


def language_prompt_name(code: str) -> str:
    return LANGUAGES[code].prompt_name


def language_suffix(code: str) -> str:
    return LANGUAGES[code].suffix
