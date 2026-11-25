"""02 — Transcription au mot près (faster-whisper)."""
import json
from pathlib import Path


def transcribe(job: Path, model_size: str = "large-v3", language: str = "fr") -> Path:
    from faster_whisper import WhisperModel  # import lourd, chargé à la demande

    model = WhisperModel(model_size, device="auto", compute_type="int8")
    segments, info = model.transcribe(
        str(job / "audio.wav"),
        language=language,
        word_timestamps=True,
        vad_filter=True,
    )

    words, segs = [], []
    for seg in segments:
        segs.append({"start": round(seg.start, 2), "end": round(seg.end, 2), "text": seg.text.strip()})
        for w in seg.words or []:
            words.append({"i": len(words), "start": round(w.start, 3), "end": round(w.end, 3),
                          "word": w.word.strip(), "p": round(w.probability, 3)})

    out = job / "transcript.json"
    out.write_text(json.dumps({"language": info.language, "segments": segs, "words": words},
                              indent=1, ensure_ascii=False))
    return out
