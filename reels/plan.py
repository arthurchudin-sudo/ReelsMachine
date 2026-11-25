"""03 — Edit plan : Claude choisit les extraits et rédige hooks + copy.

Le LLM ne touche jamais la vidéo. Il renvoie des indices de mots ; on les
convertit nous-mêmes en timecodes exacts à partir du transcript.
"""
import json
from pathlib import Path
from typing import Literal

import anthropic
from pydantic import BaseModel, Field

from .config import PROMPTS_DIR, brand, platforms

MODEL = "claude-opus-5-5"


# ---------- Schéma de sortie ----------
class Cue(BaseModel):
    word_index: int
    kind: Literal["whoosh", "pop", "riser", "hit", "zoom_in", "zoom_out"]


class GringoCopy(BaseModel):
    caption: str = Field(description="Description à forte valeur : points clés actionnables, 600-1200 caractères")
    cta: str
    hashtags: list[str]


class LinkedInCopy(BaseModel):
    post: str = Field(description="Post LinkedIn ton expert, structure mini étude de cas, 800-1500 caractères")
    cta: str


class Clip(BaseModel):
    title: str = Field(description="Nom interne court")
    start_word: int
    end_word: int
    drop_ranges: list[list[int]] = Field(
        default_factory=list, description="Plages [début, fin] d'indices de mots à retirer (digressions, redites)")
    hook_text: str = Field(description="Texte d'accroche à l'écran, 3 à 8 mots")
    why: str = Field(description="Pourquoi cet extrait va performer, en une phrase")
    score: int = Field(ge=1, le=10)
    emphasis_words: list[int] = Field(description="Indices des mots à mettre en couleur dans les sous-titres")
    cues: list[Cue]
    broll_ideas: list[str]
    gringo: GringoCopy
    linkedin: LinkedInCopy


class EditPlan(BaseModel):
    summary: str
    clips: list[Clip]


# ---------- Préparation du transcript ----------
def transcript_for_prompt(transcript: dict, words_per_line: int = 12) -> str:
    """Lignes compactes « [w120-w131 | 45.2s] texte » pour que le LLM cite des indices."""
    words = transcript["words"]
    lines = []
    for k in range(0, len(words), words_per_line):
        chunk = words[k:k + words_per_line]
        lines.append(f"[w{chunk[0]['i']}-w{chunk[-1]['i']} | {chunk[0]['start']:.1f}s] "
                     + " ".join(w["word"] for w in chunk))
    return "\n".join(lines)


def build_prompt(transcript: dict, n_clips: int) -> tuple[str, str]:
    b, p = brand(), platforms()
    tones = b["tones"]
    system = (PROMPTS_DIR / "select_clips.md").read_text(encoding="utf-8").format(
        brand=b["brand"], positioning=b["positioning"].strip(), audience=b["audience"],
        gringo=tones["gringo"]["description"], pro=tones["pro"]["description"],
        cta_gringo=tones["gringo"]["cta"].format(keyword=b["keyword"], lead_name=b["lead_magnet"]["name"]),
        cta_pro=tones["pro"]["cta"].format(keyword=b["keyword"], lead_name=b["lead_magnet"]["name"]),
        short_min=p["instagram"]["min_s"], short_max=p["instagram"]["max_s"],
        li_min=p["linkedin"]["min_s"], li_max=p["linkedin"]["max_s"],
    )
    user = f"Propose les {n_clips} meilleurs extraits.\n\nTRANSCRIPT :\n{transcript_for_prompt(transcript)}"
    return system, user


# ---------- Validation / conversion en timecodes ----------
def resolve_clip(clip: Clip, words: list[dict], pad: float = 0.12) -> dict:
    n = len(words)
    s, e = max(0, clip.start_word), min(n - 1, clip.end_word)
    if s >= e:
        raise ValueError(f"Extrait « {clip.title} » invalide : start_word >= end_word")

    keep = [(s, e)]
    for a, b in sorted(clip.drop_ranges):
        a, b = max(a, s), min(b, e)
        if a > b:
            continue
        new = []
        for ks, ke in keep:
            if b < ks or a > ke:
                new.append((ks, ke))
                continue
            if ks < a:
                new.append((ks, a - 1))
            if b < ke:
                new.append((b + 1, ke))
        keep = new

    segments = [{"start": round(max(0, words[a]["start"] - pad), 3),
                 "end": round(words[b]["end"] + pad, 3),
                 "words": [a, b]} for a, b in keep]
    duration = round(sum(x["end"] - x["start"] for x in segments), 2)
    text = " ".join(words[i]["word"] for a, b in keep for i in range(a, b + 1))
    return {**clip.model_dump(), "segments": segments, "duration": duration, "text": text}


def plan(job: Path, n_clips: int = 4, effort: str = "high") -> Path:
    transcript = json.loads((job / "transcript.json").read_text())
    system, user = build_prompt(transcript, n_clips)

    client = anthropic.Anthropic()
    response = client.messages.parse(
        model=MODEL,
        max_tokens=16000,
        system=system,
        messages=[{"role": "user", "content": user}],
        output_config={"effort": effort},
        output_format=EditPlan,
    )
    if response.stop_reason == "refusal":
        raise RuntimeError(f"Claude a refusé la requête : {response.stop_details}")
    if response.stop_reason == "max_tokens":
        raise RuntimeError("Réponse tronquée (max_tokens) : réduis n_clips")

    edit_plan: EditPlan = response.parsed_output
    words = transcript["words"]
    clips = [resolve_clip(c, words) for c in edit_plan.clips]

    out = job / "edit_plan.json"
    out.write_text(json.dumps({"model": MODEL, "summary": edit_plan.summary, "clips": clips,
                               "usage": response.usage.model_dump()}, indent=2, ensure_ascii=False))
    return out
