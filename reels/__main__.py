"""CLI : python -m reels <commande>"""
import argparse
from pathlib import Path

from dotenv import load_dotenv

from .config import JOBS_DIR


def main() -> None:
    load_dotenv()
    ap = argparse.ArgumentParser(prog="reels")
    sub = ap.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("run", help="01→03 : ingestion, transcription, edit plan")
    r.add_argument("video", type=Path)
    r.add_argument("--clips", type=int, default=4)
    r.add_argument("--copy", action="store_true", help="copier la source dans le job")
    r.add_argument("--whisper", default="large-v3")

    p = sub.add_parser("plan", help="relancer seulement l'edit plan d'un job existant")
    p.add_argument("job")
    p.add_argument("--clips", type=int, default=4)

    a = ap.parse_args()

    from . import plan, review
    if a.cmd == "run":
        from .ingest import ingest
        from .transcribe import transcribe
        job = ingest(a.video, copy=a.copy)
        print(f"[01] job créé : {job}")
        transcribe(job, model_size=a.whisper)
        print("[02] transcription OK")
    else:
        job = JOBS_DIR / a.job

    plan.plan(job, n_clips=a.clips)
    print(f"[03] edit plan → {review.render(job)}")


if __name__ == "__main__":
    main()
