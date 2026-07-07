"""
Transcriber module — convert audio to text with timestamps using faster-whisper.
"""

from pathlib import Path
from typing import Optional

from faster_whisper import WhisperModel


class Transcriber:
    """Speech-to-text transcription using faster-whisper."""

    def __init__(self, model_size: str = "base", device: str = "auto"):
        """
        Args:
            model_size: tiny, base, small, medium, large-v3
            device: auto, cpu, cuda
        """
        self.model_size = model_size
        compute_type = "int8" if device == "cpu" else "float16"
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)

    def transcribe(self, audio_path: str, language: Optional[str] = None) -> dict:
        """
        Transcribe an audio file.

        Args:
            audio_path: path to audio file (wav/mp3)
            language: optional language code (e.g. "zh", "en")

        Returns:
            dict with:
              - "segments": list of {start, end, text}
              - "language": detected language
              - "duration": total audio duration
              - "full_text": concatenated plain text
        """
        segments_gen, info = self.model.transcribe(
            audio_path,
            language=language,
            beam_size=5,
            vad_filter=True,
        )

        segments = []
        for seg in segments_gen:
            segments.append({
                "start": round(seg.start, 2),
                "end": round(seg.end, 2),
                "text": seg.text.strip(),
            })

        full_text = " ".join(s["text"] for s in segments)

        return {
            "segments": segments,
            "language": info.language,
            "duration": round(info.duration, 2),
            "full_text": full_text,
        }

    def format_srt(self, segments: list) -> str:
        """Convert segments to SRT subtitle format."""
        lines = []
        for i, seg in enumerate(segments, 1):
            start = self._format_timestamp(seg["start"])
            end = self._format_timestamp(seg["end"])
            lines.append(f"{i}\n{start} --> {end}\n{seg['text']}\n")
        return "\n".join(lines)

    @staticmethod
    def _format_timestamp(seconds: float) -> str:
        """Convert seconds to SRT timestamp format: HH:MM:SS,mmm."""
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        ms = int((seconds - int(seconds)) * 1000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
