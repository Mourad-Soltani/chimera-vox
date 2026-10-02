import pytest

from chimera_vox.stages.tts import generate_narration


@pytest.mark.asyncio
async def test_tts_generates_file(tmp_path):
    out = tmp_path / "narration.mp3"
    await generate_narration("Hello, this is a test.", out)
    assert out.exists()
    assert out.stat().st_size > 0
