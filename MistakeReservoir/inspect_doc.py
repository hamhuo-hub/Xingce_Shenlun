from docx import Document
import sys

path = r"c:\potorable\StudentSphere\行测申论\行测套卷积累\行测组卷8.docx"
try:
    doc = Document(path)
    print(f"--- Document: {path} ---")
    count = 0
    for p in doc.paragraphs:
        text = p.text.strip()
        if text:
            print(f"[{count}] {text}")
            count += 1
            if count >= 30: break
except Exception as e:
    print(f"Error: {e}")
