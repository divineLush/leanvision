# api.py
# FastAPI wrapper для запуска обработки и отдачи результатов (Swagger UI готов).

from fastapi import FastAPI, UploadFile, File, HTTPException, WebSocket
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uuid
import os
import shutil
from concurrent.futures import ThreadPoolExecutor
import time
import asyncio
import json
import ast

# импортируем вашу логику
from main import process_video
from config import OUTPUT_DIR, MODEL_PATH
from utils import ensure_dir

app = FastAPI(title="LeanVision Video Shift Analysis", version="0.1.0",
              description="API для запуска анализа видео смен и получения клипов/событий (Swagger UI автоматически).")

# CORS: укажите адреса фронтенда (добавляйте свои origin)
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET","POST","PUT","DELETE","OPTIONS"],
    allow_headers=["*"],
)

# директории
UPLOAD_DIR = "uploads"
ensure_dir(UPLOAD_DIR)
ensure_dir(OUTPUT_DIR)

# in-memory storage задач
tasks: Dict[str, Dict[str, Any]] = {}
executor = ThreadPoolExecutor(max_workers=2)

# Pydantic модели
class StartProcessRequest(BaseModel):
    video_filename: Optional[str] = None   # имя файла в uploads
    video_id: Optional[str] = None         # альтернатива
    video_path: Optional[str] = None       # полный путь (danger: используйте осторожно)
    conf: Optional[float] = None
    every: Optional[int] = None
    merge_sec: Optional[int] = None
    finalize_delay: Optional[float] = None
    save_immediately: Optional[bool] = False
    workers: Optional[int] = None
    webhook: Optional[str] = None

class ProcessStatus(BaseModel):
    task_id: str
    status: str
    started_at: Optional[float] = None
    finished_at: Optional[float] = None
    out_dir: Optional[str] = None
    message: Optional[str] = None

class EventResponse(BaseModel):
    id: int
    class_names: List[str]
    confs: List[float]
    time_s: float
    frame_idx: int
    clip_path: Optional[str]
    saved: bool

# helper runner
def _run_processing(task_id: str, video_path: str, out_dir: str, params: dict):
    tasks[task_id]["status"] = "running"
    tasks[task_id]["started_at"] = time.time()
    try:
        # Вызов основной функции обработки (блокирующий). Она уже безопасно обрабатывает None.
        process_video(
            model_path=params.get("model_path", MODEL_PATH),
            video_path=video_path,
            out_dir=out_dir,
            conf_thresh=params.get("conf", None),
            detect_every_n=params.get("every", None),
            merge_sec=params.get("merge_sec", None),
            finalize_delay=params.get("finalize_delay", None),
            save_immediately=params.get("save_immediately", False),
            workers=params.get("workers", None),
            webhook=params.get("webhook", None)
        )
        tasks[task_id]["status"] = "done"
        tasks[task_id]["finished_at"] = time.time()
        tasks[task_id]["message"] = "processed"
    except Exception as e:
        tasks[task_id]["status"] = "error"
        tasks[task_id]["finished_at"] = time.time()
        tasks[task_id]["message"] = str(e)

@app.post("/videos/upload", response_model=Dict[str, str], tags=["videos"])
async def upload_video(file: UploadFile = File(...)):
    file_id = str(uuid.uuid4())
    filename = f"{file_id}_{file.filename}"
    dest = os.path.join(UPLOAD_DIR, filename)
    try:
        with open(dest, "wb") as f:
            content = await file.read()
            f.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"cannot save file: {e}")
    return {"video_id": filename, "path": dest}

@app.post("/process/start", response_model=ProcessStatus, tags=["process"])
def start_process(req: StartProcessRequest):
    # Определяем путь к видео (принимаем video_filename, video_id или video_path)
    video_path = None
    if req.video_path:
        video_path = req.video_path
    elif req.video_filename:
        video_path = os.path.join(UPLOAD_DIR, req.video_filename)
    elif req.video_id:
        video_path = os.path.join(UPLOAD_DIR, req.video_id)

    if not video_path or not os.path.exists(video_path):
        raise HTTPException(status_code=400, detail="specify existing video_filename/video_id or provide valid video_path")

    task_id = str(uuid.uuid4())
    out_dir = os.path.join(OUTPUT_DIR, f"task_{task_id}")
    ensure_dir(out_dir)

    tasks[task_id] = {
        "task_id": task_id,
        "status": "queued",
        "video": video_path,
        "out_dir": out_dir,
        "params": req.model_dump(),
        "started_at": None,
        "finished_at": None,
        "message": None
    }

    # запускаем в пуле (не блокируем FastAPI)
    executor.submit(_run_processing, task_id, video_path, out_dir, tasks[task_id]["params"])

    return ProcessStatus(task_id=task_id, status="queued", out_dir=out_dir)

@app.get("/process/{task_id}", response_model=ProcessStatus, tags=["process"])
def get_process_status(task_id: str):
    task = tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="task not found")
    return ProcessStatus(
        task_id=task_id,
        status=task["status"],
        started_at=task["started_at"],
        finished_at=task["finished_at"],
        out_dir=task["out_dir"],
        message=task["message"]
    )

