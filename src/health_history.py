import json
import os
from datetime import datetime

HISTORY_PATH = "output/health_history.json"


def load_history() -> list:
    if not os.path.exists(HISTORY_PATH):
        return []
    try:
        with open(HISTORY_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def record_health(label: str, health: dict, n_risks: int, n_blockers: int) -> list:
    history = load_history()
    breakdown = health.get("breakdown", {})
    history.append({
        "run": len(history) + 1,
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "label": label,
        "overall": health.get("overall_health_score", 0),
        "scope_clarity": breakdown.get("scope_clarity", 0),
        "timeline_risk": breakdown.get("timeline_risk", 0),
        "blocker_load": breakdown.get("blocker_load", 0),
        "risks": n_risks,
        "blockers": n_blockers,
    })
    os.makedirs(os.path.dirname(HISTORY_PATH), exist_ok=True)
    with open(HISTORY_PATH, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)
    return history


def latest_delta(history: list):
    """Change in overall score versus the previous run, or None if < 2 runs."""
    if len(history) < 2:
        return None
    return history[-1]["overall"] - history[-2]["overall"]


def reset_history():
    """Called at the start of a fresh initial analysis so trends never mix runs
    from different document sets."""
    try:
        os.remove(HISTORY_PATH)
    except FileNotFoundError:
        pass