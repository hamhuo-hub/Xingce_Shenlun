import sqlite3
import json

db_path = "reservoir.db"
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
c = conn.cursor()

try:
    c.execute("SELECT id, original_num, substr(content_html, 1, 50) as content, options_html, length(options_html) as opt_len FROM questions ORDER BY id DESC LIMIT 5")
    rows = c.fetchall()
    print("--- Latest 5 Questions ---")
    for row in rows:
        print(f"ID: {row['id']}, Num: {row['original_num']}")
        print(f"Content: {row['content']}")
        print(f"Options Len: {row['opt_len']}")
        print(f"Options Sample: {str(row['options_html'])[:50]}")
        print("-" * 20)
except Exception as e:
    print(f"Error: {e}")

conn.close()
