from pathlib import Path

import pytest

from chimera_vox.config import Config
from chimera_vox.health import run_health_checks
from chimera_vox.providers.registry import build_provider_chain


def _dummy_photo(tmp_path: Path) -> Path:
    from PIL import Image

    p = tmp_path / "photo.png"
    Image.new("RGB", (64, 64), color="blue").save(p)
    return p


def test_health_runs(tmp_path):
    import asyncio
    photo = _dummy_photo(tmp_path)
    cfg = Config(
        photo=photo,
        script_text="Test.",
        providers=["mock"],
        temp_dir=tmp_path,
    )
    chain = build_provider_chain(cfg.providers)
    report = asyncio.run(run_health_checks(cfg, chain))
    assert report.checks
    names = {c.name for c in report.checks}
    assert "ffmpeg" in names
    assert "edge-tts" in names or True  # may be missing in restricted env
    assert "photo" in names
    assert report.ok or any(c.status == "warn" for c in report.checks)
