"""Run one SQL query on demo.db, a small SQLite database for the demo.

Usage: python3 db.py "SELECT * FROM fees"

The first run creates demo.db with a fees table. All names are fake.
"""

import sqlite3
import sys
from pathlib import Path

DB = Path(__file__).parent / "demo.db"
SAMPLE = [
    ("Priya", 2024, 12000, "paid"),
    ("Karthik", 2024, 12000, "paid"),
    ("Meena", 2025, 13500, "paid"),
    ("Arun", 2025, 13500, "due"),
    ("Divya", 2026, 15000, "due"),
]


def main() -> int:
    new = not DB.exists()
    con = sqlite3.connect(DB)
    if new:
        con.execute("CREATE TABLE fees (student TEXT, year INTEGER, amount INTEGER, status TEXT)")
        con.executemany("INSERT INTO fees VALUES (?, ?, ?, ?)", SAMPLE)
        con.commit()

    cursor = con.execute(sys.argv[1])
    rows = cursor.fetchall()
    con.commit()
    for row in rows:
        print(" | ".join(str(value) for value in row))
    if not rows:
        print(f"{cursor.rowcount} rows changed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
