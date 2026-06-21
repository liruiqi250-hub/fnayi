from dataclasses import dataclass


@dataclass
class FakeTranslator:
    prefix: str = "[EN] "

    def translate(
        self,
        text: str,
        target_language: str = "English",
        source_language: str = "Auto-detect",
    ) -> str:
        return f"{self.prefix}{text}"
