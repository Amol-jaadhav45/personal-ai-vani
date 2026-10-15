"""
tools/system_info.py
=====================
System monitoring — CPU, RAM, Disk, Battery, Uptime, Network.
"""

import psutil
import platform
import socket
from datetime import datetime, timedelta
from core.logger import get_logger

logger = get_logger(__name__)


def get_cpu_info() -> str:
    """Return CPU usage and core details."""
    try:
        usage = psutil.cpu_percent(interval=0.5)
        cores = psutil.cpu_count(logical=False) or "?"
        threads = psutil.cpu_count(logical=True) or "?"
        freq = psutil.cpu_freq()
        freq_str = f"{freq.current:.0f} MHz" if freq else "N/A"
        
        # CPU temperature (may not be available on all systems)
        bars = "█" * int(usage / 5) + "░" * (20 - int(usage / 5))
        
        return (
            f"🧠 **CPU Information**\n"
            f"├─ Usage: [{bars}] {usage}%\n"
            f"├─ Cores: {cores} physical / {threads} logical\n"
            f"├─ Frequency: {freq_str}\n"
            f"└─ Processor: {platform.processor() or 'N/A'}"
        )
    except Exception as exc:
        logger.error(f"CPU info error: {exc}")
        return f"❌ Error reading CPU info: {exc}"


def get_ram_info() -> str:
    """Return RAM usage details."""
    try:
        mem = psutil.virtual_memory()
        total_gb = mem.total / (1024 ** 3)
        used_gb  = mem.used  / (1024 ** 3)
        avail_gb = mem.available / (1024 ** 3)
        bars = "█" * int(mem.percent / 5) + "░" * (20 - int(mem.percent / 5))
        
        return (
            f"💾 **RAM Information**\n"
            f"├─ Usage: [{bars}] {mem.percent}%\n"
            f"├─ Used: {used_gb:.1f} GB / {total_gb:.1f} GB\n"
            f"└─ Available: {avail_gb:.1f} GB"
        )
    except Exception as exc:
        logger.error(f"RAM info error: {exc}")
        return f"❌ Error reading RAM info: {exc}"


def get_disk_info() -> str:
    """Return disk usage for all mounted drives."""
    try:
        lines = ["💽 **Disk Information**"]
        partitions = psutil.disk_partitions()
        for i, part in enumerate(partitions):
            try:
                usage = psutil.disk_usage(part.mountpoint)
                total_gb = usage.total / (1024 ** 3)
                used_gb  = usage.used  / (1024 ** 3)
                free_gb  = usage.free  / (1024 ** 3)
                bars = "█" * int(usage.percent / 5) + "░" * (20 - int(usage.percent / 5))
                prefix = "└─" if i == len(partitions) - 1 else "├─"
                lines.append(
                    f"{prefix} {part.device} [{bars}] {usage.percent}% "
                    f"({used_gb:.1f}/{total_gb:.1f} GB, {free_gb:.1f} GB free)"
                )
            except PermissionError:
                continue
        return "\n".join(lines) if len(lines) > 1 else "💽 No accessible drives found."
    except Exception as exc:
        logger.error(f"Disk info error: {exc}")
        return f"❌ Error reading disk info: {exc}"


def get_battery_info() -> str:
    """Return battery level and charging status."""
    try:
        battery = psutil.sensors_battery()
        if battery is None:
            return "🔌 **Battery:** Desktop PC — No battery detected (plugged in)."
        
        percent = battery.percent
        plugged = battery.power_plugged
        
        # Battery bar
        bars = "█" * int(percent / 5) + "░" * (20 - int(percent / 5))
        
        # Status icon
        if plugged:
            status = "⚡ Charging" if percent < 100 else "✅ Fully Charged"
        else:
            secs_left = battery.secsleft
            if secs_left > 0:
                hrs  = secs_left // 3600
                mins = (secs_left % 3600) // 60
                status = f"🔋 On Battery — {hrs}h {mins}m remaining"
            else:
                status = "🔋 On Battery"
        
        return (
            f"🔋 **Battery Information**\n"
            f"├─ Level: [{bars}] {percent}%\n"
            f"└─ Status: {status}"
        )
    except Exception as exc:
        logger.error(f"Battery info error: {exc}")
        return f"❌ Error reading battery info: {exc}"


