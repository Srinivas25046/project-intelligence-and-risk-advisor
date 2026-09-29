import json
import os

STORE_DIR = "output/insights"


def save_insight(name: str, data: dict):
    os.makedirs(STORE_DIR, exist_ok=True)
    path = os.path.join(STORE_DIR, f"{name}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def load_insight(name: str) -> dict:
    path = os.path.join(STORE_DIR, f"{name}.json")
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"No saved insight '{name}'. Run src.run_agents first to generate it."
        )
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)