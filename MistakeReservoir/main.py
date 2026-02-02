from fastapi import FastAPI, UploadFile, File, HTTPException, Body
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
import shutil
import os
import uvicorn
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

from extractor import QuestionExtractor
from database import DatabaseManager

app = FastAPI()

# Config
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MEDIA_DIR = os.path.join(BASE_DIR, "media")
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
if not os.path.exists(UPLOAD_DIR): os.makedirs(UPLOAD_DIR)
# Init Components
db = DatabaseManager(os.path.join(BASE_DIR, "reservoir.db"))
extractor = QuestionExtractor(MEDIA_DIR)


# ... existing imports ...

class GenerateRequest(BaseModel):
    total_count: int
    types: List[str] = [] # e.g. ["常识", "言语"]

@app.post("/generate")
def generate_paper(req: GenerateRequest):
    # Fetch Questions
    questions = db.get_random_questions(req.total_count, req.types if req.types else None)
    
    if not questions:
        raise HTTPException(status_code=400, detail="No questions available in pool")
        
    # Generate DOCX
    from generator import PaperBuilder
    builder = PaperBuilder(MEDIA_DIR)
    
    filename = f"MistakePaper_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
    output_path = os.path.join(UPLOAD_DIR, filename)
    
    builder.create_paper(questions, output_path)
    
    # Return download URL or File directly?
    # Using JSON with URL is better for fetch handling
    return {"download_url": f"/download/{filename}", "count": len(questions)}

@app.get("/download/{filename}")
def download_file(filename: str):
    file_path = os.path.join(UPLOAD_DIR, filename)
    if os.path.exists(file_path):
        return FileResponse(file_path, filename=filename)
    return HTTPException(404, "File not found")

# Mount Static
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
app.mount("/media", StaticFiles(directory=MEDIA_DIR), name="media")

# Models
class ExtractRequest(BaseModel):
    filename: str
    ranges: str # e.g. "1-5, 12"

class SaveRequest(BaseModel):
    source_filename: str
    questions: List[dict]

@app.get("/")
def read_root():
    return FileResponse(os.path.join(BASE_DIR, "static/index.html"))

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"filename": file.filename}

def parse_ranges(range_str: str) -> List[int]:
    ids = set()
    parts = range_str.split(',')
    for p in parts:
        p = p.strip()
        if '-' in p:
            try:
                start, end = map(int, p.split('-'))
                for i in range(start, end + 1):
                    ids.add(i)
            except: pass
        else:
            try:
                ids.add(int(p))
            except: pass
    return sorted(list(ids))

@app.post("/extract_preview")
def extract_preview(req: ExtractRequest):
    file_path = os.path.join(UPLOAD_DIR, req.filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    target_ids = parse_ranges(req.ranges)
    try:
        questions = extractor.extract_from_file(file_path, target_ids)
        return {"count": len(questions), "questions": questions}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/confirm_save")
def confirm_save(req: SaveRequest):
    # 1. Add Source
    sid = db.add_source(req.source_filename)
    
    # 2. Add Questions & Materials
    # We need to handle Material deduplication per save batch logic
    # Ideally, extractor returns material content. We hash it or just add it.
    
    material_map = {} # content_hash -> mid
    
    count = 0
    for q in req.questions:
        mid = None
        mat_content = q.get('material_content')
        if mat_content:
            mat_hash = hash(mat_content)
            if mat_hash in material_map:
                mid = material_map[mat_hash]
            else:
                mid = db.add_material(sid, mat_content, type=q['type'])
                material_map[mat_hash] = mid
        
        # Debug Log
        if count < 5:
            print(f"DEBUG: Saving Q {q.get('original_num')}, Options Len: {len(q.get('options_html') or '')}, Type: {q.get('type')}")

        db.add_question(
            source_id=sid,
            original_num=q['original_num'],
            content=q['content_html'],
            options=q['options_html'],
            answer=q['answer_html'], # Contains Analysis
            images=q['images'],
            type=q['type'],
            material_id=mid
        )
        count += 1
        
    return {"status": "success", "saved_count": count}

@app.get("/pool_status")
def pool_status():
    return db.get_pool_status()

# To run: uvicorn main:app --reload
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)