import sqlite3
import os

db_path = "reservoir.db"
if not os.path.exists(db_path):
    print("DB not found")
    exit()

conn = sqlite3.connect(db_path)
c = conn.cursor()

try:
    c.execute("ALTER TABLE questions ADD COLUMN options_html TEXT")
    print("Added options_html column.")
except sqlite3.OperationalError as e:
    print(f"Error (maybe exists): {e}")

conn.commit()
conn.close()
