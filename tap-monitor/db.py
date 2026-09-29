import sqlite3
from config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS prices(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts TEXT NOT NULL,            -- UTC ISO, coleta
  dest TEXT NOT NULL,
  days_ahead INTEGER NOT NULL,
  depart_date TEXT NOT NULL,
  price REAL NOT NULL,
  currency TEXT NOT NULL,
  stops INTEGER,
  duration_min INTEGER,
  source TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_prices ON prices(dest, days_ahead, ts);
CREATE TABLE IF NOT EXISTS runs(
  id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, ok INTEGER, message TEXT
);
"""


def conn():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def init():
    with conn() as c:
        c.executescript(SCHEMA)
