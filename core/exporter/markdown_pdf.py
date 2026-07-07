"""
Markdown PDF exporter — converts Markdown content to PDF via weasyprint.
"""

from pathlib import Path

import markdown
from weasyprint import HTML

from .markdown import sanitize_filename


def export_markdown_pdf(summary: dict, output_dir: str = "output") -> str:
    """
    Render the markdown summary as a PDF file.
    Returns the file path.
    """
    output_path = Path(output_dir) / f"{sanitize_filename(summary.get('title', 'summary'))}.pdf"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    md_content = _build_markdown_text(summary)
    html_body = markdown.markdown(md_content, extensions=["extra"])

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
    @page {{ margin: 2cm; }}
    body {{ font-family: -apple-system, 'PingFang SC', 'Noto Sans SC', sans-serif; font-size: 12pt; line-height: 1.6; color: #1a1a1a; }}
    h1 {{ font-size: 22pt; margin-bottom: 0.3cm; color: #111; }}
    h2 {{ font-size: 16pt; margin-top: 0.8cm; color: #333; border-bottom: 1px solid #ddd; padding-bottom: 3px; }}
    h3 {{ font-size: 13pt; margin-top: 0.5cm; color: #444; }}
    blockquote {{ border-left: 4px solid #666; margin-left: 0; padding-left: 1em; color: #555; }}
    ul {{ padding-left: 1.5em; }}
</style>
</head>
<body>
{html_body}
</body>
</html>"""

    HTML(string=html).write_pdf(str(output_path))
    return str(output_path)


def _build_markdown_text(summary: dict) -> str:
    """Build markdown text from summary dict."""
    from .markdown import export_markdown
    import tempfile
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
        md_path = export_markdown(summary, output_dir=Path(f.name).parent)
        content = Path(md_path).read_text(encoding="utf-8")
    return content
