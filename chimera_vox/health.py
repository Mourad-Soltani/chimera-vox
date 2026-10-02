"""Pre-flight health checks."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

from chimera_vox.config import Config
from chimera_vox.constants import MIN_DISK_GB
from chimera_vox.providers.base import Provider
from chimera_vox.utils.ffmpeg import ffmpeg_available, ffprobe_available
from chimera_vox.utils.files import check_disk_space

log = logging.getLogger(__name__)


@dataclass
class CheckResult:
    name: str
    status: str  # "pass" | "warn" | "fail"
    message: str


@dataclass
class HealthReport:
    checks: list[CheckResult] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not any(c.status == "fail" for c in self.checks)

    def summary(self) -> str:
        lines = []
        for c in self.checks:
            icon = {"pass": "✔", "warn": "⚠", "fail": "✘"}.get(c.status, "?")
            lines.append(f"  {icon} {c.name}: {c.message}")
        return "\n".join(lines)


async def run_health_checks(
    config: Config, providers: Sequence[Provider]
) -> HealthReport:
    """Run all pre-flight checks. Must be awaited from an event loop."""
    report = HealthReport()

    # FFmpeg
    if ffmpeg_available() and ffprobe_available():
        report.checks.append(CheckResult("ffmpeg", "pass", "ffmpeg + ffprobe found"))
    else:
        report.checks.append(
            CheckResult("ffmpeg", "fail", "ffmpeg or ffprobe not found on PATH")
        )

    # edge-tts
    try:
        import edge_tts  # noqa: F401
        report.checks.append(CheckResult("edge-tts", "pass", "edge-tts importable"))
    except ImportError:
        report.checks.append(CheckResult("edge-tts", "warn", "edge-tts not installed (required for narration)"))

    # Disk space
    ok, free = check_disk_space(config.temp_dir, MIN_DISK_GB)
    if ok:
        report.checks.append(
            CheckResult("disk", "pass", f"{free:.1f} GB free (>= {MIN_DISK_GB} GB)")
        )
    else:
        report.checks.append(
            CheckResult(
                "disk",
                "fail",
                f"Only {free:.1f} GB free (need >= {MIN_DISK_GB} GB)",
            )
        )

    # Photo readability
    try:
        from PIL import Image
        with Image.open(config.photo) as im:
            w, h = im.size
        report.checks.append(
            CheckResult("photo", "pass", f"{config.photo.name} ({w}x{h})")
        )
    except Exception as exc:  # noqa: BLE001
        report.checks.append(CheckResult("photo", "fail", f"Cannot open photo: {exc}"))

    # Providers
    provider_results = await _check_providers(providers)
    report.checks.extend(provider_results)

    return report


async def _check_providers(
    providers: Sequence[Provider],
) -> list[CheckResult]:
    results: list[CheckResult] = []
    for p in providers:
        try:
            health = await asyncio.wait_for(p.health_check(), timeout=15.0)
            status = "pass" if health.reachable else "warn"
            results.append(CheckResult(f"provider:{p.name}", status, health.message))
        except asyncio.TimeoutError:
            results.append(
                CheckResult(f"provider:{p.name}", "warn", "Health check timed out")
            )
        except Exception as exc:  # noqa: BLE001
            results.append(
                CheckResult(f"provider:{p.name}", "warn", f"Check failed: {exc}")
            )
    return results
