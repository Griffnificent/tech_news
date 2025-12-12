import sqlite3
from pathlib import Path
from datetime import datetime, timedelta

class SeenDB:
    def __init__(self, db_path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS seen (
                    id TEXT PRIMARY KEY,
                    seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_seen_at ON seen(seen_at)")

    def is_seen(self, entry_id):
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute("SELECT 1 FROM seen WHERE id = ?", (entry_id,))
            return cur.fetchone() is not None

    def mark_seen(self, entry_id):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR IGNORE INTO seen (id) VALUES (?)",
                (entry_id,)
            )

    def cleanup(self, days=30):
        cutoff = datetime.now() - timedelta(days=days)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM seen WHERE seen_at < ?", (cutoff,))
