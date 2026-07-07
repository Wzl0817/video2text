"""
Processor module — uses DeepSeek (OpenAI-compatible API) to summarize transcripts.
Generates: key points, segment summaries, key quotes.
"""

import json
import re
from typing import Optional

from openai import OpenAI

from app.config import settings


class TranscriptProcessor:
    """Summarize video transcripts using DeepSeek AI."""

    def __init__(self):
        self.client = OpenAI(
            api_key=settings.DEEPSEEK_API_KEY,
            base_url=settings.DEEPSEEK_API_BASE,
        )
        self.model = settings.DEEPSEEK_MODEL

    def summarize(self, transcript: dict, title: str = "") -> dict:
        """
        Analyze a transcript and produce structured summary.

        Args:
            transcript: output from Transcriber.transcribe()
            title: optional video title

        Returns:
            dict with:
              - "title": video title
              - "summary": short overall summary
              - "key_points": list of bullet-point takeaways
              - "segments": list of {start, end, summary}
              - "key_quotes": list of notable quotes with timestamps
        """
        segments_text = self._format_segments_for_prompt(transcript["segments"])

        prompt = f"""你是一个视频内容分析助手。请分析以下视频转录文本，输出结构化总结。

视频标题：{title or "未命名"}
视频时长：{transcript.get('duration', 0)}秒
检测语言：{transcript.get('language', 'unknown')}

请按以下 JSON 格式输出（只输出 JSON，不要其他内容）：

{{
    "summary": "用2-3句话概括整个视频的核心内容",
    "key_points": ["要点1", "要点2", ...],
    "segments": [
        {{"start": 开始时间(秒), "end": 结束时间(秒), "summary": "该段内容摘要"}}
    ],
    "key_quotes": [
        {{"text": "引文内容", "start": 时间戳(秒), "speaker": "说话人(如果有)或null"}}
    ]
}}

转录文本：
{segments_text}
"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=4096,
        )

        content = response.choices[0].message.content.strip()

        # Extract JSON from markdown code block if present
        json_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", content, re.DOTALL)
        if json_match:
            content = json_match.group(1).strip()

        try:
            result = json.loads(content)
        except json.JSONDecodeError:
            result = {
                "summary": content,
                "key_points": [],
                "segments": [],
                "key_quotes": [],
            }

        result["title"] = title or transcript.get("title", "")
        result["language"] = transcript.get("language", "")
        result["duration"] = transcript.get("duration", 0)

        return result

    def _format_segments_for_prompt(self, segments: list) -> str:
        """Format transcript segments for the AI prompt."""
        lines = []
        for seg in segments:
            start_min = int(seg["start"] // 60)
            start_sec = int(seg["start"] % 60)
            timestamp = f"[{start_min:02d}:{start_sec:02d}]"
            lines.append(f"{timestamp} {seg['text']}")
        return "\n".join(lines)
