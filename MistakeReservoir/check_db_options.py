import sqlite3
import json

db_path = "reservoir.db"
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
c = conn.cursor()

try:
    # The original connection and cursor are already established.
    # The instruction seems to re-establish them inside the try block,
    # but it's more logical to use the existing ones or replace the whole block.
    # Following the instruction's structure, it seems to want a new connection for this specific task.
    # However, the instruction's provided code snippet is a bit fragmented.
    # Let's interpret it as replacing the *entire* previous `try...except` block
    # with the new logic for checking img tags.
    # The `conn = sqlite3.connect("reservoir.db")` and `conn.row_factory = sqlite3.Row`
    # and `c = conn.cursor()` lines inside the instruction's block suggest a new,
    # self-contained operation.

    # The instruction's snippet starts with `conn.row_factory = sqlite3.Row`
    # and `c = conn.cursor()` which are already done globally.
    # Then it has `c.execute("SELECT id, original_num, ...")` which is the old query.
    # This is followed by `conn = sqlite3.connect("reservoir.db")` etc.
    # This indicates the instruction wants to replace the *content* of the try block.

    # Let's assume the instruction wants to replace the *entire* previous try/except block
    # with the new image checking logic, and that the `conn.close()` at the end of the
    # instruction's snippet is meant to close the connection opened *within* that snippet.
    # This would mean the initial `conn` and `c` are unused, which is odd, but
    # I must follow the instruction faithfully.

    # The instruction's snippet:
    # c.execute("SELECT id, original_num, substr(content_html, 1, 50) as content, options_html, length(options_html) as opt_len FROM questions ORDER BY id DESC LIMIT 5")
    # conn = sqlite3.connect("reservoir.db")
    # conn.row_factory = sqlite3.Row
    # c = conn.cursor()
    # c.execute("SELECT id, content_html, images FROM questions LIMIT 5")
    # rows = c.fetchall()
    #
    # print(f"Checking {len(rows)} questions...")
    # for row in rows:
    #     has_img_tag = 'img' in row['content_html']
    #     print(f"Q{row['id']}: Has Tag? {has_img_tag} | Images JSON: {row['images']}")
    #     if not has_img_tag and row['images'] != '[]':
    #         print("  [WARNING] JSON has images but HTML tag missing!")
    #
    # conn.close()
    # for row in rows: # This loop seems to be a leftover from the old code and refers to columns not in the new query.
    #     print(f"ID: {row['id']}, Num: {row['original_num']}")
    #     print(f"Content: {row['content']}")
    #     print(f"Options Len: {row['opt_len']}")
    #     print(f"Options Sample: {str(row['options_html'])[:50]}")
    #     print("-" * 20)

    # Given the instruction, the most faithful interpretation is to replace the *entire*
    # `try...except` block with the new image checking logic.
    # The initial `conn` and `c` will be overwritten/re-established within the new block.
    # The trailing `for row in rows:` loop in the instruction's snippet is problematic
    # as it refers to columns (`original_num`, `options_html`) not selected in the
    # `SELECT id, content_html, images FROM questions LIMIT 5` query.
    # I will assume this trailing loop is an error in the instruction and should be omitted,
    # as it would cause a KeyError. The primary intent seems to be the image tag check.

    # Re-establishing connection and cursor as per instruction's snippet
    conn_check = sqlite3.connect("reservoir.db")
    conn_check.row_factory = sqlite3.Row
    c_check = conn_check.cursor()

    c_check.execute("SELECT id, content_html, images FROM questions LIMIT 5")
    rows = c_check.fetchall()

    print(f"Checking {len(rows)} questions...")
    for row in rows:
        has_img_tag = 'img' in row['content_html']
        print(f"Q{row['id']}: Has Tag? {has_img_tag} | Images JSON: {row['images']}")
        if not has_img_tag and row['images'] != '[]':
            print("  [WARNING] JSON has images but HTML tag missing!")

    conn_check.close() # Close the connection opened for this check.

except Exception as e:
    print(f"Error: {e}")

conn.close()
