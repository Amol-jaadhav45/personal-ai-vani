"""
tools/process_manager.py
========================
Process management for closing frozen apps and finding memory hogs.
Essential for Computer Science students and developers.
"""

import psutil
from typing import Tuple
from core.logger import get_logger

logger = get_logger(__name__)

def get_heavy_processes(limit: int = 5) -> Tuple[bool, str]:
    """Find the top processes consuming the most Memory and CPU."""
    try:
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'memory_info', 'cpu_percent']):
            try:
                # We need to call memory_info().rss
                memory_mb = proc.info['memory_info'].rss / (1024 * 1024)
                processes.append({
                    "name": proc.info['name'],
                    "pid": proc.info['pid'],
                    "memory_mb": memory_mb,
                    "cpu": proc.info['cpu_percent']
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        
        # Sort by memory descending
        processes.sort(key=lambda x: x['memory_mb'], reverse=True)
        top = processes[:limit]
        
        result_lines = [f"top {limit} RAM-heavy processes:"]
        for p in top:
            result_lines.append(f" - {p['name']} (PID: {p['pid']}) — {p['memory_mb']:.1f} MB RAM")
            
        logger.info("Fetched heavy processes.")
        return True, "\n".join(result_lines)
    except Exception as exc:
        msg = f"❌ Failed to get processes: {exc}"
        logger.error(msg)
        return False, msg

def kill_process(process_name: str) -> Tuple[bool, str]:
    """Kill an application/process by name (e.g., 'chrome.exe' or 'chrome')."""
    process_name = process_name.lower().strip()
    if not process_name.endswith(".exe"):
        process_name += ".exe"
        
    killed_count = 0
    try:
        for proc in psutil.process_iter(['name']):
            try:
                if proc.info['name'] and proc.info['name'].lower() == process_name:
                    proc.kill()
                    killed_count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
                
        if killed_count > 0:
            msg = f"✅ Killed {killed_count} instance(s) of {process_name}."
            logger.info(msg)
            return True, msg
        else:
            return False, f"⚠️ No running process found for '{process_name}'."
    except Exception as exc:
        msg = f"❌ Failed to kill {process_name}: {exc}"
        logger.error(msg)
        return False, msg
