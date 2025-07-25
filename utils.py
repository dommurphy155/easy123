import psutil
import asyncio

async def send_system_report() -> str:
    """
    Collects and returns a system health report as a formatted string.
    Includes CPU, memory, disk, and network stats.
    """
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        net = psutil.net_io_counters()

        report = (
            f"📊 System Health Report:\n"
            f"🧠 CPU Usage: {cpu_percent}%\n"
            f"📈 Memory Usage: {mem.percent}% ({mem.used // (1024**2)}MB used)\n"
            f"💾 Disk Usage: {disk.percent}% ({disk.used // (1024**3)}GB used)\n"
            f"📤 Network Sent: {net.bytes_sent // (1024**2)}MB\n"
            f"📥 Network Received: {net.bytes_recv // (1024**2)}MB"
        )
    except Exception as e:
        report = f"⚠️ Failed to generate system health report: {e}"

    await asyncio.sleep(0)  # async safety
    return report
