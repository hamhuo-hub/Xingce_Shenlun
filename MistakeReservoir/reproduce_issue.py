from extractor import QuestionExtractor
import os
import json

path = r"c:\potorable\StudentSphere\行测申论\行测套卷积累\行测组卷12-解析.docx"
extractor = QuestionExtractor(media_dir="media")

try:
    print(f"Extracting from {path}...")
    # Extract only first 5 questions to save time, but extract_from_file parses all unless we hack it.
    # But extract_from_file allows target_ids.
    questions = extractor.extract_from_file(path, target_ids=[1, 2, 3, 4, 5])
    print(f"Extracted {len(questions)} questions.")
    
    for q in questions:
        print(f"--- Q {q['original_num']} [{q['type']}] ---")
        print(f"Content Start: {q['content_html'][:50]}")
            
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
