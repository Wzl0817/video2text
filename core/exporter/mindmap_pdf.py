"""
Mind map PDF exporter — renders summary as a styled PDF with mind-map layout.
"""

from pathlib import Path

from weasyprint import HTML

from .markdown import sanitize_filename


def export_mindmap_pdf(summary: dict, output_dir: str = "output") -> str:
    """
    Render a mind-map-style visual PDF of the summary.
    Returns the file path.
    """
    output_path = Path(output_dir) / f"{sanitize_filename(summary.get('title', 'summary'))}_mindmap.pdf"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    html = _build_mindmap_html(summary)
    HTML(string=html).write_pdf(str(output_path))
    return str(output_path)


def _build_mindmap_html(summary: dict) -> str:
    """Build an HTML document that looks like a mind map for PDF rendering."""
    title = summary.get("title", "Video Summary")

    tree_html = f'<div class="center-node">{_escape(title)}</div>'
    tree_html += '<div class="branches">'

    if summary.get("summary"):
        tree_html += f"""
        <div class="branch">
            <div class="branch-label">概要</div>
            <div class="branch-content">{_escape(summary['summary'][:300])}</div>
        </div>"""

    if summary.get("key_points"):
        pts = "".join(f'<li>{_escape(p[:200])}</li>' for p in summary["key_points"])
        tree_html += f"""
        <div class="branch">
            <div class="branch-label">要点</div>
            <ul class="branch-content">{pts}</ul>
        </div>"""

    if summary.get("segments"):
        segs = ""
        for seg in summary["segments"]:
            s = int(seg.get("start", 0))
            e = int(seg.get("end", 0))
            ts = f"{s//60:02d}:{s%60:02d}-{e//60:02d}:{e%60:02d}"
            segs += f'<li><strong>[{ts}]</strong> {_escape(seg.get("summary","")[:200])}</li>'
        tree_html += f"""
        <div class="branch">
            <div class="branch-label">分段摘要</div>
            <ul class="branch-content">{segs}</ul>
        </div>"""

    if summary.get("key_quotes"):
        quotes = ""
        for q in summary["key_quotes"]:
            t = int(q.get("start", 0))
            ts = f"{t//60:02d}:{t%60:02d}"
            quotes += f'<li class="quote">[{ts}] "{_escape(q.get("text","")[:200])}"</li>'
        tree_html += f"""
        <div class="branch">
            <div class="branch-label">关键引文</div>
            <ul class="branch-content">{quotes}</ul>
        </div>"""

    tree_html += "</div>"

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
    @page {{ margin: 1.5cm; size: landscape; }}
    body {{ font-family: -apple-system, 'PingFang SC', 'Noto Sans SC', sans-serif; font-size: 11pt; color: #1a1a1a; }}
    .center-node {{ background: #2563eb; color: white; font-size: 16pt; font-weight: bold; padding: 12px 20px; border-radius: 8px; text-align: center; margin-bottom: 20px; }}
    .branches {{ display: flex; flex-wrap: wrap; gap: 12px; }}
    .branch {{ flex: 1 1 45%; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px; page-break-inside: avoid; }}
    .branch-label {{ font-weight: bold; font-size: 12pt; color: #2563eb; margin-bottom: 6px; border-bottom: 2px solid #2563eb; padding-bottom: 4px; }}
    .branch-content {{ margin: 0; padding-left: 16px; }}
    .quote {{ list-style: none; font-style: italic; color: #475569; margin-bottom: 4px; }}
    li {{ margin-bottom: 4px; }}
</style>
</head>
<body>
{tree_html}
</body>
</html>"""


def _escape(text: str) -> str:
    """Escape HTML entities."""
    import html
    return html.escape(text, quote=False)
