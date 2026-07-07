# Video2Text

Video to text transcription tool — extract audio from video files and transcribe them to text.

## Overview
Fetch videos from URLs (YouTube, Bilibili, Douyin/TikTok) or upload local files, transcribe speech to text with timestamps, summarize with AI (DeepSeek), and export in your choice of formats:
- Markdown (.md)
- Markdown PDF
- Mind map (.mm)
- Mind map PDF
- Notion page
- Raw video download

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure your API keys
cp .env.example .env
# Edit .env with your DeepSeek API key and Notion token

# 3. Run the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 4. Open http://localhost:8000
```

## Project Structure

```
video2text/
├── app/           # Web UI (FastAPI + Jinja2 + HTMX)
│   ├── main.py
│   ├── config.py
│   ├── templates/
│   └── static/
├── core/          # Core engine
│   ├── parser.py          # Download + audio extraction
│   ├── transcriber.py     # Whisper transcription
│   ├── processor.py       # AI summarization
│   └── exporter/          # Output renderers
│       ├── markdown.py
│       ├── markdown_pdf.py
│       ├── mindmap.py
│       ├── mindmap_pdf.py
│       └── notion_exporter.py
├── output/        # Generated files
├── uploads/       # Temporary uploads
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

## Tech Stack
- **Parser:** yt-dlp, ffmpeg
- **Transcriber:** faster-whisper
- **Summarizer:** DeepSeek API (OpenAI-compatible)
- **Web:** FastAPI, Jinja2, HTMX, Tailwind CSS
- **Deployment:** Docker

## Supported Sources
- Local video files
- YouTube
- Bilibili
- Douyin (TikTok China)
