"""
Parser module — download videos from URLs and extract audio.
Supports: YouTube, Bilibili, Douyin, local files.
"""

import os
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

import yt_dlp


class VideoParser:
    """Handles video downloading and audio extraction."""

    SUPPORTED_PLATFORMS = {"youtube", "bilibili", "douyin"}

    def __init__(self, output_dir: str = "output", uploads_dir: str = "uploads"):
        self.output_dir = Path(output_dir)
        self.uploads_dir = Path(uploads_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.uploads_dir.mkdir(parents=True, exist_ok=True)

    def detect_source_type(self, source: str) -> str:
        """Detect whether source is a URL or local file."""
        if os.path.isfile(source):
            return "local"
        source_lower = source.lower()
        if "youtube.com" in source_lower or "youtu.be" in source_lower:
            return "youtube"
        if "bilibili.com" in source_lower or "b23.tv" in source_lower:
            return "bilibili"
        if "douyin.com" in source_lower:
            return "douyin"
        return "unknown"

    def download_video(self, url: str, output_template: str = "%(title)s.%(ext)s") -> dict:
        """
        Download video from a URL using yt-dlp.
        Returns dict with path, title, and metadata.
        """
        output_path = self.output_dir / output_template

        ydl_opts = {
            "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "outtmpl": str(output_path),
            "quiet": True,
            "no_warnings": True,
            "extract_flat": False,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            video_path = ydl.prepare_filename(info)
            # Ensure correct extension
            ext = info.get("ext", "mp4")
            video_path = str(output_path).replace("%(title)s.%(ext)s", f"{info['title']}.{ext}")

        return {
            "path": video_path,
            "title": info.get("title", "untitled"),
            "duration": info.get("duration", 0),
            "source_url": url,
        }

    def extract_audio(self, video_path: str, audio_format: str = "wav") -> str:
        """
        Extract audio from a video file using ffmpeg.
        Returns path to the extracted audio file.
        """
        video = Path(video_path)
        audio_path = self.output_dir / f"{video.stem}.{audio_format}"

        cmd = [
            "ffmpeg", "-i", str(video),
            "-vn",                          # No video
            "-acodec", "pcm_s16le" if audio_format == "wav" else "libmp3lame",
            "-ar", "16000",                 # 16kHz for Whisper
            "-ac", "1",                     # Mono
            "-y",                           # Overwrite
            str(audio_path),
        ]

        subprocess.run(cmd, capture_output=True, check=True)
        return str(audio_path)

    def process_local_file(self, file_path: str) -> dict:
        """
        Handle a local video file upload.
        Copies it to a working directory and returns info.
        """
        src = Path(file_path)
        dest = self.uploads_dir / src.name
        if src.resolve() != dest.resolve():
            import shutil
            shutil.copy2(str(src), str(dest))
        return {
            "path": str(dest),
            "title": src.stem,
            "duration": 0,  # Will be detected later
            "source_url": "",
        }

    def process(self, source: str) -> dict:
        """
        Unified entry point.
        - source: URL string or local file path
        Returns dict with video info and audio_path.
        """
        source_type = self.detect_source_type(source)

        if source_type == "local":
            video_info = self.process_local_file(source)
        elif source_type in self.SUPPORTED_PLATFORMS | {"unknown"}:
            video_info = self.download_video(source)
        else:
            raise ValueError(f"Unsupported source: {source}")

        # Extract audio
        audio_path = self.extract_audio(video_info["path"])
        video_info["audio_path"] = audio_path
        video_info["source_type"] = source_type

        return video_info
