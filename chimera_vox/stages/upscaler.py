"""Upscale the stitched video to the requested resolution using FFmpeg."""

from __future__ import annotations

import logging
from pathlib import Path

from chimera_vox.constants import RESOLUTIONS
from chimera_vox.errors import UpscalingError
from chimera_vox.utils.ffmpeg import probe_resolution, run_ffmpeg
from chimera_vox.utils.files import ensure_dir

log = logging.getLogger(__name__)


def upscale_video(
    input_path: Path,
    output_path: Path,
    resolution: str,
    temp_dir: Path,
    fps: int = 24,
    threads: int = 4,
) -> Path:
    """Upscale input_path to the target resolution using lanczos."""
    if resolution not in RESOLUTIONS:
        raise UpscalingError(
            f"Unknown resolution '{resolution}'. Options: {', '.join(RESOLUTIONS)}"
        )

    target_w, target_h = RESOLUTIONS[resolution]
    ensure_dir(temp_dir)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Avoid same-path overwrite issues
    if input_path.resolve() == output_path.resolve():
        intermediate = temp_dir / "upscale_tmp.mp4"
        run_ffmpeg(
            [
                "-i",
                str(input_path),
                "-vf",
                f"scale={target_w}:{target_h}:force_original_aspect_ratio=decrease,"
                f"pad={target_w}:{target_h}:(ow-iw)/2:(oh-ih)/2",
                "-c:v",
                "libx264",
                "-preset",
                "medium",
                "-crf",
                "18",
                "-r",
                str(fps),
                "-pix_fmt",
                "yuv420p",
                "-c:a",
                "copy",
                "-threads",
                str(threads),
                str(intermediate),
            ],
            label="upscale",
        )
        intermediate.replace(output_path)
    else:
        run_ffmpeg(
            [
                "-i",
                str(input_path),
                "-vf",
                f"scale={target_w}:{target_h}:force_original_aspect_ratio=decrease,"
                f"pad={target_w}:{target_h}:(ow-iw)/2:(oh-ih)/2",
                "-c:v",
                "libx264",
                "-preset",
                "medium",
                "-crf",
                "18",
                "-r",
                str(fps),
                "-pix_fmt",
                "yuv420p",
                "-c:a",
                "copy",
                "-threads",
                str(threads),
                str(output_path),
            ],
            label="upscale",
        )

    if not output_path.exists():
        raise UpscalingError("Upscaling produced no output file")

    try:
        w, h = probe_resolution(output_path)
        log.info("Upscaled to %dx%d → %s", w, h, output_path)
    except Exception:
        log.info("Upscaled → %s", output_path)

    return output_path
