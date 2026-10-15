"""
tools/app_launcher.py
=====================
Opens common Windows applications by name.
Falls back to well-known default installation paths if the
app is not found on PATH.
"""

import os
import subprocess
from typing import Tuple

from config.settings import CHROME_PATH, VSCODE_PATH
from core.logger import get_logger

logger = get_logger(__name__)

# ── Known application paths (Windows defaults) ────────────────────────────────
_DEFAULT_PATHS = {
    # ── Browsers ──────────────────────────────────────────────────────────────
    "chrome": [
        CHROME_PATH,
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    ],
    "edge": [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ],
    "firefox": [
        r"C:\Program Files\Mozilla Firefox\firefox.exe",
        r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe",
    ],
    "brave": [
        r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
        r"C:\Users\{user}\AppData\Local\BraveSoftware\Brave-Browser\Application\brave.exe",
    ],
    "opera": [
        r"C:\Users\{user}\AppData\Local\Programs\Opera\launcher.exe",
        r"C:\Program Files\Opera\launcher.exe",
    ],
    "vivaldi": [
        r"C:\Users\{user}\AppData\Local\Vivaldi\Application\vivaldi.exe",
    ],
    "tor": [
        r"C:\Users\{user}\Desktop\Tor Browser\Browser\firefox.exe",
        r"C:\Program Files\Tor Browser\Browser\firefox.exe",
    ],
    # ── Code Editors / IDEs ───────────────────────────────────────────────────
    "vscode": [
        VSCODE_PATH,
        r"C:\Users\{user}\AppData\Local\Programs\Microsoft VS Code\Code.exe",
        r"C:\Program Files\Microsoft VS Code\Code.exe",
    ],
    "pycharm": [
        r"C:\Users\{user}\AppData\Local\Programs\PyCharm\bin\pycharm64.exe",
        r"C:\Program Files\JetBrains\PyCharm\bin\pycharm64.exe",
        r"C:\Program Files (x86)\JetBrains\PyCharm\bin\pycharm64.exe",
    ],
    "idea": [
        r"C:\Users\{user}\AppData\Local\Programs\IntelliJ IDEA\bin\idea64.exe",
        r"C:\Program Files\JetBrains\IntelliJ IDEA\bin\idea64.exe",
    ],
    "webstorm": [
        r"C:\Users\{user}\AppData\Local\Programs\WebStorm\bin\webstorm64.exe",
        r"C:\Program Files\JetBrains\WebStorm\bin\webstorm64.exe",
    ],
    "sublime": [
        r"C:\Program Files\Sublime Text\sublime_text.exe",
        r"C:\Program Files\Sublime Text 3\sublime_text.exe",
        r"C:\Program Files (x86)\Sublime Text 3\sublime_text.exe",
    ],
    "notepadpp": [
        r"C:\Program Files\Notepad++\notepad++.exe",
        r"C:\Program Files (x86)\Notepad++\notepad++.exe",
    ],
    "atom": [
        r"C:\Users\{user}\AppData\Local\atom\atom.exe",
        r"C:\Program Files\Atom\atom.exe",
    ],
    "androidstudio": [
        r"C:\Program Files\Android\Android Studio\bin\studio64.exe",
        r"C:\Users\{user}\AppData\Local\Programs\Android Studio\bin\studio64.exe",
    ],
    "eclipse": [
        r"C:\Eclipse\eclipse.exe",
        r"C:\Program Files\Eclipse\eclipse.exe",
    ],
    "anaconda": [
        r"C:\ProgramData\Anaconda3\Scripts\anaconda-navigator.exe",
        r"C:\Users\{user}\Anaconda3\Scripts\anaconda-navigator.exe",
        r"C:\Users\{user}\AppData\Local\Continuum\anaconda3\Scripts\anaconda-navigator.exe",
    ],
    # ── Microsoft Office ──────────────────────────────────────────────────────
    "word": [
        r"C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE",
        r"C:\Program Files (x86)\Microsoft Office\root\Office16\WINWORD.EXE",
        r"C:\Program Files\Microsoft Office\Office16\WINWORD.EXE",
    ],
    "excel": [
        r"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE",
        r"C:\Program Files (x86)\Microsoft Office\root\Office16\EXCEL.EXE",
        r"C:\Program Files\Microsoft Office\Office16\EXCEL.EXE",
    ],
    "powerpoint": [
        r"C:\Program Files\Microsoft Office\root\Office16\POWERPNT.EXE",
        r"C:\Program Files (x86)\Microsoft Office\root\Office16\POWERPNT.EXE",
        r"C:\Program Files\Microsoft Office\Office16\POWERPNT.EXE",
    ],
    "outlook": [
        r"C:\Program Files\Microsoft Office\root\Office16\OUTLOOK.EXE",
        r"C:\Program Files (x86)\Microsoft Office\root\Office16\OUTLOOK.EXE",
    ],
    "onenote": [
        r"C:\Program Files\Microsoft Office\root\Office16\ONENOTE.EXE",
        r"C:\Program Files (x86)\Microsoft Office\root\Office16\ONENOTE.EXE",
    ],
    "access": [
        r"C:\Program Files\Microsoft Office\root\Office16\MSACCESS.EXE",
        r"C:\Program Files (x86)\Microsoft Office\root\Office16\MSACCESS.EXE",
    ],
    "publisher": [
        r"C:\Program Files\Microsoft Office\root\Office16\MSPUB.EXE",
        r"C:\Program Files (x86)\Microsoft Office\root\Office16\MSPUB.EXE",
    ],
    # ── Communication ─────────────────────────────────────────────────────────
    "zoom": [
        r"C:\Users\{user}\AppData\Roaming\Zoom\bin\Zoom.exe",
        r"C:\Program Files\Zoom\bin\Zoom.exe",
        r"C:\Program Files (x86)\Zoom\bin\Zoom.exe",
    ],
    "teams": [
        r"C:\Users\{user}\AppData\Local\Microsoft\Teams\current\Teams.exe",
        r"C:\Program Files\Microsoft\Teams\current\Teams.exe",
        r"C:\Users\{user}\AppData\Local\Microsoft\WindowsApps\msteams.exe",
    ],
    "discord": [
        r"C:\Users\{user}\AppData\Roaming\Discord\Discord.exe",
        r"C:\Users\{user}\AppData\Local\Discord\Update.exe",
    ],
    "whatsapp": [
        r"C:\Users\{user}\AppData\Local\WhatsApp\WhatsApp.exe",
        r"C:\Users\{user}\AppData\Local\Microsoft\WindowsApps\WhatsApp.exe",
    ],
    "telegram": [
        r"C:\Users\{user}\AppData\Roaming\Telegram Desktop\Telegram.exe",
        r"C:\Users\{user}\AppData\Local\Telegram Desktop\Telegram.exe",
    ],
    "skype": [
        r"C:\Users\{user}\AppData\Roaming\Microsoft\Teams\current\Teams.exe",
        r"C:\Program Files (x86)\Microsoft\Skype for Desktop\Skype.exe",
        r"C:\Users\{user}\AppData\Local\Microsoft\WindowsApps\Skype.exe",
    ],
    "slack": [
        r"C:\Users\{user}\AppData\Local\slack\slack.exe",
        r"C:\Users\{user}\AppData\Roaming\Slack\slack.exe",
        r"C:\Program Files\Slack\slack.exe",
    ],
    "signal": [
        r"C:\Users\{user}\AppData\Local\Programs\signal-desktop\Signal.exe",
    ],
    "viber": [
        r"C:\Users\{user}\AppData\Local\Viber\Viber.exe",
    ],
    # ── Media & Entertainment ─────────────────────────────────────────────────
    "spotify": [
        r"C:\Users\{user}\AppData\Roaming\Spotify\Spotify.exe",
        r"C:\Users\{user}\AppData\Local\Microsoft\WindowsApps\Spotify.exe",
    ],
    "vlc": [
        r"C:\Program Files\VideoLAN\VLC\vlc.exe",
        r"C:\Program Files (x86)\VideoLAN\VLC\vlc.exe",
    ],
    "itunes": [
        r"C:\Program Files\iTunes\iTunes.exe",
        r"C:\Program Files (x86)\iTunes\iTunes.exe",
    ],
    "winamp": [
        r"C:\Program Files\Winamp\winamp.exe",
        r"C:\Program Files (x86)\Winamp\winamp.exe",
    ],
    "potplayer": [
        r"C:\Program Files\DAUM\PotPlayer\PotPlayerMini64.exe",
        r"C:\Program Files (x86)\DAUM\PotPlayer\PotPlayerMini.exe",
    ],
    "mpc": [
        r"C:\Program Files\MPC-HC\mpc-hc64.exe",
        r"C:\Program Files (x86)\MPC-HC\mpc-hc.exe",
    ],
    "netflix": [
        r"C:\Users\{user}\AppData\Local\Microsoft\WindowsApps\Netflix.exe",
    ],
    # ── Gaming ────────────────────────────────────────────────────────────────
    "steam": [
        r"C:\Program Files (x86)\Steam\steam.exe",
        r"C:\Program Files\Steam\steam.exe",
    ],
    "epic": [
        r"C:\Program Files (x86)\Epic Games\Launcher\Portal\Binaries\Win32\EpicGamesLauncher.exe",
        r"C:\Program Files\Epic Games\Launcher\Portal\Binaries\Win64\EpicGamesLauncher.exe",
    ],
    "gog": [
        r"C:\Program Files (x86)\GOG Galaxy\GalaxyClient.exe",
        r"C:\Program Files\GOG Galaxy\GalaxyClient.exe",
    ],
    "origin": [
        r"C:\Program Files (x86)\Origin\Origin.exe",
        r"C:\Program Files\Origin\Origin.exe",
    ],
    "ea": [
        r"C:\Program Files\Electronic Arts\EA Desktop\EA Desktop\EADesktop.exe",
    ],
    "uplay": [
        r"C:\Program Files (x86)\Ubisoft\Ubisoft Game Launcher\UbisoftGameLauncher.exe",
        r"C:\Program Files\Ubisoft\Ubisoft Game Launcher\UbisoftGameLauncher.exe",
    ],
    "battlenet": [
        r"C:\Program Files (x86)\Battle.net\Battle.net.exe",
        r"C:\Program Files\Battle.net\Battle.net.exe",
    ],
    "roblox": [
        r"C:\Users\{user}\AppData\Local\Roblox\Versions\RobloxPlayerLauncher.exe",
    ],
    "minecraft": [
        r"C:\Program Files (x86)\Minecraft Launcher\MinecraftLauncher.exe",
        r"C:\Users\{user}\AppData\Roaming\.minecraft\launcher\MinecraftLauncher.exe",
    ],
    # ── Design & Creative ─────────────────────────────────────────────────────
    "photoshop": [
        r"C:\Program Files\Adobe\Adobe Photoshop 2024\Photoshop.exe",
        r"C:\Program Files\Adobe\Adobe Photoshop 2023\Photoshop.exe",
        r"C:\Program Files\Adobe\Adobe Photoshop CC 2019\Photoshop.exe",
    ],
    "illustrator": [
        r"C:\Program Files\Adobe\Adobe Illustrator 2024\Support Files\Contents\Windows\Illustrator.exe",
        r"C:\Program Files\Adobe\Adobe Illustrator 2023\Support Files\Contents\Windows\Illustrator.exe",
    ],
    "premiere": [
        r"C:\Program Files\Adobe\Adobe Premiere Pro 2024\Adobe Premiere Pro.exe",
        r"C:\Program Files\Adobe\Adobe Premiere Pro 2023\Adobe Premiere Pro.exe",
    ],
    "aftereffects": [
        r"C:\Program Files\Adobe\Adobe After Effects 2024\Support Files\AfterFX.exe",
        r"C:\Program Files\Adobe\Adobe After Effects 2023\Support Files\AfterFX.exe",
    ],
    "lightroom": [
        r"C:\Program Files\Adobe\Adobe Lightroom Classic\lightroom.exe",
    ],
    "gimp": [
        r"C:\Program Files\GIMP 2\bin\gimp-2.10.exe",
        r"C:\Program Files (x86)\GIMP 2\bin\gimp-2.10.exe",
    ],
    "figma": [
        r"C:\Users\{user}\AppData\Local\Figma\Figma.exe",
    ],
    "blender": [
        r"C:\Program Files\Blender Foundation\Blender 3.6\blender.exe",
        r"C:\Program Files\Blender Foundation\Blender\blender.exe",
    ],
    "inkscape": [
        r"C:\Program Files\Inkscape\bin\inkscape.exe",
        r"C:\Program Files (x86)\Inkscape\inkscape.exe",
    ],
    "canva": [
        r"C:\Users\{user}\AppData\Local\Programs\Canva\Canva.exe",
    ],
    # ── Notes & Productivity ──────────────────────────────────────────────────
    "obsidian": [
        r"C:\Users\{user}\AppData\Local\Obsidian\Obsidian.exe",
    ],
    "notion": [
        r"C:\Users\{user}\AppData\Local\Programs\Notion\Notion.exe",
    ],
    "evernote": [
        r"C:\Users\{user}\AppData\Local\Programs\Evernote\Evernote.exe",
    ],
    "trello": [
        r"C:\Users\{user}\AppData\Local\Programs\trello\Trello.exe",
    ],
    "todoist": [
        r"C:\Users\{user}\AppData\Local\Programs\todoist\Todoist.exe",
    ],
    # ── Download & File Managers ──────────────────────────────────────────────
    "idm": [
        r"C:\Program Files (x86)\Internet Download Manager\IDMan.exe",
        r"C:\Program Files\Internet Download Manager\IDMan.exe",
    ],
    "utorrent": [
        r"C:\Users\{user}\AppData\Roaming\uTorrent\uTorrent.exe",
    ],
    "qbittorrent": [
        r"C:\Program Files\qBittorrent\qbittorrent.exe",
        r"C:\Program Files (x86)\qBittorrent\qbittorrent.exe",
    ],
    "7zip": [
        r"C:\Program Files\7-Zip\7zFM.exe",
        r"C:\Program Files (x86)\7-Zip\7zFM.exe",
    ],
    "winrar": [
        r"C:\Program Files\WinRAR\WinRAR.exe",
        r"C:\Program Files (x86)\WinRAR\WinRAR.exe",
    ],
    "totalcommander": [
        r"C:\Program Files\totalcmd\TOTALCMD64.EXE",
        r"C:\totalcmd\TOTALCMD64.EXE",
    ],
    # ── Security ──────────────────────────────────────────────────────────────
    "malwarebytes": [
        r"C:\Program Files\Malwarebytes\Anti-Malware\mbamgui.exe",
    ],
    "avast": [
        r"C:\Program Files\AVAST Software\Avast\AvastUI.exe",
    ],
    "kaspersky": [
        r"C:\Program Files (x86)\Kaspersky Lab\Kaspersky Total Security 21.0\avp.exe",
    ],
    # ── Other Popular Apps ────────────────────────────────────────────────────
    "anydesk": [
        r"C:\Program Files (x86)\AnyDesk\AnyDesk.exe",
        r"C:\Program Files\AnyDesk\AnyDesk.exe",
        r"C:\Users\{user}\AppData\Roaming\AnyDesk\AnyDesk.exe",
    ],
    "teamviewer": [
        r"C:\Program Files\TeamViewer\TeamViewer.exe",
        r"C:\Program Files (x86)\TeamViewer\TeamViewer.exe",
    ],
    "bitwarden": [
        r"C:\Users\{user}\AppData\Local\Programs\bitwarden\Bitwarden.exe",
    ],
    "keepass": [
        r"C:\Program Files\KeePass Password Safe 2\KeePass.exe",
        r"C:\Program Files (x86)\KeePass Password Safe 2\KeePass.exe",
    ],
    "putty": [
        r"C:\Program Files\PuTTY\putty.exe",
        r"C:\Program Files (x86)\PuTTY\putty.exe",
    ],
    "winscp": [
        r"C:\Program Files (x86)\WinSCP\WinSCP.exe",
        r"C:\Program Files\WinSCP\WinSCP.exe",
    ],
    "postman": [
        r"C:\Users\{user}\AppData\Local\Postman\Postman.exe",
    ],
    "dbeaver": [
        r"C:\Program Files\DBeaver\dbeaver.exe",
        r"C:\Users\{user}\AppData\Local\DBeaverCE\dbeaver.exe",
    ],
    "docker": [
        r"C:\Program Files\Docker\Docker\Docker Desktop.exe",
    ],
    "virtualbox": [
        r"C:\Program Files\Oracle\VirtualBox\VirtualBox.exe",
    ],
    "vmware": [
        r"C:\Program Files (x86)\VMware\VMware Workstation\vmware.exe",
        r"C:\Program Files\VMware\VMware Workstation\vmware.exe",
    ],
    "obs": [
        r"C:\Program Files\obs-studio\bin\64bit\obs64.exe",
        r"C:\Program Files (x86)\obs-studio\bin\32bit\obs32.exe",
    ],
    "audacity": [
        r"C:\Program Files\Audacity\Audacity.exe",
        r"C:\Program Files (x86)\Audacity\Audacity.exe",
    ],
    "handbrake": [
        r"C:\Program Files\HandBrake\HandBrake.exe",
    ],
    "winmerge": [
        r"C:\Program Files\WinMerge\WinMergeU.exe",
        r"C:\Program Files (x86)\WinMerge\WinMergeU.exe",
    ],
}

