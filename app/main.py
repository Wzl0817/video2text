"""
video2text Web Application — FastAPI entry point.
"""

import json
import os
import shutil
import uuid
from pathlib import Path

from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import settings

app = FastAPI(title="video2text", version="0.1.0")

templates = Jinja2Templates(directory=str(settings.BASE_DIR / "app" / "templates"))
app.mount("/static", StaticFiles(directory=str(settings.BASE_DIR / "app" / "static")), name="static")

settings.OUTPUT_DIR.mkdir(exist_ok=True)
settings.UPLOADS_DIR.mkdir(exist_ok=True)

# In-memory task store (for light usage; replace with DB for production)
tasks: dict = {}


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/process")
async def process_video(
    request: Request,
    url: str = Form(""),
    file: UploadFile = File(None),
    output_modes: list[str] = Form([]),
    browser: str = Form(""),
):
    task_id = uuid.uuid4().hex[:12]

    if file and file.filename:
        file_path = settings.UPLOADS_DIR / f"{task_id}_{file.filename}"
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        source = str(file_path)
    elif url.strip():
        source = url.strip()
    else:
        return HTMLResponse("请提供视频 URL 或上传文件", status_code=400)

    tasks[task_id] = {
        "status": "queued",
        "progress": 0,
        "source": source,
        "output_modes": output_modes,
        "browser": browser,
        "result": None,
    }

    # Kick off async processing
    import asyncio
    asyncio.create_task(_run_pipeline(task_id, task["browser"]))

    return RedirectResponse(url=f"/result/{task_id}", status_code=303)


async def _run_pipeline(task_id: str, browser: str = ""):
    """Run the full processing pipeline in the background."""
    task = tasks[task_id]

    from core.parser import VideoParser
    from core.transcriber import Transcriber
    from core.processor import TranscriptProcessor

    try:
        task["status"] = "下载/解析视频..."
        task["progress"] = 10
        parser = VideoParser(
            output_dir=str(settings.OUTPUT_DIR),
            uploads_dir=str(settings.UPLOADS_DIR),
            browser=browser or settings.BROWSER or None,
        )
        video_info = parser.process(task["source"])
        task["progress"] = 30

        task["status"] = "正在转写语音..."
        task["progress"] = 35
        transcriber = Transcriber(model_size=settings.WHISPER_MODEL_SIZE)
        transcript = transcriber.transcribe(video_info["audio_path"])
        task["progress"] = 55

        task["status"] = "正在 AI 分析总结..."
        task["progress"] = 60
        processor = TranscriptProcessor()
        summary = processor.summarize(transcript, title=video_info["title"])
        task["progress"] = 75

        task["status"] = "正在生成输出文件..."
        task["progress"] = 80
        files = {}
        output_dir = str(settings.OUTPUT_DIR)

        if "md" in task["output_modes"]:
            from core.exporter.markdown import export_markdown
            files["markdown"] = export_markdown(summary, output_dir)

        if "md_pdf" in task["output_modes"]:
            from core.exporter.markdown_pdf import export_markdown_pdf
            files["markdown_pdf"] = export_markdown_pdf(summary, output_dir)

        if "mm" in task["output_modes"]:
            from core.exporter.mindmap import export_mindmap
            files["mindmap"] = export_mindmap(summary, output_dir)

        if "mm_pdf" in task["output_modes"]:
            from core.exporter.mindmap_pdf import export_mindmap_pdf
            files["mindmap_pdf"] = export_mindmap_pdf(summary, output_dir)

        if "notion" in task["output_modes"]:
            try:
                from core.exporter.notion_exporter import NotionExporter
                exporter = NotionExporter()
                notion_url = exporter.export(summary)
                files["notion_url"] = notion_url
            except ValueError as e:
                files["notion_error"] = str(e)

        if "video" in task["output_modes"]:
            files["video"] = video_info["path"]

        task["progress"] = 100
        task["status"] = "completed"
        task["result"] = {"summary": summary, "files": files}

    except Exception as e:
        task["status"] = "error"
        task["result"] = {"error": str(e)}


@app.get("/result/{task_id}", response_class=HTMLResponse)
async def result_page(request: Request, task_id: str):
    task = tasks.get(task_id)
    if not task:
        return HTMLResponse("任务不存在", status_code=404)

    return templates.TemplateResponse("result.html", {
        "request": request,
        "task_id": task_id,
        "status": task["status"],
        "progress": task.get("progress", 0),
        "result": task.get("result"),
    })


@app.get("/api/task/{task_id}")
async def get_task_status(task_id: str):
    task = tasks.get(task_id)
    if not task:
        return JSONResponse({"error": "任务不存在"}, status_code=404)
    return JSONResponse({
        "task_id": task_id,
        "status": task["status"],
        "progress": task.get("progress", 0),
        "result": task.get("result"),
    })


@app.get("/download/{filename:path}")
async def download_file(filename: str):
    file_path = settings.OUTPUT_DIR / filename
    if not file_path.exists():
        return JSONResponse({"error": "文件不存在"}, status_code=404)
    return FileResponse(str(file_path), filename=filename)
