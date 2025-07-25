import os
import json
import asyncio
from datetime import datetime, timezone
from typing import Any, List, Optional

def load_json(filepath: str) -> Optional[Any]:
    """Load a JSON file safely. Returns None if file doesn't exist or is invalid."""
    if not os.path.exists(filepath):
        return None
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None

def save_json(filepath: str, data: Any) -> bool:
    """Save data to a JSON file. Returns True if successful."""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        return True
    except IOError:
        return False

def now_utc_iso() -> str:
    """Return current UTC time in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat()

async def async_sleep(seconds: float) -> None:
    """Asynchronous sleep."""
    try:
        await asyncio.sleep(seconds)
    except asyncio.CancelledError:
        pass

def chunk_list(lst: List[Any], n: int) -> List[List[Any]]:
    """Split list into chunks of size n."""
    if n <= 0:
        return [lst]
    return [lst[i:i + n] for i in range(0, len(lst), n)]
