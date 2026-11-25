# ReelsMachine

Une vidéo source → plusieurs Reels montés → **ta validation** → publication (IG, TikTok, Shorts, LinkedIn) → leads via le mot-clé en commentaire.

## Pipeline

| Étape | Module | État |
|---|---|---|
| 01 Ingestion + anti-doublon | `reels/ingest.py` | ✅ |
| 02 Transcription au mot (faster-whisper) | `reels/transcribe.py` | ✅ |
| 03 Edit plan : extraits, hooks, copy Gringo + LinkedIn (Claude) | `reels/plan.py` | ✅ |
| 04 Montage auto dans DaVinci Resolve (9:16 + 4:5) | `reels/resolve_build.py` | à venir |
| 05 Sous-titres mot à mot (overlay) | `reels/captions.py` | à venir |
| 06 Publication après validation | `reels/publish.py` | à venir |
| 07 Commentaire → DM → ressource | ManyChat (V1) | à venir |

Le LLM ne coupe jamais la vidéo : il renvoie des **indices de mots**, convertis ensuite en timecodes exacts.

## Installation (Mac)

```bash
brew install python@3.11 ffmpeg
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # puis colle ta clé ANTHROPIC_API_KEY
```

Le Python système de macOS (3.9) est trop ancien : utilise bien `python3.11`.

## Utilisation

```bash
python -m reels run ~/Videos/interview.mp4 --clips 4
```

Résultat dans `jobs/<date>-<nom>/` :
- `transcript.json` : mots horodatés
- `edit_plan.json` : extraits + timecodes + copy (machine)
- `edit_plan.md` : **la version à relire et valider**

Relancer seulement l'analyse : `python -m reels plan <nom-du-job> --clips 3`

## Réglages

- `config/brand.yaml` : ton, mot-clé (`CARTE`), lead magnet, CTA
- `config/platforms.yaml` : formats et durées par plateforme
- `prompts/select_clips.md` : consignes de sélection et d'écriture
