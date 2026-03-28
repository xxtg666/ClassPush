import sqlite3
import os
import shutil
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger("classpush.database")

DB_PATH = None


def get_db_path():
    global DB_PATH
    if DB_PATH is None:
        base_dir = Path(__file__).parent.parent
        DB_PATH = str(base_dir / "classpush.db")
    return DB_PATH


def get_connection():
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_database():
    db_path = get_db_path()
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                type        TEXT NOT NULL DEFAULT 'notice',
                sender      TEXT NOT NULL DEFAULT '老师',
                content     TEXT NOT NULL,
                status      TEXT DEFAULT 'active',
                duration_minutes INTEGER DEFAULT 0,
                hidden      INTEGER DEFAULT 0,
                scheduled_at TEXT,
                created_at  TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
                expired_at  TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key   TEXT PRIMARY KEY,
                value TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS senders (
                name       TEXT PRIMARY KEY,
                use_count  INTEGER DEFAULT 1,
                last_used  TEXT DEFAULT (datetime('now', 'localtime'))
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_messages_status ON messages(status)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_messages_created ON messages(created_at DESC)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_messages_scheduled ON messages(scheduled_at)
        """)

        conn.commit()
        conn.close()
        logger.info("Database initialized at %s", db_path)
    except sqlite3.DatabaseError as e:
        logger.error("Database corrupted: %s", e)
        backup_path = db_path + ".bak"
        if os.path.exists(db_path):
            shutil.copy2(db_path, backup_path)
            os.remove(db_path)
        conn = get_connection()
        conn.close()
        init_database()


def insert_message(msg_data: dict) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO messages (type, sender, content, status, duration_minutes, scheduled_at)
        VALUES (?, ?, ?, 'active', ?, ?)
    """,
        (
            msg_data.get("type", "notice"),
            msg_data.get("sender", "老师"),
            msg_data.get("content", ""),
            msg_data.get("duration_minutes", 0),
            msg_data.get("scheduled_at"),
        ),
    )
    msg_id = cursor.lastrowid
    conn.commit()

    sender_name = msg_data.get("sender", "老师")
    if sender_name:
        cursor.execute(
            """
            INSERT INTO senders (name, use_count, last_used)
            VALUES (?, 1, datetime('now', 'localtime'))
            ON CONFLICT(name) DO UPDATE SET use_count = use_count + 1, last_used = datetime('now', 'localtime')
        """,
            (sender_name,),
        )
        conn.commit()

    conn.close()
    logger.info(
        "Message inserted: id=%d, type=%s, sender=%s",
        msg_id,
        msg_data.get("type"),
        msg_data.get("sender"),
    )
    return msg_id


def get_messages(status="active", limit=20, offset=0) -> list:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT * FROM messages
        WHERE status = ? AND hidden = 0
        AND (duration_minutes = 0 OR datetime(created_at, '+' || duration_minutes || ' minutes') >= datetime('now', 'localtime'))
        ORDER BY created_at DESC
        LIMIT ? OFFSET ?
    """,
        (status, limit, offset),
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_all_messages(limit=50, offset=0) -> list:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT * FROM messages
        ORDER BY created_at DESC
        LIMIT ? OFFSET ?
    """,
        (limit, offset),
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_message_count(status="active") -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM messages WHERE status = ?", (status,))
    count = cursor.fetchone()[0]
    conn.close()
    return count


def hide_message(msg_id: int):
    conn = get_connection()
    conn.execute("UPDATE messages SET hidden = 1 WHERE id = ?", (msg_id,))
    conn.commit()
    conn.close()


def unhide_message(msg_id: int):
    conn = get_connection()
    conn.execute("UPDATE messages SET hidden = 0 WHERE id = ?", (msg_id,))
    conn.commit()
    conn.close()


def get_hidden_messages(limit=50) -> list:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM messages WHERE hidden = 1 ORDER BY created_at DESC LIMIT ?",
        (limit,),
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def unhide_all_messages():
    conn = get_connection()
    conn.execute("UPDATE messages SET hidden = 0 WHERE hidden = 1")
    conn.commit()
    conn.close()


def archive_message(msg_id: int):
    conn = get_connection()
    conn.execute("UPDATE messages SET status = 'archived' WHERE id = ?", (msg_id,))
    conn.commit()
    conn.close()


def delete_message(msg_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM messages WHERE id = ?", (msg_id,))
    conn.commit()
    conn.close()


def clear_all_messages():
    conn = get_connection()
    conn.execute("DELETE FROM messages")
    conn.commit()
    conn.close()


def get_active_count_no_hidden() -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """SELECT COUNT(*) FROM messages WHERE status = 'active' AND hidden = 0
        AND (duration_minutes = 0 OR datetime(created_at, '+' || duration_minutes || ' minutes') >= datetime('now', 'localtime'))"""
    )
    count = cursor.fetchone()[0]
    conn.close()
    return count


def get_senders(limit=10) -> list:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT name FROM senders ORDER BY use_count DESC, last_used DESC LIMIT ?",
        (limit,),
    )
    rows = cursor.fetchall()
    conn.close()
    return [row["name"] for row in rows]


def get_scheduled_messages() -> list:
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        """
        SELECT * FROM messages
        WHERE status = 'active' AND scheduled_at IS NOT NULL AND scheduled_at <= ?
        ORDER BY scheduled_at ASC
    """,
        (now,),
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def expire_old_messages(hours=24):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE messages SET status = 'archived'
        WHERE status = 'active'
        AND datetime(created_at, '+' || ? || ' hours') < datetime('now', 'localtime')
    """,
        (hours,),
    )
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    if affected > 0:
        logger.info("Expired %d old messages", affected)
