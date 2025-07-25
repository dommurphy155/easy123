import os
import json
import asyncio
from datetime import datetime, timezone
from typing import Any, List, Optional
import psutil



def load_json(filepath: str) -> Optional[Any]:
    if not os.path.exists(filepath):
        return None
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None

def save_json(filepath: str, data: Any) -> bool:
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        return True
    except IOError:
        return False

def now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

async def async_sleep(seconds: float) -> None:
    try:
        await asyncio.sleep(seconds)
    except asyncio.CancelledError:
        pass

def chunk_list(lst: List[Any], n: int) -> List[List[Any]]:
    if n <= 0:
        return [lst]
    return [lst[i:i + n] for i in range(0, len(lst), n)]

async def send_system_report() -> str:
    cpu_percent = psutil.cpu_percent(interval=1)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    net = psutil.net_io_counters()

    report = (
        f"📊 System Health Report:\n"
        f"CPU Usage: {cpu_percent}%\n"
        f"Memory Usage: {mem.percent}% ({mem.used // (1024**2)}MB used)\n"
        f"Disk Usage: {disk.percent}% ({disk.used // (1024**3)}GB used)\n"
        f"Network Sent: {net.bytes_sent // (1024**2)}MB\n"
        f"Network Received: {net.bytes_recv // (1024**2)}MB"
    )
    await asyncio.sleep(0)
    return report
