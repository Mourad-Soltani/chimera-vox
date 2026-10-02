from chimera_vox.stages.script_parser import full_text, parse_script


def test_empty_script():
    assert parse_script("") == []
    assert parse_script("   \n\n  ") == []


def test_single_sentence():
    segs = parse_script("Hello world.")
    assert len(segs) == 1
    assert segs[0].text == "Hello world."
    assert segs[0].estimated_duration > 0


def test_multiple_paragraphs():
    # Use longer paragraphs so packing does not merge them under default duration
    script = (
        "First paragraph here with enough words to stand alone as a segment. "
        "It needs more content so the duration estimate exceeds a small clip target.\n\n"
        "Second paragraph here also has sufficient length to become its own segment "
        "and not be merged with the previous one under the packing rules."
    )
    segs = parse_script(script, clip_duration=2.0)
    assert len(segs) >= 2


def test_full_text_roundtrip():
    script = "One. Two. Three."
    segs = parse_script(script)
    assert "One." in full_text(segs)
    assert "Three." in full_text(segs)


def test_long_paragraph_splits():
    words = " ".join(["word"] * 200)
    segs = parse_script(words + ".", clip_duration=1.0)  # force small target
    assert len(segs) >= 2
