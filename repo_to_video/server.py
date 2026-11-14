"""FastAPI backend server for Repo-to-Video React Frontend."""

from pathlib import Path
import uuid
import os
from typing import Dict, Any, Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from .pipeline import RepoToVideoPipeline
from .director.storyboard import Storyboard, Scene
from .config import OUTPUT_DIR, PROJECT_ROOT, is_gemini_configured, DEFAULT_STYLE


app = FastAPI(title="Repo-to-Video API", version="0.1.0")

# Enable CORS for Vite frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pipeline = RepoToVideoPipeline()

# Job tracker for async rendering
jobs: Dict[str, Dict[str, Any]] = {}


class AnalyzeRequest(BaseModel):
    repo_target: str
    style: Optional[str] = DEFAULT_STYLE


class RenderRequest(BaseModel):
    storyboard: Storyboard
    style: Optional[str] = DEFAULT_STYLE


@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "gemini_configured": is_gemini_configured(),
        "default_style": DEFAULT_STYLE
    }


@app.post("/api/analyze")
def analyze_repo(req: AnalyzeRequest):
    """Analyzes a codebase and drafts the initial onboarding storyboard."""
    try:
        repo_path, repo_name, digest = pipeline.analyze_repository(req.repo_target)
        storyboard = pipeline.draft_storyboard(digest, style=req.style or DEFAULT_STYLE)
        
        return {
            "success": True,
            "repo_name": repo_name,
            "digest": {
                "repo_name": digest.repo_name,
                "total_files": digest.total_files,
                "languages": digest.languages,
                "file_tree": digest.file_tree,
                "readme_excerpt": digest.readme_excerpt,
                "entry_points": digest.entry_points
            },
            "storyboard": storyboard.model_dump()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _run_render_job(job_id: str, storyboard: Storyboard, style: str):
    def update_progress(msg: str, val: float):
        if job_id in jobs:
            jobs[job_id]["progress"] = val
            jobs[job_id]["message"] = msg

    try:
        jobs[job_id]["status"] = "rendering"
        result = pipeline.render_video(storyboard, style=style, progress_cb=update_progress)
        video_filename = Path(result["video_path"]).name
        sub_filename = Path(result["subtitles_path"]).name if result.get("subtitles_path") else None
        
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["progress"] = 1.0
        jobs[job_id]["message"] = "Video generation complete!"
        jobs[job_id]["result"] = {
            "video_filename": video_filename,
            "video_url": f"/output/{video_filename}",
            "subtitles_url": f"/output/{sub_filename}" if sub_filename else None,
            "total_duration": result.get("total_duration", 0)
        }
    except Exception as e:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)
        jobs[job_id]["message"] = f"Rendering error: {e}"


@app.post("/api/render")
def trigger_render(req: RenderRequest, bg_tasks: BackgroundTasks):
    """Triggers video rendering asynchronously."""
    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        "job_id": job_id,
        "status": "queued",
        "progress": 0.0,
        "message": "Initializing rendering pipeline...",
        "result": None,
        "error": None
    }
    bg_tasks.add_task(_run_render_job, job_id, req.storyboard, req.style or DEFAULT_STYLE)
    return {"job_id": job_id}


@app.get("/api/jobs/{job_id}")
def get_job_status(job_id: str):
    """Polls job status and real-time progress."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return jobs[job_id]


@app.get("/api/videos")
def list_videos():
    """Lists all previously rendered onboarding videos."""
    videos = []
    for f in OUTPUT_DIR.glob("*.mp4"):
        stat = f.stat()
        videos.append({
            "filename": f.name,
            "url": f"/output/{f.name}",
            "size_bytes": stat.st_size,
            "modified_time": stat.st_mtime
        })
    videos.sort(key=lambda x: -x["modified_time"])
    return {"videos": videos}


# Static output files mount
app.mount("/output", StaticFiles(directory=str(OUTPUT_DIR)), name="output")

# Mount frontend assets
dist_dir = PROJECT_ROOT / "frontend" / "dist"
assets_dir = dist_dir / "assets"
if assets_dir.exists():
    app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")


# SPA Catch-all: serve index.html or static root files
@app.get("/{full_path:path}")
def serve_spa(full_path: str):
    if dist_dir.exists():
        target = dist_dir / full_path
        if full_path and target.is_file():
            return FileResponse(target)
        index_file = dist_dir / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
    return {"message": "Repo-to-Video API running. Build frontend with 'npm run build'."}
