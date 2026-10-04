"""Static-image motion providers (Ken Burns family).

CPU-only FFmpeg effects over a still photo. Always available as demos or
last-resort fallbacks when AI providers fail.
"""

from __future__ import annotations

import asyncio
import logging
import subprocess
import tempfile
from pathlib import Path

from chimera_vox.providers.base import Provider, ProviderHealth, ProviderResult

log = logging.getLogger(__name__)

# Effect presets → zoompan expressions (evaluated per frame at fps=25)
# z: zoom factor, x/y: top-left of crop window in input coords
_EFFECTS: dict[str, dict[str, str]] = {
    # Classic Ken Burns: slow zoom-in, subject held near center
    "kenburns": {
        "label": "Ken Burns (zoom-in center)",
        "z": "min(zoom+0.0015,1.18)",
        "x": "iw/2-(iw/zoom/2)",
        "y": "ih/2-(ih/zoom/2)",
    },
    # Pure zoom-in (slightly stronger)
    "zoomin": {
        "label": "Zoom in",
        "z": "min(zoom+0.0022,1.25)",
        "x": "iw/2-(iw/zoom/2)",
        "y": "ih/2-(ih/zoom/2)",
    },
    # Zoom out: start tight, pull back
    "zoomout": {
        "label": "Zoom out",
        "z": "if(eq(on,1),1.25,max(zoom-0.0020,1.0))",
        "x": "iw/2-(iw/zoom/2)",
        "y": "ih/2-(ih/zoom/2)",
    },
    # Pan left across the frame
    "panleft": {
        "label": "Pan left",
        "z": "1.12",
        "x": "max(iw/zoom-ow,0)*on/duration",
        "y": "ih/2-(ih/zoom/2)",
    },
    # Pan right
    "panright": {
        "label": "Pan right",
        "z": "1.12",
        "x": "max(iw/zoom-ow,0)*(1-on/duration)",
        "y": "ih/2-(ih/zoom/2)",
    },
    # Pan up
    "panup": {
        "label": "Pan up",
        "z": "1.12",
        "x": "iw/2-(iw/zoom/2)",
        "y": "max(ih/zoom-oh,0)*on/duration",
    },
    # Pan down
    "pandown": {
        "label": "Pan down",
        "z": "1.12",
        "x": "iw/2-(iw/zoom/2)",
        "y": "max(ih/zoom-oh,0)*(1-on/duration)",
    },
    # Diagonal drift (down-right) + gentle zoom
    "drift": {
        "label": "Diagonal drift",
        "z": "min(zoom+0.0012,1.15)",
        "x": "max(iw/zoom-ow,0)*on/duration*0.85",
        "y": "max(ih/zoom-oh,0)*on/duration*0.85",
    },
}


def available_motion_effects() -> list[str]:
    return list(_EFFECTS.keys())


class StaticMotionProvider(Provider):
    """Still photo → short clip via a named FFmpeg motion preset."""

    effect: str = "kenburns"
    name: str = "kenburns"

    def __init__(self, hf_token: str | None = None, effect: str | None = None) -> None:
        super().__init__(hf_token)
        if effect:
            self.effect = effect
            self.name = effect
        if self.effect not in _EFFECTS:
            raise ValueError(
                f"Unknown motion effect '{self.effect}'. "
                f"Choose from: {', '.join(_EFFECTS)}"
            )

    async def health_check(self) -> ProviderHealth:
        label = _EFFECTS[self.effect]["label"]
        return ProviderHealth(True, f"{label} (FFmpeg) always available")

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
        out_dir = Path(tempfile.mkdtemp(prefix=f"chimera_{self.effect}_"))
        out = out_dir / "clip.mp4"
        frames = max(int(duration * 25), 25)
        preset = _EFFECTS[self.effect]
        z_expr, x_expr, y_expr = preset["z"], preset["x"], preset["y"]

        # duration in expressions refers to total frames for pan presets
        x_expr = x_expr.replace("duration", str(frames))
        y_expr = y_expr.replace("duration", str(frames))

        vf = (
            f"scale=1280:720:force_original_aspect_ratio=increase,"
            f"crop=1280:720,"
            f"zoompan=z='{z_expr}':x='{x_expr}':y='{y_expr}':"
            f"d={frames}:s=1280x720:fps=25"
        )

        cmd = [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-loop",
            "1",
            "-i",
            str(image),
            "-vf",
            vf,
            "-t",
            f"{duration:.2f}",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-preset",
            "fast",
            "-crf",
            "20",
            str(out),
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0 or not out.exists():
            log.warning(
                "%s zoompan failed (%s) — static fallback",
                self.effect,
                (proc.stderr or "")[:200],
            )
            cmd = [
                "ffmpeg",
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-loop",
                "1",
                "-i",
                str(image),
                "-c:v",
                "libx264",
                "-t",
                f"{duration:.2f}",
                "-pix_fmt",
                "yuv420p",
                "-vf",
                "scale=1280:720:force_original_aspect_ratio=decrease,"
                "pad=1280:720:(ow-iw)/2:(oh-ih)/2",
                str(out),
            ]
            subprocess.run(cmd, check=True, capture_output=True)

        log.info(
            "%s clip generated: %s (%.1fs)", self.effect, out, duration
        )
        return ProviderResult(path=out, duration=duration, provider_name=self.name)


# Concrete providers for the registry (one class per effect name)
class KenBurnsProvider(StaticMotionProvider):
    effect = "kenburns"
    name = "kenburns"


class ZoomInProvider(StaticMotionProvider):
    effect = "zoomin"
    name = "zoomin"


class ZoomOutProvider(StaticMotionProvider):
    effect = "zoomout"
    name = "zoomout"


class PanLeftProvider(StaticMotionProvider):
    effect = "panleft"
    name = "panleft"


class PanRightProvider(StaticMotionProvider):
    effect = "panright"
    name = "panright"


class PanUpProvider(StaticMotionProvider):
    effect = "panup"
    name = "panup"


class PanDownProvider(StaticMotionProvider):
    effect = "pandown"
    name = "pandown"


class DriftProvider(StaticMotionProvider):
    effect = "drift"
    name = "drift"