# Simple apps that Windows can resolve by name / registry
_SIMPLE_APPS = {
    "notepad":       "notepad.exe",
    "calculator":    "calc.exe",
    "paint":         "mspaint.exe",
    "explorer":      "explorer.exe",
    "wordpad":       "wordpad.exe",
    "cmd":           "cmd.exe",
    "powershell":    "powershell.exe",
    "taskmgr":       "taskmgr.exe",
    "control":       "control.exe",
    "regedit":       "regedit.exe",
    "snippingtool":  "SnippingTool.exe",
    "mspaint":       "mspaint.exe",
    "msedge":        "msedge.exe",
    "mmc":           "mmc.exe",           # Management Console
    "services":      "services.msc",      # Windows Services
    "devmgmt":       "devmgmt.msc",       # Device Manager
    "diskmgmt":      "diskmgmt.msc",      # Disk Management
    "eventvwr":      "eventvwr.msc",      # Event Viewer
    "perfmon":       "perfmon.exe",       # Performance Monitor
    "resmon":        "resmon.exe",        # Resource Monitor
    "certmgr":       "certmgr.msc",      # Certificate Manager
    "wt":            "wt.exe",            # Windows Terminal
    "terminal":      "wt.exe",
    "winword":       "winword.exe",
    "excel":         "excel.exe",
}




