"""
ChimeraVox — Gradio demo

Default path uses Ken Burns + edge-tts (CPU-only, always works).
Optional AI providers when HF_TOKEN is set and Spaces are reachable.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import gradio as gr

from chimera_vox.config import Config
from chimera_vox.constants import VOICE_CHOICES
from chimera_vox.pipeline import run_pipeline_sync
from chimera_vox import __version__

EXAMPLE_SCRIPT = (
    "Welcome to ChimeraVox. "
    "This demo turns a single photo and a short script into a narrated video. "
    "When AI providers are unavailable, we fall back to a Ken Burns pan over your image."
)


def _run(
    photo,
    script: str,
    prompt: str,
    mode: str,
    resolution: str,
    voice: str,
    progress=gr.Progress(track_tqdm=False),
):
    if photo is None:
        raise gr.Error("Please upload a photo.")
    script = (script or "").strip()
    if not script:
        raise gr.Error("Please enter a script.")

    photo_path = Path(photo)
    out_dir = Path(tempfile.mkdtemp(prefix="chimera_demo_"))
    output = out_dir / "output.mp4"
    temp_dir = out_dir / "tmp"
    temp_dir.mkdir()

    # Static motion presets map 1:1 to provider names
    _MOTION = {
        "Ken Burns (zoom center)": "kenburns",
        "Zoom in": "zoomin",
        "Zoom out": "zoomout",
        "Pan left": "panleft",
        "Pan right": "panright",
        "Pan up": "panup",
        "Pan down": "pandown",
        "Diagonal drift": "drift",
    }
    if mode in _MOTION:
        providers = [_MOTION[mode]]
        dry_run = False
        skip_health = True
    elif mode == "Dry-run (mock colors)":
        providers = ["mock"]
        dry_run = True
        skip_health = True
    else:
        # Full AI chain — auto-fallback to Ken Burns if Spaces fail
        providers = ["ltx", "cogvideox", "wan"]
        dry_run = False
        skip_health = False

    progress(0.1, desc="Configuring…")
    cfg = Config(
        photo=photo_path,
        script_text=script,
        prompt=prompt or "",
        resolution=resolution,
        output=output,
        voice=voice,
        providers=providers,
        dry_run=dry_run,
        skip_health_check=skip_health,
        temp_dir=temp_dir,
        verbose=False,
    )

    progress(0.2, desc="Running pipeline…")
    try:
        result = run_pipeline_sync(cfg)
    except Exception as exc:
        raise gr.Error(f"Pipeline failed: {exc}") from exc

    progress(1.0, desc="Done")
    return str(result)


def build_ui() -> gr.Blocks:
    with gr.Blocks(title="ChimeraVox Demo") as demo:
        gr.Markdown(
            f"""
# ChimeraVox
### Photo + script → narrated video (free-tier pipeline)

Version **{__version__}** · Author [Mourad Soltani](https://github.com/Mourad-Soltani)

Upload a photo, write a short script, and generate a video.
The default **Ken Burns** mode runs entirely on CPU and always produces a result.
AI image-to-video (ZeroGPU Spaces) is optional and may queue or fail under free-tier limits.
            """
        )

        with gr.Row():
            with gr.Column(scale=1):
                photo = gr.Image(type="filepath", label="Photo", height=280)
                script = gr.Textbox(
                    label="Script",
                    lines=5,
                    value=EXAMPLE_SCRIPT,
                    placeholder="Narration text…",
                )
                prompt = gr.Textbox(
                    label="Visual prompt (AI modes only)",
                    placeholder="cinematic slow pan, golden hour…",
                )
                mode = gr.Dropdown(
                    choices=[
                        "Ken Burns (zoom center)",
                        "Zoom in",
                        "Zoom out",
                        "Pan left",
                        "Pan right",
                        "Pan up",
                        "Pan down",
                        "Diagonal drift",
                        "Dry-run (mock colors)",
                        "Full AI (ZeroGPU — may queue)",
                    ],
                    value="Ken Burns (zoom center)",
                    label="Mode / motion",
                )
                with gr.Row():
                    resolution = gr.Dropdown(
                        choices=["720p", "1080p", "4k"],
                        value="720p",
                        label="Resolution",
                    )
                    voice = gr.Dropdown(
                        choices=list(VOICE_CHOICES),
                        value="en-US-AriaNeural",
                        label="Voice (EN / FR / AR)",
                    )
                btn = gr.Button("Generate video", variant="primary")

            with gr.Column(scale=1):
                video = gr.Video(label="Output")
                gr.Markdown(
                    """
**Tips**
- Start with **Ken Burns** — instant, no GPU queue.
- **Full AI** needs reachable Hugging Face ZeroGPU Spaces and may take minutes.
- If all AI providers fail, ChimeraVox automatically falls back to Ken Burns.
- [GitHub](https://github.com/Mourad-Soltani/chimera-vox) · [Runbook](https://github.com/Mourad-Soltani/chimera-vox/blob/main/docs/RUNBOOK.md)
                    """
                )

        btn.click(
            fn=_run,
            inputs=[photo, script, prompt, mode, resolution, voice],
            outputs=[video],
        )

    return demo


if __name__ == "__main__":
    demo = build_ui()
    # Cloud hosts (Render, etc.) inject PORT; never enable share=True in production
    demo.queue(default_concurrency_limit=1).launch(
        server_name="0.0.0.0",
        server_port=int(os.getenv("PORT", "7860")),
        share=False,
    )
