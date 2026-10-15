"""
tests/test_tools.py
====================
Unit tests for all tool modules.

Run with:
    py -m pytest tests/ -v
or without pytest:
    py tests/test_tools.py
"""

import sys
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Make sure the project root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


# =============================================================================
# File Operations Tests
# =============================================================================

class TestFileOps(unittest.TestCase):
    """Tests for tools/file_ops.py"""

    def setUp(self):
        """Create a temporary directory for each test."""
        self.tmp = tempfile.mkdtemp()
        self.tmp_path = Path(self.tmp)

    # ── list_files ────────────────────────────────────────────────────────────

    def test_list_files_empty_dir(self):
        from tools.file_ops import list_files
        ok, msg = list_files(self.tmp)
        self.assertTrue(ok)
        self.assertIn("empty", msg.lower())

    def test_list_files_with_content(self):
        from tools.file_ops import list_files
        (self.tmp_path / "hello.txt").write_text("hi")
        (self.tmp_path / "subdir").mkdir()
        ok, msg = list_files(self.tmp)
        self.assertTrue(ok)
        self.assertIn("hello.txt", msg)
        self.assertIn("subdir", msg)

    def test_list_files_nonexistent(self):
        from tools.file_ops import list_files
        ok, msg = list_files("/nonexistent/path/xyz")
        self.assertFalse(ok)
        self.assertIn("not exist", msg)

    # ── create_folder ─────────────────────────────────────────────────────────

    def test_create_folder(self):
        from tools.file_ops import create_folder
        target = str(self.tmp_path / "new_folder")
        ok, msg = create_folder(target)
        self.assertTrue(ok)
        self.assertTrue(Path(target).is_dir())

    def test_create_folder_nested(self):
        from tools.file_ops import create_folder
        target = str(self.tmp_path / "a" / "b" / "c")
        ok, msg = create_folder(target)
        self.assertTrue(ok)
        self.assertTrue(Path(target).is_dir())

    # ── write_file / read_file ────────────────────────────────────────────────

    def test_write_then_read_file(self):
        from tools.file_ops import write_file, read_file
        target = str(self.tmp_path / "test.txt")
        ok, msg = write_file(target, "Hello, Vani!")
        self.assertTrue(ok)

        ok2, content = read_file(target)
        self.assertTrue(ok2)
        self.assertIn("Hello, Vani!", content)

    def test_read_nonexistent_file(self):
        from tools.file_ops import read_file
        ok, msg = read_file("/nonexistent/file.txt")
        self.assertFalse(ok)
        self.assertIn("not found", msg)

    # ── rename_file ───────────────────────────────────────────────────────────

    def test_rename_file(self):
        from tools.file_ops import rename_file
        src = self.tmp_path / "old.txt"
        src.write_text("content")
        ok, msg = rename_file(str(src), "new.txt")
        self.assertTrue(ok)
        self.assertTrue((self.tmp_path / "new.txt").exists())
        self.assertFalse(src.exists())

    def test_rename_nonexistent(self):
        from tools.file_ops import rename_file
        ok, msg = rename_file("/no/such/file.txt", "renamed.txt")
        self.assertFalse(ok)

    # ── move_file ─────────────────────────────────────────────────────────────

    def test_move_file_into_dir(self):
        from tools.file_ops import move_file, create_folder
        src = self.tmp_path / "to_move.txt"
        src.write_text("data")
        dest_dir = self.tmp_path / "dest_folder"
        dest_dir.mkdir()

        ok, msg = move_file(str(src), str(dest_dir))
        self.assertTrue(ok)
        self.assertTrue((dest_dir / "to_move.txt").exists())

    # ── delete_file ───────────────────────────────────────────────────────────

    def test_delete_file(self):
        from tools.file_ops import delete_file
        f = self.tmp_path / "deleteme.txt"
        f.write_text("bye")
        ok, msg = delete_file(str(f))
        self.assertTrue(ok)
        self.assertFalse(f.exists())

    def test_delete_folder(self):
        from tools.file_ops import delete_file
        d = self.tmp_path / "deleteme_dir"
        d.mkdir()
        (d / "file.txt").write_text("inside")
        ok, msg = delete_file(str(d))
        self.assertTrue(ok)
        self.assertFalse(d.exists())

    def test_delete_nonexistent(self):
        from tools.file_ops import delete_file
        ok, msg = delete_file("/no/such/path")
        self.assertFalse(ok)


