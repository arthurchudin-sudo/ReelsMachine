"""01 — Ingestion : crée un job, refuse les doublons, extrait l'audio."""
import hashlib
import json
import re
import shutil
import subprocess
from datetime import date
from pathlib import Path

from .config import JOBS_DIR

INDEX = JOBS_DIR / "index.json"


def sha256(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while block := f.read(chunk):
            h.update(block)
    return h.hexdigest()


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:40] or "video"


def probe(path: Path) -> dict:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams", str(path)],
        check=True, capture_output=True, text=True,
    ).stdout
    data = json.loads(out)
    video = next((s for s in data["streams"] if s["codec_type"] == "video"), {})
    return {
        "duration": float(data["format"]["duration"]),
        "width": video.get("width"),
        "height": video.get("height"),
        "fps": video.get("r_frame_rate"),
    }


def _load_index() -> dict:
    return json.loads(INDEX.read_text()) if INDEX.exists() else {}


def ingest(source: Path, copy: bool = False) -> Path:
    """Crée jobs/<date>-<slug>/ et renvoie son chemin. Lève une erreur si la vidéo a déjà été traitée."""
    source = source.expanduser().resolve()
    if not source.exists():
        raise FileNotFoundError(source)

    digest = sha256(source)
    index = _load_index()
    if digest in index:
        raise ValueError(f"Vidéo déjà traitée : job {index[digest]} (anti-doublon)")

    job = JOBS_DIR / f"{date.today():%Y-%m-%d}-{slugify(source.stem)}"
    job.mkdir(parents=True, exist_ok=False)

    if copy:
        media = job / f"source{source.suffix.lower()}"
        shutil.copy2(source, media)
    else:
        media = source  # on évite de dupliquer des rushs lourds

    # Audio mono 16 kHz pour la transcription
    subprocess.run(
        ["ffmpeg", "-v", "error", "-y", "-i", str(media), "-vn", "-ac", "1", "-ar", "16000", str(job / "audio.wav")],
        check=True,
    )

    meta = {"source": str(media), "sha256": digest, **probe(media), "status": "ingested"}
    (job / "job.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False))

    index[digest] = job.name
    INDEX.write_text(json.dumps(index, indent=2))
    return job
