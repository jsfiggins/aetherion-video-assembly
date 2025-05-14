from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import requests
import subprocess
import tempfile
from pathlib import Path

app = FastAPI()

# -----------------------------
# Environment variables
# -----------------------------
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
BUCKET_NAME = "aetherion-media"
OUTPUT_FOLDER = "video/assembled"

# -----------------------------
# Request Model
# -----------------------------
class AssembleRequest(BaseModel):
    frames_folder_url: str
    audio_file_url: str
    output_file_name: str

# -----------------------------
# Routes
# -----------------------------
@app.post("/assemble")
async def assemble_video(req: AssembleRequest):
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            frames_dir = Path(temp_dir) / "frames"
            frames_dir.mkdir()

            # Download example 1 frame (test mode)
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

            # Upload final video to Supabase
            upload_to_supabase(output_path, req.output_file_name)

            return {"status": "success", "video_file": req.output_file_name}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# -----------------------------
# Utilities
# -----------------------------
def download_file(url, output_path):
    r = requests.get(url, stream=True)
    if r.status_code == 200:
        with open(output_path, 'wb') as f:
            for chunk in r.iter_content(1024):
                f.write(chunk)
    else:
        raise Exception(f"Download failed: {url}")

def upload_to_supabase(file_path, file_name):
    storage_url = f"{SUPABASE_URL}/storage/v1/object/{BUCKET_NAME}/{OUTPUT_FOLDER}/{file_name}"

    headers = {
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "video/mp4"
    }

    with open(file_path, "rb") as f:
        file_data = f.read()

    response = requests.put(storage_url, headers=headers, data=file_data)

    if response.status_code != 200 and response.status_code != 201:
        raise Exception(f"Failed to upload to Supabase Storage: {response.status_code}, {response.text}")
