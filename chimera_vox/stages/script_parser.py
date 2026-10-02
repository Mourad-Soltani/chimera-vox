"""Split a script into timed, sentence-level segments."""

from __future__ import annotations

import re
from dataclasses import dataclass

# Approximate words-per-second for narration (moderate pace)
WORDS_PER_SECOND = 2.5

_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+|\n{2,}")


@dataclass
class ScriptSegment:
    """A single narration segment."""

    index: int
    text: str
    estimated_duration: float


def parse_script(script: str, clip_duration: float = 3.0) -> list[ScriptSegment]:
    """
    Split script into segments whose estimated spoken duration is close to
    clip_duration. Falls back to sentence splitting if paragraphs are too short.
    Also force-splits very long sentences by word count.
    """
    script = script.strip()
    if not script:
        return []

    # First split on double newlines (paragraphs) then sentences
    paragraphs = re.split(r"\n{2,}", script)
    raw_sentences: list[str] = []
    for para in paragraphs:
        parts = _SENTENCE_RE.split(para.strip())
        raw_sentences.extend(p.strip() for p in parts if p.strip())

    if not raw_sentences:
        return []

    target_words = max(1, int(clip_duration * WORDS_PER_SECOND))

    # Further split any sentence that is itself longer than ~2x target
    units: list[str] = []
    for sent in raw_sentences:
        words = sent.split()
        if len(words) <= target_words * 2:
            units.append(sent)
        else:
            # force-split long run into chunks of ~target_words
            for i in range(0, len(words), target_words):
                chunk = " ".join(words[i : i + target_words])
                if chunk:
                    units.append(chunk)

    segments: list[ScriptSegment] = []
    current_text: list[str] = []
    current_words = 0
    idx = 0

    for unit in units:
        words = len(unit.split())
        if current_words + words > target_words and current_text:
            text = " ".join(current_text)
            segments.append(
                ScriptSegment(
                    index=idx,
                    text=text,
                    estimated_duration=max(1.0, current_words / WORDS_PER_SECOND),
                )
            )
            idx += 1
            current_text = [unit]
            current_words = words
        else:
            current_text.append(unit)
            current_words += words

    if current_text:
        text = " ".join(current_text)
        segments.append(
            ScriptSegment(
                index=idx,
                text=text,
                estimated_duration=max(1.0, current_words / WORDS_PER_SECOND),
            )
        )

    return segments


def full_text(segments: list[ScriptSegment]) -> str:
    """Reassemble the full narration text from segments."""
    return " ".join(seg.text for seg in segments)
