"""FFmpeg wrapper utilities."""

from __future__ import annotations

import logging
import shutil
import subprocess
from pathlib import Path

from chimera_vox.errors import FFmpegError

log = logging.getLogger(__name__)


def ffmpeg_available() -> bool:
    """Return True if ffmpeg is on PATH."""
    return shutil.which("ffmpeg") is not None


def ffprobe_available() -> bool:
    """Return True if ffprobe is on PATH."""
    return shutil.which("ffprobe") is not None


def run_ffmpeg(args: list[str], *, label: str = "ffmpeg") -> None:
    """Run ffmpeg with the given argument list, raising on failure."""
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", *args]
    log.debug("Running %s: %s", label, " ".join(cmd))
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    except FileNotFoundError as exc:
        raise FFmpegError("ffmpeg binary not found on PATH") from exc
    if proc.returncode != 0:
        raise FFmpegError(
            f"{label} failed (exit {proc.returncode}):\n{proc.stderr.strip()}"
        )


def probe_duration(path: Path) -> float:
    """Return duration of a media file in seconds."""
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(path),
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    except FileNotFoundError as exc:
        raise FFmpegError("ffprobe binary not found on PATH") from exc
    if proc.returncode != 0:
        raise FFmpegError(f"ffprobe failed: {proc.stderr.strip()}")
    return float(proc.stdout.strip())


def probe_resolution(path: Path) -> tuple[int, int]:
    """Return (width, height) of a video file."""
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=width,height",
        "-of",
        "csv=s=x:p=0",
        str(path),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise FFmpegError(f"ffprobe failed: {proc.stderr.strip()}")
    w, h = proc.stdout.strip().split("x")
    return int(w), int(h)


def extract_last_frame(video: Path, out_png: Path) -> Path:
    """Extract the last frame of a video as a PNG."""
    out_png.parent.mkdir(parents=True, exist_ok=True)
    run_ffmpeg(
        [
            "-sseof",
            "-0.1",
            "-i",
            str(video),
            "-frames:v",
            "1",
            "-q:v",
            "2",
            str(out_png),
        ],
        label="extract_last_frame",
    )
    if not out_png.exists():
        raise FFmpegError(f"Failed to extract last frame from {video}")
    return out_png


def extract_first_frame(video: Path, out_png: Path) -> Path:
    """Extract the first frame of a video as a PNG."""
    out_png.parent.mkdir(parents=True, exist_ok=True)
    run_ffmpeg(
        [
            "-i",
            str(video),
            "-frames:v",
            "1",
            "-q:v",
            "2",
            str(out_png),
        ],
        label="extract_first_frame",
    )
    return out_png
