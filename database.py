"""Small SQLite repository; timestamps are UTC epoch seconds."""
import sqlite3
from pathlib import Path

SCHEMA = '''
CREATE TABLE IF NOT EXISTS reports (
 id INTEGER PRIMARY KEY, title TEXT NOT NULL, description TEXT NOT NULL,
 animal_type TEXT NOT NULL, status_type TEXT NOT NULL,
 latitude REAL NOT NULL, longitude REAL NOT NULL,
 created_at REAL NOT NULL, expires_at REAL NOT NULL,
 delete_token_hash TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS reports_expiration ON reports(expires_at);
CREATE TABLE IF NOT EXISTS rate_limits (
 fingerprint TEXT NOT NULL, created_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS rate_expiration ON rate_limits(created_at);
'''


def connect(path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path, timeout=10)
    db.row_factory = sqlite3.Row
    return db


def initialize(path):
    with connect(path) as db:
        db.executescript(SCHEMA)
        columns = {row[1] for row in db.execute('PRAGMA table_info(reports)')}
        if 'author_id' not in columns:
            db.execute('ALTER TABLE reports ADD COLUMN author_id INTEGER')


def cleanup(db, now):
    db.execute('DELETE FROM reports WHERE expires_at <= ?', (now,))
    db.execute('DELETE FROM rate_limits WHERE created_at <= ?', (now - 3600,))

    if db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='account_tokens'").fetchone():
        db.execute('DELETE FROM account_tokens WHERE expires_at<=?', (now,))
        db.execute('DELETE FROM account_sessions WHERE expires_at<=?', (now,))
        db.execute('DELETE FROM auth_attempts WHERE created_at<=?', (now-3600,))


# Author projection deliberately excludes emails, hashes and internal account IDs.
REPORT_SELECT = ('SELECT r.*, u.username AS author_username, u.emoji AS author_emoji '
                 'FROM reports r LEFT JOIN users u ON u.id=r.author_id')
