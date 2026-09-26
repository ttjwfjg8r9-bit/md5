import json
from pathlib import Path

STORAGE = Path("data.json")


def load_state():
    if not STORAGE.exists():
        return {
            "history": [],
            "stats": {"total": 0, "correct": 0, "wrong": 0},
            "last_session": None,
        }
    try:
        return json.loads(STORAGE.read_text(encoding="utf-8"))
    except Exception:
        return {
            "history": [],
            "stats": {"total": 0, "correct": 0, "wrong": 0},
            "last_session": None,
        }


def save_state(state):
    tmp = STORAGE.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(STORAGE)
