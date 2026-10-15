"""
core/memory.py
==============
Handles all SQLite database operations for storing conversation history.

Tables:
    conversations  – each chat session with a title and timestamp
    messages       – individual messages linked to a conversation
"""

import sqlite3
import uuid
from datetime import datetime
from typing import List, Dict, Optional

from config.settings import DB_PATH
from core.logger import get_logger
from core.rag_memory import RAGMemory

logger = get_logger(__name__)


class Memory:
    """
    Simple SQLite-backed conversation memory.

    Example usage:
        mem = Memory()
        session_id = mem.new_session("My first chat")
        mem.save_message(session_id, "user", "Hello!")
        mem.save_message(session_id, "assistant", "Hi there!")
        history = mem.get_messages(session_id)
    """

    def __init__(self):
        self._db_path = DB_PATH
        logger.info(f"Connecting to database: {self._db_path}")
        self._init_db()
        self._rag = RAGMemory()

    # ── Private helpers ───────────────────────────────────────────────────────

    def _connect(self) -> sqlite3.Connection:
        """Open a connection with row_factory for dict-like access."""
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")  # better concurrency
        return conn

    def _init_db(self):
        """Create tables if they don't already exist."""
        sql = """
        CREATE TABLE IF NOT EXISTS conversations (
            id          TEXT PRIMARY KEY,
            title       TEXT NOT NULL,
            created_at  TEXT NOT NULL,
            updated_at  TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS messages (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id TEXT NOT NULL REFERENCES conversations(id),
            role            TEXT NOT NULL CHECK(role IN ('user','assistant','system')),
            content         TEXT NOT NULL,
            timestamp       TEXT NOT NULL
        );
        """
        with self._connect() as conn:
            conn.executescript(sql)
        logger.debug("Database tables verified/created.")

    # ── Public API ────────────────────────────────────────────────────────────

    def new_session(self, title: str = "New Conversation") -> str:
        """Create a new conversation session and return its UUID."""
        session_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO conversations(id, title, created_at, updated_at) VALUES(?,?,?,?)",
                (session_id, title, now, now),
            )
        logger.info(f"New session created: {session_id} — '{title}'")
        return session_id

    def save_message(self, session_id: str, role: str, content: str):
        """Append a message to an existing session."""
        now = datetime.now().isoformat()
        inserted_id = None
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO messages(conversation_id, role, content, timestamp) VALUES(?,?,?,?)",
                (session_id, role, content, now),
            )
            inserted_id = cursor.lastrowid
            conn.execute(
                "UPDATE conversations SET updated_at=? WHERE id=?",
                (now, session_id),
            )
        logger.debug(f"Message saved [{role}]: {content[:60]}...")
        
        # Mirror to Long Term RAG Memory in background
        if inserted_id is not None:
             import threading
             threading.Thread(
                 target=self._rag.add_memory,
                 args=(session_id, role, content, f"{session_id}_{inserted_id}"),
                 daemon=True
             ).start()

    def get_messages(
        self, session_id: str, limit: int = 50
    ) -> List[Dict[str, str]]:
        """
        Retrieve the last `limit` messages for a session as a list of dicts
        compatible with the OpenAI chat format: [{"role": ..., "content": ...}].
        """
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT role, content FROM messages
                WHERE conversation_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (session_id, limit),
            ).fetchall()
        # Reverse so oldest is first (chronological order)
        return [{"role": r["role"], "content": r["content"]} for r in reversed(rows)]

    def get_all_sessions(self) -> List[Dict]:
        """Return a list of all conversation sessions."""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT id, title, created_at, updated_at FROM conversations ORDER BY updated_at DESC"
            ).fetchall()
        return [dict(r) for r in rows]

    def delete_session(self, session_id: str):
        """Delete a session and all its messages."""
        with self._connect() as conn:
            conn.execute("DELETE FROM messages WHERE conversation_id=?", (session_id,))
            conn.execute("DELETE FROM conversations WHERE id=?", (session_id,))
        logger.info(f"Session deleted: {session_id}")

    def update_session_title(self, session_id: str, title: str):
        """Rename a conversation session."""
        now = datetime.now().isoformat()
        with self._connect() as conn:
            conn.execute(
                "UPDATE conversations SET title=?, updated_at=? WHERE id=?",
                (title, now, session_id),
            )
            
    def search_rag(self, query: str) -> str:
        """Search long term memory and return a context string."""
        return self._rag.search(query, limit=5)
