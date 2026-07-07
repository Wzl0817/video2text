"""
Parser module.
"""

import os
import subprocess
from pathlib import Path
from typing import Optional
import yt_dlp


class VideoParser:
    """Handles video downloading and audio extraction."""

    SUPPORTED_PLATFORMS = {"youtube", "bilibili", "douyin"}

    def __init__(self, output_dir="output", uploads_dir="uploads", browser=None):
        self.output_dir = Path(output_dir)
        self.uploads_dir = Path(uploads_dir)
        self.browser = browser
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.uploads_dir.mkdir(parents=True, exist_ok=True)

    def detect_source_type(self, source):
        if os.path.isfile(source):
            return "local"
        s = source.lower()
        if "youtube.com" in s or "youtu.be" in s:
            return "youtube"
        if "bilibili.com" in s or "b23.tv" in s:
            return "bilibili"
        if "douyin.com" in s:
            return "douyin"
        return "unknown"

    def _build_ydl_opts(self, output_template, source_type):
        opts = {
            "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "outtmpl": str(self.output_dir / output_template),
            "quiet": True,
            "no_warnings": True,
            "extract_flat": False,
            "extractor_retries": 3,
            "retries": 5,
            "fragment_retries": 5,
            "ignore_no_formats_error": True,
        }
        if self.browser:
            opts["cookiesfrombrowser"] = (self.browser,)
        if source_type == "bilibili":
            opts["extractor_args"] = {"bilibili": {"prefer_hd": ["True"]}}
        elif source_type == "douyin":
            opts["extractor_args"] = {"douyin": {"use_api": ["web" if self.browser else "mobile"]}}
            opts["format"] = "best"
        elif source_type == "youtube":
            opts["extractor_args"] = {"youtube": {"skip": ["webpage"]}}
        return opts

    def download_video(self, url, output_template="%(title)s.%(ext)s"):
        st = self.detect_source_type(url)
        ydl_opts = self._build_ydl_opts(output_template, st)
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            ext = info.get("ext", "mp4")
            base = Path(ydl.prepare_filename(info)).stem
            vp = str(self.output_dir / f"{base}.{ext}")
            return {"path": vp, "title": info.get("title", "untitled"),
                    "duration": info.get("duration", 0),
                    "source_url": url, "source_type": st}

    def extract_audio(self, video_path, audio_format="wav"):
        video = Path(video_path)
        audio = self.output_dir / f"{video.stem}.{audio_format}"
        subprocess.run(["ffmpeg", "-i", str(video), "-vn",
            "-acodec", "pcm_s16le" if audio_format == "wav" else "libmp3lame",
            "-ar", "16000", "-ac", "1", "-y", str(audio)], capture_output=True, check=True)
        return str(audio)

    def process_local_file(self, file_path):
        import shutil
        src = Path(file_path)
        dest = self.uploads_dir / src.name
        if src.resolve() != dest.resolve():
            shutil.copy2(str(src), str(dest))
        return {"path": str(dest), "title": src.stem, "duration": 0,
                "source_url": "", "source_type": "local"}

    def process(self, source):
        st = self.detect_source_type(source)
        vi = self.process_local_file(source) if st == "local" else self.download_video(source)
        vi["audio_path"] = self.extract_audio(vi["path"])
        return vi
