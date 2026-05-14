"""
SQLite Database — Chat History Persistence

Uses Python's built-in sqlite3 module (zero extra dependencies).
Database file: chat_history.db (auto-created on first startup in backend dir)

Schema:
  conversations  — one row per conversation session
  messages       — all messages across all conversations
"""

import os
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone

DB_PATH = os.path.join(os.path.dirname(__file__), "chat_history.db")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@contextmanager
def get_db():
    """
    Context manager for SQLite connections.
    - Enables WAL mode for better concurrent read performance.
    - Rows returned as dict-like objects via row_factory.
    - Auto-commits on success, rolls back on exception.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    """
    Create tables if they don't exist.
    Called once on application startup — safe to call multiple times.
    """
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS conversations (
                id          TEXT PRIMARY KEY,
                title       TEXT NOT NULL,
                created_at  TEXT NOT NULL,
                updated_at  TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS messages (
                id               TEXT PRIMARY KEY,
                conversation_id  TEXT NOT NULL,
                role             TEXT NOT NULL,    -- 'user' | 'assistant'
                content          TEXT NOT NULL,
                intent           TEXT,             -- insight: populated on assistant rows
                sentiment        TEXT,             -- insight: populated on assistant rows
                created_at       TEXT NOT NULL,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id)
            );
        """)


# ── Conversation operations ────────────────────────────────────────────────────

def create_conversation(title: str) -> dict:
    """Create a new conversation. Title is derived from the first user message."""
    conv_id = str(uuid.uuid4())
    now = _utc_now()
    # Trim and sanitize title
    safe_title = title.strip()[:80] or "New Conversation"
    with get_db() as conn:
        conn.execute(
            "INSERT INTO conversations (id, title, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (conv_id, safe_title, now, now),
        )
    return {"id": conv_id, "title": safe_title, "created_at": now, "updated_at": now}


def list_conversations() -> list[dict]:
    """Return all conversations, most recently updated first."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, title, created_at, updated_at "
            "FROM conversations ORDER BY updated_at DESC"
        ).fetchall()
    return [dict(row) for row in rows]


def touch_conversation(conversation_id: str) -> None:
    """Bump updated_at so the conversation floats to the top of the list."""
    with get_db() as conn:
        conn.execute(
            "UPDATE conversations SET updated_at = ? WHERE id = ?",
            (_utc_now(), conversation_id),
        )


def delete_conversation(conversation_id: str) -> None:
    """Delete a conversation and cascade-delete all its messages."""
    with get_db() as conn:
        conn.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation_id,))
        conn.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))


# ── Message operations ─────────────────────────────────────────────────────────

def save_message(
    conversation_id: str,
    role: str,
    content: str,
    intent: str | None = None,
    sentiment: str | None = None,
) -> dict:
    """Persist a single message. intent/sentiment only set on assistant rows."""
    msg_id = str(uuid.uuid4())
    now = _utc_now()
    with get_db() as conn:
        conn.execute(
            "INSERT INTO messages (id, conversation_id, role, content, intent, sentiment, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (msg_id, conversation_id, role, content, intent, sentiment, now),
        )
    return {
        "id": msg_id,
        "conversation_id": conversation_id,
        "role": role,
        "content": content,
        "intent": intent,
        "sentiment": sentiment,
        "created_at": now,
    }


# def update_message_insights(message_id: str, intent: str, sentiment: str) -> None:
#     """
#     Example of an alternative (slower) approach: Updating the user's message row.
#     Avoided in our architecture to stick to fast insert-only workloads.
#     """
#     with get_db() as conn:
#         conn.execute(
#             "UPDATE messages SET intent = ?, sentiment = ? WHERE id = ?",
#             (intent, sentiment, message_id),
#         )


def get_messages_for_conversation(conversation_id: str) -> list[dict]:
    """Return all messages for a conversation in chronological order."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, conversation_id, role, content, intent, sentiment, created_at "
            "FROM messages WHERE conversation_id = ? ORDER BY created_at ASC",
            (conversation_id,),
        ).fetchall()
    return [dict(row) for row in rows]
