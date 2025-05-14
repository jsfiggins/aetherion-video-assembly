from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import os
import requests
import subprocess
import tempfile
from pathlib import Path

app = FastAPI()

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

            # Download example 1 frame (for testing)
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

            return {"status": "success", "video_path": str(output_path)}

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
