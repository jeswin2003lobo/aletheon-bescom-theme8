import sqlite3
import os
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

FEEDBACK_DB_PATH = Path(os.environ.get("FEEDBACK_DB_PATH", "./aletheon_feedback.db"))


def _get_conn():
    conn = sqlite3.connect(str(FEEDBACK_DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = _get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS field_feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id TEXT NOT NULL,
            meter_id_hash TEXT NOT NULL,
            inspector_id TEXT,
            feedback_type TEXT NOT NULL,
            finding TEXT NOT NULL,
            notes TEXT,
            photo_reference TEXT,
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


init_db()


def submit_feedback(
    case_id: str,
    meter_id_hash: str,
    feedback_type: str,
    finding: str,
    inspector_id: str = None,
    notes: str = None,
    photo_reference: str = None,
):
    conn = _get_conn()
    conn.execute(
        """INSERT INTO field_feedback
           (case_id, meter_id_hash, inspector_id, feedback_type, finding, notes, photo_reference, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (case_id, meter_id_hash, inspector_id, feedback_type, finding, notes, photo_reference, datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()
    return {"status": "submitted", "case_id": case_id}


def get_feedback(case_id: str = None, meter_id: str = None):
    conn = _get_conn()
    if case_id:
        rows = conn.execute("SELECT * FROM field_feedback WHERE case_id = ?", (case_id,)).fetchall()
    elif meter_id:
        rows = conn.execute("SELECT * FROM field_feedback WHERE meter_id_hash = ?", (meter_id,)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM field_feedback ORDER BY created_at DESC LIMIT 100").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_feedback_stats():
    conn = _get_conn()
    total = conn.execute("SELECT COUNT(*) FROM field_feedback").fetchone()[0]
    by_type = conn.execute(
        "SELECT feedback_type, COUNT(*) as count FROM field_feedback GROUP BY feedback_type"
    ).fetchall()
    conn.close()
    return {
        "total_feedback": total,
        "by_type": {r["feedback_type"]: r["count"] for r in by_type},
    }
