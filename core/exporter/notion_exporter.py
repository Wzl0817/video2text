"""
Notion exporter — pushes the summary to a Notion page via the API.
"""

from pathlib import Path
from typing import Optional

from notion_client import Client

from app.config import settings


class NotionExporter:
    """Push video summaries to a Notion page."""

    def __init__(self, token: Optional[str] = None):
        self.token = token or settings.NOTION_TOKEN
        if not self.token:
            raise ValueError("Notion token is required. Set NOTION_TOKEN in .env")
        self.client = Client(auth=self.token)

    def export(self, summary: dict, page_id: Optional[str] = None) -> str:
        """
        Create a new Notion page with the video summary as child blocks.

        Args:
            summary: summary dict from TranscriptProcessor
            page_id: parent Notion page ID (default from settings)

        Returns:
            URL of the created Notion page
        """
        parent_id = page_id or settings.NOTION_PAGE_ID
        if not parent_id:
            raise ValueError("Notion page ID is required")

        title = summary.get("title", "Video Summary")
        page = self.client.pages.create(
            parent={"type": "page_id", "page_id": parent_id},
            properties={
                "title": {"title": [{"text": {"content": f"[video2text] {title}"}}]}
            },
        )
        new_page_id = page["id"]

        blocks = self._build_blocks(summary)

        for i in range(0, len(blocks), 100):
            batch = blocks[i:i + 100]
            self.client.blocks.children.append(
                block_id=new_page_id,
                children=batch,
            )

        url = f"https://notion.so/{new_page_id.replace('-', '')}"
        return url

    def _build_blocks(self, summary: dict) -> list:
        """Convert summary dict into Notion block objects."""
        blocks = []

        duration = summary.get("duration", 0)
        lang = summary.get("language", "")
        blocks.append({
            "type": "callout",
            "callout": {
                "rich_text": [{"type": "text", "text": {"content": f"时长: {int(duration//60)}分{int(duration%60)}秒  |  语言: {lang}"}}],
                "icon": {"emoji": "\U0001f3ac"},
                "color": "blue_background",
            }
        })

        if summary.get("summary"):
            blocks.append({"type": "heading_2", "heading_2": {"rich_text": [{"type": "text", "text": {"content": "概要"}}]}})
            blocks.append({
                "type": "paragraph",
                "paragraph": {"rich_text": [{"type": "text", "text": {"content": summary["summary"]}}]},
            })

        if summary.get("key_points"):
            blocks.append({"type": "heading_2", "heading_2": {"rich_text": [{"type": "text", "text": {"content": "要点"}}]}})
            for point in summary["key_points"]:
                blocks.append({
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {"rich_text": [{"type": "text", "text": {"content": point}}]},
                })

        if summary.get("segments"):
            blocks.append({"type": "heading_2", "heading_2": {"rich_text": [{"type": "text", "text": {"content": "分段摘要"}}]}})
            for seg in summary["segments"]:
                s = int(seg.get("start", 0))
                e = int(seg.get("end", 0))
                ts = f"{s//60:02d}:{s%60:02d} - {e//60:02d}:{e%60:02d}"
                blocks.append({
                    "type": "heading_3",
                    "heading_3": {"rich_text": [{"type": "text", "text": {"content": ts}}]},
                })
                blocks.append({
                    "type": "paragraph",
                    "paragraph": {"rich_text": [{"type": "text", "text": {"content": seg.get("summary", "")}}]},
                })

        if summary.get("key_quotes"):
            blocks.append({"type": "heading_2", "heading_2": {"rich_text": [{"type": "text", "text": {"content": "关键引文"}}]}})
            for q in summary["key_quotes"]:
                t = int(q.get("start", 0))
                ts = f"{t//60:02d}:{t%60:02d}"
                speaker = f" \u2014 {q['speaker']}" if q.get("speaker") else ""
                blocks.append({
                    "type": "quote",
                    "quote": {"rich_text": [{"type": "text", "text": {"content": f'"{q["text"]}" [{ts}]{speaker}'}}]},
                })

        return blocks
