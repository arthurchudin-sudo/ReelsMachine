from reels.plan import Clip, resolve_clip, transcript_for_prompt

WORDS = [{"i": i, "start": i * 0.5, "end": i * 0.5 + 0.4, "word": f"m{i}"} for i in range(40)]


def make_clip(**kw):
    base = dict(title="t", start_word=2, end_word=20, hook_text="h", why="w", score=7,
                emphasis_words=[], cues=[], broll_ideas=[],
                gringo={"caption": "c", "cta": "x", "hashtags": []},
                linkedin={"post": "p", "cta": "x"})
    return Clip(**{**base, **kw})


def test_drop_range_splits_segments():
    out = resolve_clip(make_clip(drop_ranges=[[8, 10]]), WORDS)
    assert [s["words"] for s in out["segments"]] == [[2, 7], [11, 20]]
    assert "m9" not in out["text"].split()


def test_out_of_bounds_is_clamped():
    out = resolve_clip(make_clip(end_word=999), WORDS)
    assert out["segments"][-1]["words"][1] == 39


def test_prompt_lines_cite_word_indices():
    text = transcript_for_prompt({"words": WORDS}, words_per_line=10)
    assert text.splitlines()[1].startswith("[w10-w19")
