"""Ken Burns static-image fallback provider.

Produces a slow pan/zoom over the input photo using FFmpeg's zoompan filter.
Always succeeds (given FFmpeg). Used as the automatic last-resort floor when
all AI providers fail, or can be selected explicitly via --providers kenburns.
"""

from __future__ import annotations

import asyncio
import logging
import subprocess
import tempfile
from pathlib import Path

from chimera_vox.providers.base import Provider, ProviderHealth, ProviderResult

log = logging.getLogger(__name__)


class KenBurnsProvider(Provider):
    """Static photo + Ken Burns pan/zoom → short video clip."""

    name = "kenburns"

    def __init__(self, hf_token: str | None = None) -> None:
        super().__init__(hf_token)

    async def health_check(self) -> ProviderHealth:
        return ProviderHealth(True, "Ken Burns (FFmpeg) always available")

    async def generate_clip(
        self,
        image: Path,
        prompt: str,
        duration: float,
    ) -> ProviderResult:
        return await asyncio.to_thread(self._generate_sync, image, prompt, duration)

    def _generate_sync(
        self, image: Path, prompt: str, duration: float
    ) -> ProviderResult:
        duration = max(1.5, min(float(duration), 8.0))
        out_dir = Path(tempfile.mkdtemp(prefix="chimera_kb_"))
        out = out_dir / "clip.mp4"

        # Target a reasonable working resolution; final upscale happens later
        # zoompan: slow zoom-in + slight pan. d = frames at 25 fps
        frames = int(duration * 25)
        # z goes from 1.0 → ~1.15 over the clip; x/y keep subject roughly centered
        z_expr = f"min(zoom+0.0015,1.15)"
        x_expr = "iw/2-(iw/zoom/2)"
        y_expr = "ih/2-(ih/zoom/2)"

        vf = (
            f"scale=1280:720:force_original_aspect_ratio=increase,"
            f"crop=1280:720,"
            f"zoompan=z='{z_expr}':x='{x_expr}':y='{y_expr}':d={frames}:s=1280x720:fps=25"
        )

        cmd = [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-loop", "1",
            "-i", str(image),
            "-vf", vf,
            "-t", f"{duration:.2f}",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-preset", "fast",
            "-crf", "20",
            str(out),
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0 or not out.exists():
            # Absolute minimal fallback: static image turned into a video
            cmd = [
                "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                "-loop", "1",
                "-i", str(image),
                "-c:v", "libx264",
                "-t", f"{duration:.2f}",
                "-pix_fmt", "yuv420p",
                "-vf", "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2",
                str(out),
            ]
            subprocess.run(cmd, check=True, capture_output=True)

        log.info("Ken Burns clip generated: %s (%.1fs)", out, duration)
        return ProviderResult(path=out, duration=duration, provider_name=self.name)
