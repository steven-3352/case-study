"""Focused infrastructure smoke tests; the frozen acceptance suite supplies the full matrix."""

from pathlib import Path

from mv_platform.config import Settings
from mv_platform.infrastructure.database import Database


def test_settings_and_database(tmp_path):
    settings = Settings(db_path=str(Path("data") / "app.sqlite3"))
    assert settings.host == "127.0.0.1"
    database = Database(tmp_path / "nested" / "app.sqlite3")
    database.migrate()
    with database.connect() as connection:
        assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        assert connection.execute("PRAGMA journal_mode").fetchone()[0].lower() == "wal"
        assert connection.execute("PRAGMA busy_timeout").fetchone()[0] > 0
