"""File-system helpers."""

from __future__ import annotations

import logging
import shutil
from pathlib import Path

from chimera_vox.constants import MIN_DISK_GB

log = logging.getLogger(__name__)


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def free_disk_gb(path: Path) -> float:
    """Return free disk space in GB for the filesystem containing path."""
    target = path if path.exists() else path.parent
    while not target.exists() and target != target.parent:
        target = target.parent
    usage = shutil.disk_usage(target)
    return usage.free / (1024**3)


def check_disk_space(path: Path, min_gb: float = MIN_DISK_GB) -> tuple[bool, float]:
    """Return (ok, free_gb)."""
    free = free_disk_gb(path)
    return free >= min_gb, free


def clean_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path, ignore_errors=True)
    path.mkdir(parents=True, exist_ok=True)
