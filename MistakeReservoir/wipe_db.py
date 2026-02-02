import sqlite3
import os

db_path = "reservoir.db"
if not os.path.exists(db_path):
    print("DB not found")
    exit()

conn = sqlite3.connect(db_path)
c = conn.cursor()

try:
    c.execute("DELETE FROM review_stats")
    c.execute("DELETE FROM questions")
    c.execute("DELETE FROM materials")
    c.execute("DELETE FROM sources")
    print("Database Wiped Clean.")
except Exception as e:
    print(f"Error: {e}")

conn.commit()
conn.close()
