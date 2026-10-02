"""LTX-2.3 Turbo provider (ZeroGPU Space)."""

from __future__ import annotations

import asyncio
import logging
import tempfile
from pathlib import Path

import httpx
# from gradio_client import Client, handle_file  # lazy

from chimera_vox.constants import API_CANDIDATES, SPACES
from chimera_vox.errors import ProviderError
from chimera_vox.providers.base import Provider, ProviderHealth, ProviderResult
from chimera_vox.utils.retry import retry_async

log = logging.getLogger(__name__)


class LTXTurboProvider(Provider):
    """Generate clips via the LTX-2.3 Turbo ZeroGPU Space."""

    name = "ltx"

    def __init__(self, hf_token: str | None = None) -> None:
        super().__init__(hf_token)
        self.space = SPACES["ltx"]
        self._client = None
        self._api_name: str | None = None

    def _get_client(self):
        if self._client is None:
            from gradio_client import Client
            kwargs = {}
            if self.hf_token:
                kwargs["hf_token"] = self.hf_token
            self._client = Client(self.space, **kwargs)
        return self._client

    async def health_check(self) -> ProviderHealth:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                url = f"https://huggingface.co/spaces/{self.space}"
                resp = await client.head(url, follow_redirects=True)
                if resp.status_code < 400:
                    return ProviderHealth(True, f"Space reachable ({resp.status_code})")
                return ProviderHealth(False, f"HTTP {resp.status_code}")
        except Exception as exc:  # noqa: BLE001
            return ProviderHealth(False, str(exc))

    async def generate_clip(
        self,
        image: Path,
        prompt: str,
        duration: float,
    ) -> ProviderResult:
        async def _call() -> ProviderResult:
            return await asyncio.to_thread(self._generate_sync, image, prompt, duration)

        return await retry_async(_call, label=f"{self.name}.generate_clip")

    def _generate_sync(
        self, image: Path, prompt: str, duration: float
    ) -> ProviderResult:
        client = self._get_client()
        # Probe for a working API endpoint if not yet known
        if self._api_name is None:
            self._api_name = self._probe_api(client)

        try:
            result = client.predict(
                str(image),
                prompt,
                duration,
                api_name=self._api_name,
            )
        except Exception as exc:  # noqa: BLE001
            # Fallback: try common signatures
            try:
                result = client.predict(
                    str(image),
                    prompt,
                    api_name=self._api_name,
                )
            except Exception as exc2:  # noqa: BLE001
                raise ProviderError(f"{self.name} predict failed: {exc2}") from exc2

        # result is typically a filepath or tuple containing filepath
        video_path = self._extract_video_path(result)
        if not video_path or not Path(video_path).exists():
            raise ProviderError(f"{self.name} returned no video file")

        # Copy to a stable location
        out = Path(tempfile.mkdtemp(prefix="chimera_ltx_")) / "clip.mp4"
        Path(video_path).rename(out) if Path(video_path).parent != out.parent else None
        if not out.exists():
            import shutil
            shutil.copy(video_path, out)

        from chimera_vox.utils.ffmpeg import probe_duration

        try:
            dur = probe_duration(out)
        except Exception:
            dur = duration

        return ProviderResult(path=out, duration=dur, provider_name=self.name)

    def _probe_api(self, client: Client) -> str:
        for name in API_CANDIDATES:
            try:
                # Just checking if the endpoint exists in the schema
                if hasattr(client, "view_api"):
                    info = client.view_api(return_format="dict")
                    # crude check
                    if name in str(info):
                        return name
            except Exception:
                continue
        # Default fallback
        return "/generate"

    def _extract_video_path(self, result) -> str | None:
        if isinstance(result, (str, Path)) and str(result).endswith((".mp4", ".webm", ".gif")):
            return str(result)
        if isinstance(result, (list, tuple)):
            for item in result:
                if isinstance(item, (str, Path)) and str(item).endswith((".mp4", ".webm", ".gif")):
                    return str(item)
                if isinstance(item, dict) and "video" in item:
                    return str(item["video"])
        if isinstance(result, dict):
            for key in ("video", "output", "path", "file"):
                if key in result:
                    return str(result[key])
        return None
