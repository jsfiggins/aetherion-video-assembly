# ✅ Aetherion Video Assembly Service with Supabase Upload (Python + FastAPI)

# File: main.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import requests
import subprocess
import tempfile
from pathlib import Path
from supabase import create_client, Client

app = FastAPI()

# 🔑 Replace these with your real Supabase project values
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://your-project.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "your-supabase-service-role-key")
BUCKET_NAME = "aetherion-media"
OUTPUT_FOLDER = "video/assembled"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

class AssembleRequest(BaseModel):
    frames_folder_url: str
    audio_file_url: str
    output_file_name: str

@app.post("/assemble")
async def assemble_video(req: AssembleRequest):
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            frames_dir = Path(temp_dir) / "frames"
            frames_dir.mkdir()

            # For now, simulate 1 frame image (real use = download all frames later)
            frame_path = frames_dir / "frame1.png"
            download_file(req.frames_folder_url, frame_path)

            audio_path = Path(temp_dir) / "audio.mp3"
            download_file(req.audio_file_url, audio_path)

            output_path = Path(temp_dir) / req.output_file_name

            ffmpeg_command = [
                "ffmpeg",
                "-framerate", "1",
                "-pattern_type", "glob",
                "-i", f"{frames_dir}/*.png",
                "-i", str(audio_path),
                "-shortest",
                "-pix_fmt", "yuv420p",
                str(output_path)
            ]

            subprocess.run(ffmpeg_command, check=True)

            # ✅ Upload video to Supabase
            upload_to_supabase(output_path, req.output_file_name)

            return {"status": "success", "video_file": req.output_file_name}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def download_file(url, output_path):
    r = requests.get(url, stream=True)
    if r.status_code == 200:
        with open(output_path, 'wb') as f:
            for chunk in r.iter_content(1024):
                f.write(chunk)
    else:
        raise Exception(f"Download failed: {url}")

def upload_to_supabase(file_path, file_name):
    with open(file_path, "rb") as f:
        data = f.read()
        supabase.storage.from_(BUCKET_NAME).upload(
            file=f"{OUTPUT_FOLDER}/{file_name}",
            file_data=data,
            file_options={"content-type": "video/mp4"}
        )

# ------------------------
# File: requirements.txt
# ------------------------

# fastapi
# uvicorn
# requests
# supabase

# ------------------------
# File: Procfile
# ------------------------

# web: uvicorn main:app --host=0.0.0.0 --port=${PORT:-5000}

# ------------------------
# File: runtime.txt
# ------------------------

# python-3.10