# =============================================================================
# Browser / Web Tests
# =============================================================================

class TestBrowserWeb(unittest.TestCase):
    """Tests for tools/browser_web.py"""

    @patch("webbrowser.open", return_value=True)
    def test_web_search(self, mock_open):
        from tools.browser_web import web_search
        ok, msg = web_search("Python tutorials")
        self.assertTrue(ok)
        self.assertIn("Python", msg)
        mock_open.assert_called_once()
        # URL should contain encoded query
        call_url = mock_open.call_args[0][0]
        self.assertIn("google.com/search", call_url)
        self.assertIn("Python", call_url.replace("+", " "))

    def test_web_search_empty(self):
        from tools.browser_web import web_search
        ok, msg = web_search("")
        self.assertFalse(ok)

    @patch("webbrowser.open", return_value=True)
    def test_open_url(self, mock_open):
        from tools.browser_web import open_url
        ok, msg = open_url("https://github.com")
        self.assertTrue(ok)
        mock_open.assert_called_with("https://github.com")

    @patch("webbrowser.open", return_value=True)
    def test_open_url_auto_https(self, mock_open):
        from tools.browser_web import open_url
        ok, msg = open_url("github.com")
        self.assertTrue(ok)
        call_url = mock_open.call_args[0][0]
        self.assertTrue(call_url.startswith("https://"))


# =============================================================================
# System Info Tests
# =============================================================================

class TestSystemInfo(unittest.TestCase):
    """Tests for tools/system_info.py"""

    def test_get_cpu_info(self):
        from tools.system_info import get_cpu_info
        result = get_cpu_info()
        self.assertIn("CPU", result)

    def test_get_ram_info(self):
        from tools.system_info import get_ram_info
        result = get_ram_info()
        self.assertIn("RAM", result)

    def test_get_disk_info(self):
        from tools.system_info import get_disk_info
        result = get_disk_info()
        self.assertIn("Disk", result)

    def test_get_battery_info(self):
        from tools.system_info import get_battery_info
        result = get_battery_info()
        self.assertIn("Batter", result)  # "Battery" or "battery"

    def test_get_network_info(self):
        from tools.system_info import get_network_info
        result = get_network_info()
        self.assertIn("Network", result)

    def test_get_uptime_info(self):
        from tools.system_info import get_uptime_info
        result = get_uptime_info()
        self.assertIn("Uptime", result)

    def test_system_info_all(self):
        from tools.system_info import get_system_info
        ok, msg = get_system_info("all")
        self.assertTrue(ok)
        self.assertIn("CPU", msg)
        self.assertIn("RAM", msg)

    def test_system_info_unknown_type(self):
        from tools.system_info import get_system_info
        ok, msg = get_system_info("invalid_type")
        self.assertFalse(ok)


# =============================================================================
# AI Engine Tests
# =============================================================================

class TestAIEngine(unittest.TestCase):
    """Tests for core/ai_engine.py"""

    def test_parse_action_valid_json(self):
        from core.ai_engine import AIEngine
        response = '{"action": "open_app", "params": {"app": "chrome"}}'
        result = AIEngine.parse_action(response)
        self.assertIsNotNone(result)
        self.assertEqual(result["action"], "open_app")
        self.assertEqual(result["params"]["app"], "chrome")

    def test_parse_action_plain_text(self):
        from core.ai_engine import AIEngine
        response = "Hello! I am Vani, how can I help?"
        result = AIEngine.parse_action(response)
        self.assertIsNone(result)

    def test_parse_action_markdown_wrapped(self):
        from core.ai_engine import AIEngine
        response = '```json\n{"action": "take_screenshot", "params": {}}\n```'
        result = AIEngine.parse_action(response)
        self.assertIsNotNone(result)
        self.assertEqual(result["action"], "take_screenshot")

    def test_fallback_hello(self):
        from core.ai_engine import AIEngine
        engine = AIEngine()  # no API key in test env
        response = engine._fallback_response("Hello!")
        self.assertIn("Vani", response)

    def test_fallback_open_chrome(self):
        from core.ai_engine import AIEngine
        import json
        engine = AIEngine()
        response = engine._fallback_response("open chrome")
        data = json.loads(response)
        self.assertEqual(data["action"], "open_app")
        self.assertEqual(data["params"]["app"], "chrome")

    def test_fallback_take_screenshot(self):
        from core.ai_engine import AIEngine
        import json
        engine = AIEngine()
        response = engine._fallback_response("take a screenshot")
        data = json.loads(response)
        self.assertEqual(data["action"], "take_screenshot")

    def test_fallback_get_time(self):
        from core.ai_engine import AIEngine
        import json
        engine = AIEngine()
        response = engine._fallback_response("what time is it?")
        data = json.loads(response)
        self.assertEqual(data["action"], "get_time")


