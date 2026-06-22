import time
from typing import Protocol

from openai import OpenAI

from file_toolbox.config import AppConfig
from file_toolbox.languages import LANGUAGES


class Translator(Protocol):
    def translate(
        self,
        text: str,
        target_language: str = "English",
        source_language: str = "Auto-detect",
    ) -> str:
        ...


def chunk_text(text: str, max_chars: int = 3500) -> list[str]:
    paragraphs = [part.strip() for part in text.split("\n\n") if part.strip()]
    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        if len(paragraph) > max_chars:
            if current:
                chunks.append(current)
                current = ""
            chunks.extend(
                paragraph[start : start + max_chars]
                for start in range(0, len(paragraph), max_chars)
            )
            continue
        candidate = paragraph if not current else f"{current}\n{paragraph}"
        if len(candidate) <= max_chars:
            current = candidate
        else:
            if current:
                chunks.append(current)
            current = paragraph
    if current:
        chunks.append(current)
    return chunks


def _prompt_name_to_code(prompt_name: str) -> str:
    for lang in LANGUAGES.values():
        if lang.prompt_name == prompt_name:
            return lang.code
    return "auto"


def _map_google_code(code: str) -> str:
    _CODE_MAP = {"zh": "zh-CN", "auto": "auto"}
    return _CODE_MAP.get(code, code)


def _map_mymemory_code(code: str) -> str:
    _MAP = {"zh": "zh-CN", "en": "en-GB", "ja": "ja-JP", "ko": "ko-KR",
            "fr": "fr-FR", "de": "de-DE", "es": "es-ES", "it": "it-IT",
            "pt": "pt-PT", "ru": "ru-RU", "ar": "ar-SA", "auto": "en-GB"}
    return _MAP.get(code, code)


def _retry_translate(translator_fn, text: str, max_attempts: int = 3, delay: float = 1.5) -> str:
    last_error = None
    for attempt in range(max_attempts):
        try:
            return translator_fn(text)
        except Exception as e:
            last_error = e
            if attempt < max_attempts - 1:
                time.sleep(delay * (attempt + 1))
    raise RuntimeError(str(last_error)) from last_error


class _NullTranslator:
    """\u5f53\u7ffb\u8bd1\u5f15\u64ce\u4e0d\u652f\u6301\u8be5\u8bed\u8a00\u5bf9\u65f6\uff0c\u76f4\u63a5\u8fd4\u56de\u539f\u6587\u3002"""
    def translate(self, text: str) -> str:
        return text


class _BaseFreeTranslator:
    """Base class for free web translators with automatic chunking and retry."""
    max_chars: int = 4000

    def _make_translator(self, source: str, target: str):
        raise NotImplementedError

    def translate(
        self,
        text: str,
        target_language: str = "English",
        source_language: str = "Auto-detect",
    ) -> str:
        if not text.strip():
            return text
        source_code = _prompt_name_to_code(source_language)
        target_code = _prompt_name_to_code(target_language)
        translator = self._make_translator(source_code, target_code)

        def _do_translate(t: str) -> str:
            if len(t) > self.max_chars:
                parts = [translator.translate(chunk) for chunk in chunk_text(t, max_chars=self.max_chars)]
                return "\n\n".join(parts)
            return translator.translate(t)

        return _retry_translate(_do_translate, text, max_attempts=3, delay=1.5)


class GoogleFreeTranslator(_BaseFreeTranslator):
    """Free translation via Google Translate. No API key needed."""

    def _make_translator(self, source_code: str, target_code: str):
        from deep_translator import GoogleTranslator
        return GoogleTranslator(
            source=_map_google_code(source_code),
            target=_map_google_code(target_code),
        )


def _detect_language_code(text: str) -> str:
    """简单的语言检测，用于 MyMemory 不支持 auto 时的后备方案。"""
    import re
    # 检查是否有 CJK 统一表意文字（中日韩越）
    cjk_chars = len(re.findall(r'[\u4e00-\u9fff\u3400-\u4dbf]', text))
    # 检查是否有日文假名
    jp_chars = len(re.findall(r'[\u3040-\u309f\u30a0-\u30ff]', text))
    # 检查是否有韩文
    ko_chars = len(re.findall(r'[\uac00-\ud7af]', text))
    # 检查是否有俄文
    ru_chars = len(re.findall(r'[\u0400-\u04ff]', text))
    # 检查是否有阿拉伯文
    ar_chars = len(re.findall(r'[\u0600-\u06ff]', text))

    total = len(text.strip())
    if total == 0:
        return "en-GB"
    
    ratio_cjk = cjk_chars / total
    ratio_jp = jp_chars / total
    ratio_ko = ko_chars / total
    ratio_ru = ru_chars / total
    ratio_ar = ar_chars / total

    if ratio_ko > 0.3:
        return "ko-KR"
    if ratio_jp > 0.2:
        return "ja-JP"
    if ratio_cjk > 0.3:
        return "zh-CN"
    if ratio_ru > 0.3:
        return "ru-RU"
    if ratio_ar > 0.3:
        return "ar-SA"
    # 默认英文
    return "en-GB"

