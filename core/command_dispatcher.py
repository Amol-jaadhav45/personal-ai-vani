"""
core/command_dispatcher.py
==========================
Routes an AI-generated action dict to the correct tool function.

The AI engine returns either:
  A) A plain text response  → display it directly
  B) A JSON action object   → this dispatcher executes the right tool

All tool results are returned as (success: bool, message: str) tuples.
Destructive actions (delete_file) pause and ask the GUI for confirmation
before executing — the dispatcher never deletes anything without consent.
"""

from typing import Tuple, Callable, Optional

from core.logger import get_logger
from tools import app_launcher, browser_web, screenshot, system_info, file_ops, youtube_player, spotify_player, python_executor, vision, web_scraper, search_engine, clipboard_ops, process_manager, media_controls

logger = get_logger(__name__)

# Actions that require user confirmation before running
DESTRUCTIVE_ACTIONS = {"delete_file"}


class CommandDispatcher:
    """
    Routes action dicts to the appropriate tool.

    Parameters
    ----------
    confirm_callback : callable, optional
        A function(message: str) -> bool that the dispatcher calls when it
        needs user confirmation for a destructive action.
        If not provided, destructive actions are blocked.
    """

    def __init__(self, confirm_callback: Optional[Callable[[str], bool]] = None):
        self._confirm = confirm_callback
        logger.info("CommandDispatcher initialised.")

    # ── Public dispatch method ────────────────────────────────────────────────

    def dispatch(self, action_dict: dict) -> Tuple[bool, str]:
        """
        Execute the action described by `action_dict`.

        Parameters
        ----------
        action_dict : dict
            Must contain 'action' key and optionally 'params'.

        Returns
        -------
        (success: bool, result_message: str)
        """
        action = action_dict.get("action", "").strip()
        params = action_dict.get("params", {}) or {}

        logger.info(f"Dispatching action: '{action}' with params: {params}")

        # ── Guard: confirm destructive actions ───────────────────────────────
        if action in DESTRUCTIVE_ACTIONS:
            target = params.get("path", "the selected item")
            if not self._request_confirmation(
                f"⚠️  Are you sure you want to DELETE:\n\n{target}\n\nThis cannot be undone."
            ):
                return False, "❌ Operation cancelled by user."

        # ── Route to the correct tool ─────────────────────────────────────────
        try:
            return self._route(action, params)
        except Exception as exc:
            msg = f"❌ Unexpected error in dispatcher: {exc}"
            logger.error(msg, exc_info=True)
            return False, msg

    # ── Routing table ─────────────────────────────────────────────────────────

    def _route(self, action: str, params: dict) -> Tuple[bool, str]:
        """Map action names to tool functions."""

        # App launcher
        if action == "open_app":
            app = params.get("app", "")
            if not app:
                return False, "❌ 'open_app' requires an 'app' parameter."
            return app_launcher.open_app(app)

        # Web / browser
        elif action == "web_search":
            query = params.get("query", "")
            return browser_web.web_search(query)

        elif action == "open_url":
            url = params.get("url", "")
            return browser_web.open_url(url)

        # YouTube playback
        elif action == "youtube_play":
            query = params.get("query", "")
            speed = float(params.get("speed", 1.0))
            quality = params.get("quality", "hd1080")
            return youtube_player.play_youtube_video(query, speed, quality)

        # Spotify playback
        elif action == "spotify_play":
            query = params.get("query", "")
            return spotify_player.play_spotify_song(query)

        # Screenshot
        elif action == "take_screenshot":
            return screenshot.take_screenshot()

        # System info
        elif action == "system_info":
            info_type = params.get("type", "all")
            return system_info.get_system_info(info_type)

        # File operations
        elif action == "list_files":
            path = params.get("path", "")
            if not path:
                return False, "❌ 'list_files' requires a 'path' parameter."
            return file_ops.list_files(path)

        elif action == "read_file":
            path = params.get("path", "")
            if not path:
                return False, "❌ 'read_file' requires a 'path' parameter."
            return file_ops.read_file(path)

        elif action == "create_folder":
            path = params.get("path", "")
            if not path:
                return False, "❌ 'create_folder' requires a 'path' parameter."
            return file_ops.create_folder(path)

        elif action == "write_file":
            path = params.get("path", "")
            content = params.get("content", "")
            if not path:
                return False, "❌ 'write_file' requires a 'path' parameter."
            return file_ops.write_file(path, content)

        elif action == "delete_file":
            path = params.get("path", "")
            if not path:
                return False, "❌ 'delete_file' requires a 'path' parameter."
            return file_ops.delete_file(path)

        elif action == "rename_file":
            path     = params.get("path", "")
            new_name = params.get("new_name", "")
            if not path or not new_name:
                return False, "❌ 'rename_file' requires 'path' and 'new_name' parameters."
            return file_ops.rename_file(path, new_name)

        elif action == "move_file":
            src  = params.get("src", "")
            dest = params.get("dest", "")
            if not src or not dest:
                return False, "❌ 'move_file' requires 'src' and 'dest' parameters."
            return file_ops.move_file(src, dest)
            
        elif action == "execute_python":
            code = params.get("code", "")
            if not code:
                return False, "❌ 'execute_python' requires a 'code' parameter."
            return python_executor.execute_python(code)
            
        elif action == "analyze_screen":
            query = params.get("query", "Describe what is on the screen in detail.")
            return vision.analyze_screen(query)
            
        elif action == "read_webpage":
            url = params.get("url", "")
            if not url:
                return False, "❌ 'read_webpage' requires a 'url' parameter."
            return web_scraper.read_webpage(url)
            
        elif action == "headless_search":
            query = params.get("query", "")
            if not query:
                return False, "❌ 'headless_search' requires a 'query' parameter."
            return search_engine.headless_search(query)
            
        elif action == "play_youtube":
            query = params.get("query", "")
            if not query:
                return False, "❌ 'play_youtube' requires a 'query' parameter."
            speed = params.get("speed", 1.0)
            quality = params.get("quality", "hd1080")
            return youtube_player.play_youtube_video(query, speed=speed, quality=quality)
            
        elif action == "play_spotify":
            query = params.get("query", "")
            if not query:
                return False, "❌ 'play_spotify' requires a 'query' parameter."
            return spotify_player.play_spotify_song(query)

        elif action == "media_control":
            cmd = params.get("command", "")
            return media_controls.media_control(cmd)
            
        elif action == "get_time":
            from datetime import datetime
            now = datetime.now()
            return True, f"🕕 Current date and time: {now.strftime('%A, %d %B %Y  —  %I:%M %p')}"

        elif action == "read_clipboard":
            return clipboard_ops.read_clipboard()
            
        elif action == "write_clipboard":
            text = params.get("text", "")
            return clipboard_ops.write_clipboard(text)
            
        elif action == "list_heavy_processes":
            return process_manager.get_heavy_processes()
            
        elif action == "kill_process":
            app = params.get("app", "")
            if not app:
                return False, "❌ 'kill_process' requires an 'app' parameter."
            if not self._request_confirmation(f"Are you sure you want to FORCE KILL {app}? Unsaved work may be lost."):
                return False, "User cancelled killing the process."
            return process_manager.kill_process(app)

        # Unknown action
        else:
            msg = f"❓ Unknown action: '{action}'. The AI may have made an error."
            logger.warning(msg)
            return False, msg

    # ── Confirmation helper ───────────────────────────────────────────────────

    def _request_confirmation(self, message: str) -> bool:
        """Return True if the user confirmed, False otherwise."""
        if self._confirm is None:
            logger.warning("Destructive action blocked: no confirm_callback set.")
            return False
        result = self._confirm(message)
        logger.info(f"User confirmation result: {result}")
        return result
