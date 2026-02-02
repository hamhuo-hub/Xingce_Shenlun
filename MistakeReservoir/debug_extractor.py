from extractor import QuestionExtractor
import os
import json

path = r"c:\potorable\StudentSphere\行测申论\行测套卷积累\行测组卷8.docx"
extractor = QuestionExtractor(media_dir="media")

try:
    print(f"Extracting from {path}...")
    questions = extractor.extract_from_file(path)
    print(f"Extracted {len(questions)} questions.")
    
    no_opt_count = 0
    for q in questions[:10]:
        print(f"--- Q {q['original_num']} ---")
        print(f"Options: {q['options_html']}")
        if not q['options_html']:
            no_opt_count += 1
            
    print(f"\nTotal questions with NO options in first 10: {no_opt_count}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
