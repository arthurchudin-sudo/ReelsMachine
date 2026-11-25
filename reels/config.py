from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
JOBS_DIR = ROOT / "jobs"
PROMPTS_DIR = ROOT / "prompts"


def load_yaml(name: str) -> dict:
    return yaml.safe_load((ROOT / "config" / name).read_text(encoding="utf-8"))


def brand() -> dict:
    return load_yaml("brand.yaml")


def platforms() -> dict:
    return load_yaml("platforms.yaml")