# =============================================================================
# Memory (SQLite) Tests
# =============================================================================

class TestMemory(unittest.TestCase):
    """Tests for core/memory.py using a temporary database."""

    def setUp(self):
        from config import settings as s
        self.tmp_dir = tempfile.mkdtemp()
        # Override DB path for tests
        self._original_db = s.DB_PATH
        s.DB_PATH = Path(self.tmp_dir) / "test.db"

    def tearDown(self):
        from config import settings as s
        s.DB_PATH = self._original_db

    def test_new_session_and_messages(self):
        from core.memory import Memory
        mem = Memory()
        sid = mem.new_session("Test Chat")
        self.assertIsNotNone(sid)

        mem.save_message(sid, "user", "Hello")
        mem.save_message(sid, "assistant", "Hi there!")

        messages = mem.get_messages(sid)
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]["role"], "user")
        self.assertEqual(messages[0]["content"], "Hello")

    def test_get_all_sessions(self):
        from core.memory import Memory
        mem = Memory()
        mem.new_session("Session A")
        mem.new_session("Session B")
        sessions = mem.get_all_sessions()
        self.assertGreaterEqual(len(sessions), 2)

    def test_delete_session(self):
        from core.memory import Memory
        mem = Memory()
        sid = mem.new_session("To Delete")
        mem.save_message(sid, "user", "Bye")
        mem.delete_session(sid)
        msgs = mem.get_messages(sid)
        self.assertEqual(msgs, [])

    def test_update_title(self):
        from core.memory import Memory
        mem = Memory()
        sid = mem.new_session("Old Title")
        mem.update_session_title(sid, "New Title")
        sessions = {s["id"]: s for s in mem.get_all_sessions()}
        self.assertEqual(sessions[sid]["title"], "New Title")


# =============================================================================
# Command Dispatcher Tests
# =============================================================================

class TestCommandDispatcher(unittest.TestCase):
    """Tests for core/command_dispatcher.py"""

    def test_dispatch_unknown_action(self):
        from core.command_dispatcher import CommandDispatcher
        dispatcher = CommandDispatcher()
        ok, msg = dispatcher.dispatch({"action": "fly_to_moon", "params": {}})
        self.assertFalse(ok)
        self.assertIn("Unknown", msg)

    def test_dispatch_get_time(self):
        from core.command_dispatcher import CommandDispatcher
        dispatcher = CommandDispatcher()
        ok, msg = dispatcher.dispatch({"action": "get_time", "params": {}})
        self.assertTrue(ok)
        self.assertIn("date", msg.lower())

    def test_dispatch_system_info(self):
        from core.command_dispatcher import CommandDispatcher
        dispatcher = CommandDispatcher()
        ok, msg = dispatcher.dispatch({"action": "system_info", "params": {"type": "cpu"}})
        self.assertTrue(ok)
        self.assertIn("CPU", msg)

    def test_destructive_blocked_without_confirm(self):
        from core.command_dispatcher import CommandDispatcher
        dispatcher = CommandDispatcher(confirm_callback=None)
        ok, msg = dispatcher.dispatch({"action": "delete_file", "params": {"path": "/some/file"}})
        self.assertFalse(ok)
        self.assertIn("cancel", msg.lower())

    def test_destructive_confirmed(self):
        from core.command_dispatcher import CommandDispatcher
        import tempfile
        f = tempfile.NamedTemporaryFile(delete=False)
        f.close()

        dispatcher = CommandDispatcher(confirm_callback=lambda _: True)
        ok, msg = dispatcher.dispatch(
            {"action": "delete_file", "params": {"path": f.name}}
        )
        self.assertTrue(ok)
        self.assertFalse(Path(f.name).exists())


# =============================================================================
# Entry point
# =============================================================================

if __name__ == "__main__":
    unittest.main(verbosity=2)