def get_network_info() -> str:
    """Return network / WiFi status."""
    try:
        hostname = socket.gethostname()
        try:
            local_ip = socket.gethostbyname(hostname)
        except Exception:
            local_ip = "N/A"
        
        # Network interfaces
        net_io = psutil.net_io_counters()
        sent_mb = net_io.bytes_sent / (1024 ** 2)
        recv_mb = net_io.bytes_recv / (1024 ** 2)
        
        # Check internet connectivity
        connected = False
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=2)
            connected = True
        except OSError:
            pass
        
        status = "🟢 Connected" if connected else "🔴 Disconnected"
        
        return (
            f"🌐 **Network Information**\n"
            f"├─ Status: {status}\n"
            f"├─ Hostname: {hostname}\n"
            f"├─ Local IP: {local_ip}\n"
            f"├─ Data Sent: {sent_mb:.1f} MB\n"
            f"└─ Data Received: {recv_mb:.1f} MB"
        )
    except Exception as exc:
        logger.error(f"Network info error: {exc}")
        return f"❌ Error reading network info: {exc}"


def get_uptime_info() -> str:
    """Return system uptime."""
    try:
        boot = datetime.fromtimestamp(psutil.boot_time())
        uptime = datetime.now() - boot
        
        days  = uptime.days
        hours = uptime.seconds // 3600
        mins  = (uptime.seconds % 3600) // 60
        
        parts = []
        if days > 0:
            parts.append(f"{days} day{'s' if days > 1 else ''}")
        if hours > 0:
            parts.append(f"{hours} hour{'s' if hours > 1 else ''}")
        parts.append(f"{mins} minute{'s' if mins > 1 else ''}")
        
        return (
            f"⏱️ **System Uptime**\n"
            f"├─ Boot Time: {boot.strftime('%B %d, %Y at %I:%M %p')}\n"
            f"└─ Uptime: {', '.join(parts)}"
        )
    except Exception as exc:
        logger.error(f"Uptime info error: {exc}")
        return f"❌ Error reading uptime: {exc}"


def get_system_overview() -> str:
    """Return a complete JARVIS-style system overview."""
    try:
        uname = platform.uname()
        return (
            f"🖥️ **System Overview**\n"
            f"├─ OS: {uname.system} {uname.release} ({uname.version[:50]})\n"
            f"├─ Machine: {uname.machine}\n"
            f"├─ Computer: {uname.node}\n"
            f"└─ Python: {platform.python_version()}"
        )
    except Exception as exc:
        return f"❌ Error: {exc}"


# ── Main dispatcher ──────────────────────────────────────────────────────────

def get_system_info(info_type: str = "all") -> tuple:
    """
    Return system information based on requested type.
    
    Returns:
        (success: bool, message: str)
    """
    handlers = {
        "cpu":       get_cpu_info,
        "ram":       get_ram_info,
        "disk":      get_disk_info,
        "battery":   get_battery_info,
        "network":   get_network_info,
        "uptime":    get_uptime_info,
        "overview":  get_system_overview,
    }
    
    info_type = info_type.lower().strip()
    
    if info_type == "all":
        sections = [
            get_system_overview(),
            "",
            get_cpu_info(),
            "",
            get_ram_info(),
            "",
            get_disk_info(),
            "",
            get_battery_info(),
            "",
            get_network_info(),
            "",
            get_uptime_info(),
        ]
        return True, "\n".join(sections)
    
    handler = handlers.get(info_type)
    if handler:
        return True, handler()
    
    valid = ", ".join(list(handlers.keys()) + ["all"])
    return False, f"❌ Unknown system info type: '{info_type}'. Valid: {valid}"
