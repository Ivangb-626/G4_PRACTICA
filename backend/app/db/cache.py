from functools import lru_cache
import json
from pathlib import Path
from app.db.database import STATIC_CACHE

# Base path for game data
DATA_DIR = Path(__file__).resolve().parents[1] / "data"

@lru_cache(maxsize=128)
def get_static_data(filename):
    """
    Cached loader for static game data (techs, buildings, races).
    Reduces I/O overhead for high-frequency endpoints.
    """
    if filename not in STATIC_CACHE:
        file_path = DATA_DIR / f"{filename}.json"
        if file_path.exists():
            with open(file_path, "r", encoding="utf-8") as f:
                STATIC_CACHE[filename] = json.load(f)
    return STATIC_CACHE.get(filename)
