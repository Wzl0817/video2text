"""
Markdown exporter — renders structured summary as a .md file.
"""

from pathlib import Path


def export_markdown(summary: dict, output_dir: str = "output") -> str:
    """
    Generate a Markdown file from the summary dict.
    Returns the file path.
    """
    output_path = Path(output_dir) / f"{sanitize_filename(summary.get('title', 'summary'))}.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    lines = []

    title = summary.get("title", "Video Summary")
    lines.append(f"# {title}\n")

    duration = summary.get("duration", 0)
    mins = int(duration // 60)
    secs = int(duration % 60)
    lang = summary.get("language", "")
    lines.append(f"> 时长: {mins}分{secs}秒  |  语言: {lang}\n")

    if summary.get("summary"):
        lines.append("## 概要\n")
        lines.append(summary["summary"] + "\n")

    if summary.get("key_points"):
        lines.append("## 要点\n")
        for point in summary["key_points"]:
            lines.append(f"- {point}")
        lines.append("")

    if summary.get("segments"):
        lines.append("## 分段摘要\n")
        for seg in summary["segments"]:
            start = seg.get("start", 0)
            end = seg.get("end", 0)
            start_ts = f"{int(start//60):02d}:{int(start%60):02d}"
            end_ts = f"{int(end//60):02d}:{int(end%60):02d}"
            lines.append(f"### [{start_ts} - {end_ts}]")
            lines.append(seg.get("summary", "") + "\n")

    if summary.get("key_quotes"):
        lines.append("## 关键引文\n")
        for q in summary["key_quotes"]:
            ts = q.get("start", 0)
            ts_str = f"{int(ts//60):02d}:{int(ts%60):02d}"
            speaker = f" — {q['speaker']}" if q.get("speaker") else ""
            lines.append(f"> \"{q['text']}\"")
            lines.append(f"> _[{ts_str}]{speaker}_\n")

    content = "\n".join(lines)
    output_path.write_text(content, encoding="utf-8")
    return str(output_path)


def sanitize_filename(name: str) -> str:
    """Remove or replace characters unsafe for filenames."""
    import re
    name = re.sub(r'[<>:"/\\|?*]', "_", name)
    return name[:200] or "summary"
