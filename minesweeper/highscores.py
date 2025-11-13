
from __future__ import annotations
import json, time, os
from typing import Dict

FILE = os.path.join(os.path.expanduser("~"), ".minesweeper_highscores.json")

def _load() -> Dict:
    if not os.path.exists(FILE):
        return {}
    try:
        with open(FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def _save(data: Dict) -> None:
    try:
        with open(FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass

def _key(rows: int, cols: int, mines: int) -> str:
    return f"{rows}x{cols}:{mines}"

def submit_score(rows: int, cols: int, mines: int, name: str, elapsed: float) -> None:
    data = _load()
    k = _key(rows, cols, mines)
    data.setdefault(k, [])
    data[k].append({"name": name.strip()[:32] or "anon", "time": float(elapsed), "when": time.strftime("%Y-%m-%d")})
    data[k] = sorted(data[k], key=lambda s: s["time"])[:10]
    _save(data)

def get_top10(rows: int, cols: int, mines: int):
    data = _load()
    return data.get(_key(rows, cols, mines), [])
