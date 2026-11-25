"""Rendu lisible de l'edit plan pour la validation humaine."""
import json
from pathlib import Path


def tc(seconds: float) -> str:
    m, s = divmod(seconds, 60)
    return f"{int(m):02d}:{s:05.2f}"


def render(job: Path) -> Path:
    data = json.loads((job / "edit_plan.json").read_text())
    lines = [f"# Edit plan — {job.name}", "", data["summary"], ""]
    for n, c in enumerate(sorted(data["clips"], key=lambda c: -c["score"]), 1):
        segs = ", ".join(f"{tc(s['start'])} → {tc(s['end'])}" for s in c["segments"])
        lines += [
            f"## {n}. {c['title']}  ·  score {c['score']}/10  ·  {c['duration']} s",
            f"**Hook écran :** {c['hook_text']}",
            f"**Pourquoi :** {c['why']}",
            f"**Coupes :** {segs}",
            "", f"> {c['text']}", "",
            "### Version Gringo (IG / TikTok / Shorts)", c["gringo"]["caption"], "", c["gringo"]["cta"],
            " ".join("#" + h.lstrip("#") for h in c["gringo"]["hashtags"]), "",
            "### Version LinkedIn", c["linkedin"]["post"], "", c["linkedin"]["cta"], "",
            "---", "",
        ]
    out = job / "edit_plan.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    return out