class MyMemoryFreeTranslator(_BaseFreeTranslator):
    """Free translation via MyMemory. No API key needed.
    
    直接使用 HTTP API 调用，绕过 deep_translator 的编码问题。
    """

    def __init__(self):
        import requests as _req
        self._session = _req.Session()
        self._session.headers.update({"User-Agent": "FileTranslator/1.0"})

    def _make_translator(self, source_code: str, target_code: str):
        # MyMemory API 不支持 "auto"，所以当源语言为 auto 时默认用 en-GB
        src = _map_mymemory_code(source_code) if source_code != "auto" else "en-GB"
        tgt = _map_mymemory_code(target_code)
        return _MyMemoryDirectApi(self._session, src, tgt)

    def translate(
        self,
        text: str,
        target_language: str = "English",
        source_language: str = "Auto-detect",
    ) -> str:
        if not text.strip():
            return text
        source_code = _prompt_name_to_code(source_language)
        target_code = _prompt_name_to_code(target_language)

        # MyMemory 不支持 auto 检测，手动检测源语言
        if source_code == "auto":
            source_code = _detect_language_code(text)

        # 如果检测出的源语言和目标语言相同，直接返回原文
        my_src = _map_mymemory_code(source_code) if source_code != "auto" else "en-GB"
        my_tgt = _map_mymemory_code(target_code)
        if my_src == my_tgt:
            return text

        translator = _MyMemoryDirectApi(self._session, my_src, my_tgt)

        def _do_translate(t: str) -> str:
            if len(t) > self.max_chars:
                parts = [translator.translate(chunk) for chunk in chunk_text(t, max_chars=self.max_chars)]
                return "\n\n".join(parts)
            return translator.translate(t)

        return _retry_translate(_do_translate, text, max_attempts=3, delay=1.5)


class _MyMemoryDirectApi:
    """MyMemory API 直接 HTTP 调用，正确处理 Unicode 编码。"""

    def __init__(self, session, source: str, target: str):
        self._session = session
        self._source = source
        self._target = target

    def translate(self, text: str) -> str:
        if not text.strip():
            return text
        url = "https://api.mymemory.translated.net/get"
        params = {"q": text, "langpair": f"{self._source}|{self._target}"}
        try:
            import requests as _req
            resp = self._session.get(url, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            status = int(data.get("responseStatus", 0))
            if status != 200:
                details = data.get("responseDetails", "")
                if "DISTINCT LANGUAGES" in details:
                    # 源语言和目标语言相同，直接返回原文
                    return text
                raise RuntimeError(f"MyMemory API 错误: {details}")
            translated = data.get("responseData", {}).get("translatedText", "")
            if not translated:
                return text  # 空结果返回原文
            return translated
        except _req.exceptions.RequestException as e:
            raise RuntimeError(f"MyMemory 请求失败: {e}")


class DeepSeekTranslator:
    def __init__(self, config: AppConfig):
        self._config = config
        self._client = OpenAI(api_key=config.api_key, base_url=config.base_url)
        self._max_chars = 3500
        self._max_attempts = 3
        self._delay = 1.5

    def translate(
        self,
        text: str,
        target_language: str = "English",
        source_language: str = "Auto-detect",
    ) -> str:
        if not text.strip():
            return text

        source_instruction = (
            "Detect the source language automatically."
            if source_language == "Auto-detect"
            else f"The source language is {source_language}."
        )

        def _do_translate(t: str) -> str:
            """Translate a single chunk (or full text if short enough)."""
            response = self._client.chat.completions.create(
                model=self._config.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            f"{source_instruction} "
                            f"Translate the user text into clear professional {target_language}. "
                            "Preserve names, numbers, product codes, and formatting markers."
                        ),
                    },
                    {"role": "user", "content": t},
                ],
                temperature=0.2,
            )
            return response.choices[0].message.content or ""

        if len(text) > self._max_chars:
            chunks = chunk_text(text, max_chars=self._max_chars)
            translated_chunks = []
            for chunk in chunks:
                result = _retry_translate(_do_translate, chunk, self._max_attempts, self._delay)
                translated_chunks.append(result)
            return "\n\n".join(translated_chunks)

        return _retry_translate(_do_translate, text, self._max_attempts, self._delay)


