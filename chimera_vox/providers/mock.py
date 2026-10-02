"""Mock provider for offline testing and dry-run mode."""

from __future__ import annotations

import asyncio
import logging
import subprocess
import tempfile
from pathlib import Path

from chimera_vox.providers.base import Provider, ProviderHealth, ProviderResult

log = logging.getLogger(__name__)


class MockProvider(Provider):
    """Generates simple colored test clips with FFmpeg (no network)."""

    name = "mock"

    def __init__(self, hf_token: str | None = None) -> None:
        super().__init__(hf_token)

    async def health_check(self) -> ProviderHealth:
        return ProviderHealth(True, "Mock provider always available")

    async def generate_clip(
        self,
        image: Path,
        prompt: str,
        duration: float,
    ) -> ProviderResult:
        # Run in thread so we don't block the event loop
        return await asyncio.to_thread(self._generate_sync, image, prompt, duration)

    def _generate_sync(
        self, image: Path, prompt: str, duration: float
    ) -> ProviderResult:
        duration = max(1.0, min(duration, 6.0))
        out_dir = Path(tempfile.mkdtemp(prefix="chimera_mock_"))
        out = out_dir / "clip.mp4"

        # Create a simple animated color clip that roughly matches the input size
        # or falls back to 640x360
        try:
            from PIL import Image
            with Image.open(image) as im:
                w, h = im.size
            # keep reasonable size for mock
            w = min(w, 1280)
            h = min(h, 720)
        except Exception:
            w, h = 640, 360

        # Use a color based on a hash of the prompt for visual variety
        colors = ["red", "blue", "green", "purple", "orange", "teal"]
        color = colors[hash(prompt) % len(colors)]

        cmd = [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-f", "lavfi",
            "-i", f"color=c={color}:s={w}x{h}:d={duration}",
            "-vf", f"drawtext=text='MOCK':fontsize=36:fontcolor=white:x=(w-tw)/2:y=(h-th)/2",
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-t", str(duration),
            str(out),
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0 or not out.exists():
            # fallback without drawtext (in case fontconfig missing)
            cmd = [
                "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                "-f", "lavfi",
                "-i", f"color=c={color}:s={w}x{h}:d={duration}",
                "-c:v", "libx264", "-pix_fmt", "yuv420p",
                str(out),
            ]
            subprocess.run(cmd, check=True, capture_output=True)

        log.info("Mock clip generated: %s (%.1fs, %s)", out, duration, color)
        return ProviderResult(path=out, duration=duration, provider_name=self.name)
