from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProcessResult:
    source: Path
    output: Path | None
    status: str
    message: str


def write_report(results: list[ProcessResult], output_dir: Path) -> Path:
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        report_path = output_dir / "处理报告.md"
        lines = ["# 处理报告", ""]
        for result in results:
            output = str(result.output) if result.output else "-"
            lines.append(f"- {result.status}: {result.source} -> {output} ({result.message})")
        report_path.write_text("\n".join(lines), encoding="utf-8")
        return report_path
    except:
        import logging
        logging.getLogger("file_toolbox").warning("写报告文件失败")
        return output_dir / "处理报告.md"