@app.get("/process/{task_id}/clips", tags=["process"])
def list_clips_for_task(task_id: str):
    task = tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="task not found")
    out_dir = task["out_dir"]
    clips = []
    if os.path.exists(out_dir):
        for root, _, files in os.walk(out_dir):
            for name in files:
                if name.endswith('.mp4'):
                    clip_path = os.path.join(root, name)
                    rel = os.path.relpath(clip_path, OUTPUT_DIR).replace(os.path.sep, '/')
                    clips.append({
                        "name": name,
                        "clip_url": f"/static/{rel}",
                        "thumbnail_url": None
                    })
    return clips

@app.get("/events", response_model=List[EventResponse], tags=["events"])
def list_events(limit: int = 50):
    rows = []
    for sub in os.listdir(OUTPUT_DIR):
        candidate = os.path.join(OUTPUT_DIR, sub, "violations_events.csv")
        if os.path.exists(candidate):
            import pandas as pd
            try:
                df = pd.read_csv(candidate)
                for _, r in df.iterrows():
                    # Парсим поля class_names/confs которые могли быть сохранены как питоновские/JSON-строки
                    try:
                        class_names = json.loads(r.get("class_names")) if isinstance(r.get("class_names"), str) else r.get("class_names")
                    except Exception:
                        try:
                            class_names = ast.literal_eval(r.get("class_names"))
                        except Exception:
                            class_names = [r.get("class_names")]
                    try:
                        confs = json.loads(r.get("confs")) if isinstance(r.get("confs"), str) else r.get("confs")
                    except Exception:
                        try:
                            confs = ast.literal_eval(r.get("confs"))
                        except Exception:
                            confs = []
                    rows.append({
                        "id": int(r.get("id", 0)),
                        "class_names": class_names if isinstance(class_names, list) else [class_names],
                        "confs": confs if isinstance(confs, list) else [],
                        "time_s": float(r.get("time_s", 0.0)),
                        "frame_idx": int(r.get("frame_idx", 0)),
                        "clip_path": r.get("clip_path", None),
                        "saved": bool(r.get("saved", False))
                    })
            except Exception:
                continue
    rows = rows[:limit]
    return [EventResponse(**r) for r in rows]

@app.get("/events/{event_id}", response_model=EventResponse, tags=["events"])
def get_event(event_id: int):
    for sub in os.listdir(OUTPUT_DIR):
        candidate = os.path.join(OUTPUT_DIR, sub, "violations_events.csv")
        if os.path.exists(candidate):
            import pandas as pd
            df = pd.read_csv(candidate)
            for _, r in df.iterrows():
                if int(r.get("id", 0)) == event_id:
                    try:
                        class_names = json.loads(r.get("class_names")) if isinstance(r.get("class_names"), str) else r.get("class_names")
                    except Exception:
                        try:
                            class_names = ast.literal_eval(r.get("class_names"))
                        except Exception:
                            class_names = [r.get("class_names")]
                    try:
                        confs = json.loads(r.get("confs")) if isinstance(r.get("confs"), str) else r.get("confs")
                    except Exception:
                        try:
                            confs = ast.literal_eval(r.get("confs"))
                        except Exception:
                            confs = []
                    obj = {
                        "id": int(r.get("id", 0)),
                        "class_names": class_names if isinstance(class_names, list) else [class_names],
                        "confs": confs if isinstance(confs, list) else [],
                        "time_s": float(r.get("time_s", 0.0)),
                        "frame_idx": int(r.get("frame_idx", 0)),
                        "clip_path": r.get("clip_path", None),
                        "saved": bool(r.get("saved", False))
                    }
                    return EventResponse(**obj)
    raise HTTPException(status_code=404, detail="event not found")

@app.get("/events/{event_id}/clip", tags=["events"])
def download_clip(event_id: int):
    for sub in os.listdir(OUTPUT_DIR):
        candidate = os.path.join(OUTPUT_DIR, sub, "violations_events.csv")
        if os.path.exists(candidate):
            import pandas as pd
            df = pd.read_csv(candidate)
            for _, r in df.iterrows():
                if int(r.get("id", 0)) == event_id:
                    clip = r.get("clip_path", None)
                    if clip and os.path.exists(clip):
                        return FileResponse(clip, media_type="video/mp4", filename=os.path.basename(clip))
                    raise HTTPException(status_code=404, detail="clip not found on disk")
    raise HTTPException(status_code=404, detail="event not found")

@app.websocket("/ws/tasks/{task_id}")
async def ws_task_status(websocket: WebSocket, task_id: str):
    await websocket.accept()
    try:
        while True:
            task = tasks.get(task_id)
            await websocket.send_json(task or {"status":"not_found"})
            await asyncio.sleep(1.0)
    except Exception:
        await websocket.close()

@app.get("/health", tags=["system"])
def health():
    return {"status": "ok", "tasks": len(tasks)}

# Static files for clips (serve via Nginx in prod)
from fastapi.staticfiles import StaticFiles
app.mount("/static", StaticFiles(directory=OUTPUT_DIR), name="static")
