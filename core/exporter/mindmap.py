"""
Mind map exporter — generates .mm (FreeMind) XML from the summary.
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from xml.dom import minidom

from .markdown import sanitize_filename


def export_mindmap(summary: dict, output_dir: str = "output") -> str:
    """
    Generate a FreeMind .mm file from the summary.
    Returns the file path.
    """
    output_path = Path(output_dir) / f"{sanitize_filename(summary.get('title', 'summary'))}.mm"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    root = ET.Element("map", version="1.0.1")

    title = summary.get("title", "Video Summary")
    center = ET.SubElement(root, "node", TEXT=title, POSITION="center")
    _add_rich_content(center, summary)

    rough = ET.tostring(root, encoding="unicode")
    dom = minidom.parseString(rough.encode())
    pretty = dom.toprettyxml(indent="  ")

    output_path.write_text(pretty, encoding="utf-8")
    return str(output_path)


def _add_rich_content(parent: ET.Element, summary: dict):
    """Add structured child nodes to the mind map."""

    if summary.get("summary"):
        summary_node = ET.SubElement(parent, "node", TEXT="概要")
        ET.SubElement(summary_node, "node", TEXT=summary["summary"][:200])

    if summary.get("key_points"):
        points_node = ET.SubElement(parent, "node", TEXT="要点")
        for point in summary["key_points"]:
            ET.SubElement(points_node, "node", TEXT=point[:150])

    if summary.get("segments"):
        segs_node = ET.SubElement(parent, "node", TEXT="分段摘要")
        for seg in summary["segments"]:
            start_ts = f"{int(seg.get('start',0)//60):02d}:{int(seg.get('start',0)%60):02d}"
            end_ts = f"{int(seg.get('end',0)//60):02d}:{int(seg.get('end',0)%60):02d}"
            label = f"[{start_ts}-{end_ts}] {seg.get('summary','')[:120]}"
            ET.SubElement(segs_node, "node", TEXT=label)

    if summary.get("key_quotes"):
        quotes_node = ET.SubElement(parent, "node", TEXT="关键引文")
        for q in summary["key_quotes"]:
            ts_str = f"{int(q.get('start',0)//60):02d}:{int(q.get('start',0)%60):02d}"
            text = f"[{ts_str}] {q['text'][:150]}"
            ET.SubElement(quotes_node, "node", TEXT=text)
