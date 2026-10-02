"""Stitch AI clips together and mux narration audio using FFmpeg."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Sequence

from chimera_vox.errors import StitchingError
from chimera_vox.providers.base import ProviderResult
from chimera_vox.utils.ffmpeg import probe_duration, run_ffmpeg
from chimera_vox.utils.files import ensure_dir

log = logging.getLogger(__name__)


def stitch_clips(
    clips: Sequence[ProviderResult],
    audio_path: Path,
    output_path: Path,
    temp_dir: Path,
    fps: int = 24,
    threads: int = 4,
) -> Path:
    """Concatenate clips and mux the narration audio."""
    if not clips:
        raise StitchingError("No clips to stitch")

    ensure_dir(temp_dir)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write concat list
    list_file = temp_dir / "concat.txt"
    with list_file.open("w") as f:
        for clip in clips:
            # Escape single quotes for the concat demuxer
            safe = str(clip.path).replace("'", "'\\''")
            f.write(f"file '{safe}'\n")

    # Intermediate video without audio
    intermediate = temp_dir / "stitched_noaudio.mp4"
    run_ffmpeg(
        [
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(list_file),
            "-c:v",
            "libx264",
            "-preset",
            "fast",
            "-crf",
            "18",
            "-r",
            str(fps),
            "-pix_fmt",
            "yuv420p",
            "-threads",
            str(threads),
            "-an",
            str(intermediate),
        ],
        label="stitch_concat",
    )

    # Mux audio if present
    if audio_path.exists() and audio_path.stat().st_size > 0:
        run_ffmpeg(
            [
                "-i",
                str(intermediate),
                "-i",
                str(audio_path),
                "-c:v",
                "copy",
                "-c:a",
                "aac",
                "-b:a",
                "192k",
                "-shortest",
                "-threads",
                str(threads),
                str(output_path),
            ],
            label="mux_audio",
        )
    else:
        # No audio — just rename
        intermediate.rename(output_path)

    if not output_path.exists():
        raise StitchingError("Stitching produced no output file")

    try:
        dur = probe_duration(output_path)
        log.info("Stitched video: %s (%.1fs)", output_path, dur)
    except Exception:
        log.info("Stitched video: %s", output_path)

    return output_path
