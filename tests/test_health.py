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


@pytest.mark.asyncio
async def test_health_runs(tmp_path):
    photo = _dummy_photo(tmp_path)
    cfg = Config(
        photo=photo,
        script_text="Test.",
        providers=["ltx"],
        temp_dir=tmp_path,
    )
    chain = build_provider_chain(cfg.providers)
    report = await run_health_checks(cfg, chain)
    assert report.checks
    names = {c.name for c in report.checks}
    assert "ffmpeg" in names
    assert "edge-tts" in names
    assert "photo" in names
