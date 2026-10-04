"""
ChimeraVox — Streamlit demo (Streamlit Community Cloud)

Default path: Ken Burns + edge-tts (CPU-only, always works).
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import streamlit as st

from chimera_vox import __version__
from chimera_vox.config import Config
from chimera_vox.pipeline import run_pipeline_sync

EXAMPLE_SCRIPT = (
    "Welcome to ChimeraVox. "
    "This demo turns a single photo and a short script into a narrated video. "
    "When AI providers are unavailable, we fall back to a Ken Burns pan over your image."
)

VOICES = [
    "en-US-AriaNeural",
    "en-US-JennyNeural",
    "en-US-GuyNeural",
    "en-GB-SoniaNeural",
    "en-GB-RyanNeural",
    "fr-FR-DeniseNeural",
    "fr-FR-HenriNeural",
]

st.set_page_config(
    page_title="ChimeraVox",
    page_icon="🎬",
    layout="wide",
)

st.title("🎬 ChimeraVox")
st.caption(
    f"Photo + script → narrated video · free-tier pipeline · v{__version__} · "
    "[Mourad Soltani](https://github.com/Mourad-Soltani)"
)

st.markdown(
    """
Upload a photo and a short script. **Ken Burns** mode runs on CPU and always
produces a video. Full AI (ZeroGPU) is optional and may queue or fail under free-tier limits.
"""
)

col_l, col_r = st.columns(2)

with col_l:
    photo_file = st.file_uploader("Photo", type=["jpg", "jpeg", "png", "webp"])
    script = st.text_area("Script", value=EXAMPLE_SCRIPT, height=140)
    prompt = st.text_input(
        "Visual prompt (AI modes only)",
        placeholder="cinematic slow pan, golden hour…",
    )
    mode = st.radio(
        "Mode",
        [
            "Ken Burns (reliable demo)",
            "Dry-run (mock colors)",
            "Full AI (ZeroGPU — may queue)",
        ],
        index=0,
    )
    c1, c2 = st.columns(2)
    with c1:
        resolution = st.selectbox("Resolution", ["720p", "1080p", "4k"], index=0)
    with c2:
        voice = st.selectbox("Voice", VOICES, index=0)
    run_btn = st.button("Generate video", type="primary", use_container_width=True)

with col_r:
    st.subheader("Output")
    out_slot = st.empty()
    st.markdown(
        """
**Tips**
- Prefer **Ken Burns** on free hosts (no GPU queue).
- Keep the script short (1–3 sentences) for faster runs.
- Full AI needs a reachable Hugging Face Space; otherwise Ken Burns is used automatically.
- [GitHub](https://github.com/Mourad-Soltani/chimera-vox) · [Runbook](https://github.com/Mourad-Soltani/chimera-vox/blob/main/docs/RUNBOOK.md)
"""
    )

if run_btn:
    if photo_file is None:
        st.error("Please upload a photo.")
        st.stop()
    script = (script or "").strip()
    if not script:
        st.error("Please enter a script.")
        st.stop()

    work = Path(tempfile.mkdtemp(prefix="chimera_st_"))
    photo_path = work / (photo_file.name or "photo.png")
    photo_path.write_bytes(photo_file.getvalue())
    output = work / "output.mp4"
    temp_dir = work / "tmp"
    temp_dir.mkdir()

    if mode.startswith("Ken Burns"):
        providers, dry_run, skip_health = ["kenburns"], False, True
    elif mode.startswith("Dry-run"):
        providers, dry_run, skip_health = ["mock"], True, True
    else:
        providers, dry_run, skip_health = ["ltx", "cogvideox", "wan"], False, False

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

    progress = st.progress(0, text="Configuring…")
    status = st.status("Running ChimeraVox pipeline…", expanded=True)
    try:
        with status:
            st.write("1/4 Configuring…")
            progress.progress(10, text="Configuring…")
            st.write("2/4 Generating narration + clips (this can take several minutes)…")
            progress.progress(25, text="Running pipeline…")
            result = run_pipeline_sync(cfg)
            progress.progress(90, text="Finalizing…")
            st.write("3/4 Encoding complete")
            progress.progress(100, text="Done")
            st.write("4/4 Done")
        status.update(label="Done", state="complete")
        out_slot.video(str(result))
        st.success(f"Video ready: {result.name}")
        with open(result, "rb") as f:
            st.download_button(
                "Download MP4",
                data=f,
                file_name="chimera_vox_output.mp4",
                mime="video/mp4",
            )
    except Exception as exc:
        status.update(label="Failed", state="error")
        progress.progress(0, text="Failed")
        st.error(f"Pipeline failed: {exc}")
