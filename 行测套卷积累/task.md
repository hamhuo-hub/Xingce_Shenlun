# Task: Question Reservoir System

## Phase 1: Core Engine (Extraction & Storage)
- [/] Initialize Project Structure (FastAPI, SQLite, `media/` folder) <!-- id: 1 -->
- [x] Implement `QuestionExtractor` Class <!-- id: 2 -->
    - [x] **Image Extraction**: Save images to `media/`, return relative paths.
    - [x] **Material Detection**: Identify shared text/material for Data Analysis.
    - [ ] **Parsing**: Integrate `complete_converter` cleaning logic.
    - [ ] **Type Classification**: Detect type based on headers (e.g., "常识判断").
- [x] Debug: Fix 'forEach' error (Backend Exception) <!-- id: 9 -->
    - [x] **Parsing**: Integrate `complete_converter` cleaning logic.
    - [x] **Type Classification**: Detect type based on headers (e.g., "常识判断").
- [x] Debug: Fix 'Table' object text error <!-- id: 10 -->
- [x] localized Database Manager (SQLite) <!-- id: 3 -->
    - [x] Create methods for `add_question`, `add_material`, `link_question_material`.

## Phase 2: Web Interface & API
- [x] FastAPI Endpoints <!-- id: 4 -->
    - [x] `/upload_source`: Handle file upload & temporary storage.
    - [x] `/extract_preview`: Parse range string -> Return Preview data.
    - [x] `/confirm_extract`: Save to DB.
- [x] Dashboard UI <!-- id: 5 -->
    - [x] "Reservoir" Visuals (Water level / progress bars).
    - [x] "Entry" Form (File + Range Input).

## Phase 3: DOCX Generator
- [x] Template Design: (Abandoned for Web View) <!-- id: 6 -->
- [ ] Web Print View (`paper.html`) <!-- id: 7 -->
    - [ ] Endpoint `/api/paper_data` to fetch Type-grouped questions.
    - [ ] `paper.html`: Render questions with CSS for printing (A4 layout).
    - [ ] Grouping: Sort by Type (Const/Verbal/Quant/Logic/Data).
    - [ ] Styling: Compact, hidden UI buttons.

## Phase 4: Scoring System (New)
- [ ] Update Extractor to detect Sub-types (Graph/Def/Analogy/Logic) <!-- id: 11 -->
- [ ] Implement Score Calculator Logic (Points per type) <!-- id: 12 -->
- [ ] UI: Display "Lost Score" / "Current Score" upon entry. <!-- id: 13 -->

## Phase 5: Integration
- [ ] End-to-end Test: Import -> Pool -> Generate -> Result Update. <!-- id: 8 -->
