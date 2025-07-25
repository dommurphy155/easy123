import os
import json
import asyncio
from datetime import datetime, timezone

def load_json(filepath):
    if not os.path.exists(filepath):
        return None
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(filepath, data):
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def now_utc_iso():
    return datetime.now(timezone.utc).isoformat()

async def async_sleep(seconds):
    await asyncio.sleep(seconds)

def chunk_list(lst, n):
    """Split list into chunks of max size n."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]