def open_app(app_name: str) -> Tuple[bool, str]:
    """
    Open a named application.

    Parameters
    ----------
    app_name : str
        Case-insensitive application key, e.g. 'chrome', 'notepad'.

    Returns
    -------
    (success: bool, message: str)
    """
    name = app_name.lower().strip()
    logger.info(f"Attempting to open application: '{name}'")

    # ── Simple Windows built-in apps ──────────────────────────────────────────
    if name in _SIMPLE_APPS:
        exe = _SIMPLE_APPS[name]
        try:
            subprocess.Popen([exe], shell=True)
            msg = f"✅ Opened {name.capitalize()} successfully."
            logger.info(msg)
            return True, msg
        except Exception as exc:
            msg = f"❌ Failed to open {name}: {exc}"
            logger.error(msg)
            return False, msg

    # ── Apps that need path resolution ────────────────────────────────────────
    if name in _DEFAULT_PATHS:
        username = os.environ.get("USERNAME", "")
        for path in _DEFAULT_PATHS[name]:
            if not path:
                continue
            resolved = path.replace("{user}", username)
            if os.path.isfile(resolved):
                try:
                    os.startfile(resolved)
                    msg = f"✅ Opened {name.capitalize()} successfully."
                    logger.info(msg)
                    return True, msg
                except Exception as exc:
                    logger.warning(f"Path {resolved} failed: {exc}")

        msg = (
            f"❌ Could not find {name.capitalize()}. "
            f"Please set its path in the .env file (e.g. CHROME_PATH=...)."
        )
        logger.warning(msg)
        return False, msg

    # ── Last-resort: try several generic Windows launch strategies ─────────────
    # Strategy 1: Windows 'start' command (opens registered shell associations)
    try:
        result = subprocess.run(
            f'start "" "{name}"',
            shell=True,
            timeout=3,
            capture_output=True,
        )
        if result.returncode == 0:
            msg = f"✅ Opened '{name}' successfully."
            logger.info(msg)
            return True, msg
    except Exception:
        pass

    # Strategy 2: Try appending .exe and running directly
    try:
        exe_name = name if name.endswith(".exe") else f"{name}.exe"
        subprocess.Popen([exe_name], shell=True)
        msg = f"✅ Attempted to launch '{name}'."
        logger.info(msg)
        return True, msg
    except Exception:
        pass

    # Strategy 3: Open via Windows shell 'explorer' (works for UWP / Store apps)
    try:
        os.startfile(name)
        msg = f"✅ Attempted to open '{name}' via shell."
        logger.info(msg)
        return True, msg
    except Exception as exc:
        msg = (
            f"❌ Could not open '{name}'. "
            f"Make sure it is installed. Error: {exc}"
        )
        logger.error(msg)
        return False, msg
