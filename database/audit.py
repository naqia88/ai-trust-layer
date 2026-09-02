# Import built-in modules for SQLite storage, JSON serialization, and timestamps.
import datetime
import json
import sqlite3

from config import DB_PATH


# Create the actions table when the audit database is first used.
def init_db():
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS actions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            action_type TEXT,
            details TEXT,
            financial_score INTEGER,
            privacy_score INTEGER,
            policy_score INTEGER,
            final_score INTEGER,
            decision TEXT,
            reasons TEXT,
            resolved_by TEXT,
            resolution TEXT,
            resolution_time TEXT
        )
        """
    )
    connection.commit()
    connection.close()


# Save one trust decision and its original action data in the audit log.
def log_action(result):
    action = result["action"]
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    cursor.execute(
        """
        INSERT INTO actions (
            timestamp,
            action_type,
            details,
            financial_score,
            privacy_score,
            policy_score,
            final_score,
            decision,
            reasons
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            result["timestamp"],
            action["action_type"],
            json.dumps(action["details"]),
            result["financial_score"],
            result["privacy_score"],
            result["policy_score"],
            result["final_score"],
            result["decision"],
            json.dumps(result["reasons"]),
        ),
    )
    connection.commit()
    action_id = cursor.lastrowid
    connection.close()
    return action_id


# Return all audit records with their column names for the dashboard and API.
def get_actions():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM actions ORDER BY id DESC")
    actions = [dict(row) for row in cursor.fetchall()]
    connection.close()
    return actions


# Record the human decision that resolved an escalated action.
def resolve_action(action_id, resolved_by, resolution):
    resolution_time = datetime.datetime.now().isoformat()
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    cursor.execute(
        """
        UPDATE actions
        SET resolved_by = ?, resolution = ?, resolution_time = ?
        WHERE id = ?
        """,
        (resolved_by, resolution, resolution_time, action_id),
    )
    connection.commit()
    connection.close()
