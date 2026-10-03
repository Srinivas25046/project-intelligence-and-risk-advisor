import json
import os
import hashlib

MANIFEST_PATH = "output/ingestion_manifest.json"


def _file_hash(filepath: str) -> str:
    with open(filepath, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()[:12]


def load_manifest() -> dict:
    if not os.path.exists(MANIFEST_PATH):
        return {}
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_manifest(manifest: dict):
    os.makedirs(os.path.dirname(MANIFEST_PATH), exist_ok=True)
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)


def get_new_or_changed_files(raw_dir: str) -> list[str]:
    manifest = load_manifest()
    new_or_changed = []
    for filename in os.listdir(raw_dir):
        filepath = os.path.join(raw_dir, filename)
        if not os.path.isfile(filepath):
            continue
        current_hash = _file_hash(filepath)
        if manifest.get(filename) != current_hash:
            new_or_changed.append(filename)
    return new_or_changed


def mark_ingested(raw_dir: str, filenames: list[str]):
    manifest = load_manifest()
    for filename in filenames:
        filepath = os.path.join(raw_dir, filename)
        manifest[filename] = _file_hash(filepath)
    save_manifest(manifest)


LAST_BATCH_PATH = "output/last_batch.json"


def save_last_batch(filenames: list[str]):
    """
    Records which files were added in the most recent ingestion batch
    (initial or incremental), so agents can guarantee ALL of them are
    considered — not just the single most-recently-modified file.
    """
    os.makedirs(os.path.dirname(LAST_BATCH_PATH), exist_ok=True)
    with open(LAST_BATCH_PATH, "w", encoding="utf-8") as f:
        json.dump(filenames, f, indent=2)


def load_last_batch() -> list[str]:
    if not os.path.exists(LAST_BATCH_PATH):
        return []
    with open(LAST_BATCH_PATH, "r", encoding="utf-8") as f:
        return json.load(f)