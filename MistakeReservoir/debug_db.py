import sqlite3
import os

db_path = "reservoir.db"
if not os.path.exists(db_path):
    print("DB not found")
    exit()

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
c = conn.cursor()

# 1. Check Total
count = c.execute("SELECT count(*) FROM questions").fetchone()[0]
print(f"Total Questions: {count}")

# 2. Check Types
print("\n--- Types ---")
types = c.execute("SELECT type, count(*) as c FROM questions GROUP BY type").fetchall()
for t in types:
    print(f"{t['type']}: {t['c']}")

# 3. Check Missing Content
print("\n--- Missing Content Stats ---")
no_options = c.execute("SELECT count(*) FROM questions WHERE options_html IS NULL OR length(options_html) < 5").fetchone()[0]
no_answer = c.execute("SELECT count(*) FROM questions WHERE answer_html IS NULL OR length(answer_html) < 5").fetchone()[0]
print(f"Empty/Short Options: {no_options}")
print(f"Empty/Short Analysis: {no_answer}")

# 4. Sample a bad question (if any)
print("\n--- Sample Q with Empty Options ---")
bad_q = c.execute("SELECT * FROM questions WHERE options_html IS NULL OR length(options_html) < 5 LIMIT 1").fetchone()
if bad_q:
    print(f"ID: {bad_q['id']}, Type: {bad_q['type']}")
    print(f"Content Preview: {bad_q['content_html'][:100]}...")
    print(f"Options: {bad_q['options_html']}")
    print(f"Answer: {bad_q['answer_html']}")
else:
    print("None found.")

conn.close()
