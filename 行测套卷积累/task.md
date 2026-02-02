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

## Phase 3: DOCX Generator (Pivot)
- [/] Implement DOCX Generator in `generator.py` <!-- id: 5 -->
    - [ ] Mapped Section Headers (Common Sense, Verbal, etc.) <!-- id: 14 -->
    - [ ] Standard Question Format (1. Stem) <!-- id: 15 -->
    - [ ] Options Formatting (A/B/C/D on new lines) <!-- id: 16 -->
    - [ ] Image Insertion (Absolute paths from media) <!-- id: 17 -->
    - [ ] Answer Key Section <!-- id: 18 -->
- [ ] Update API to Serve DOCX <!-- id: 19 -->
- [ ] Update Frontend to Trigger Download <!-- id: 20 -->

## Phase 4: Scoring System (New)
- [x] Update Extractor to detect Sub-types (Graph/Def/Analogy/Logic) <!-- id: 11 -->
- [x] Implement Score Calculator Logic (Points per type) <!-- id: 12 -->
- [x] UI: Display "Lost Score" / "Current Score" upon entry. <!-- id: 13 -->

## Phase 5: Integration
- [x] End-to-end Test: Import -> Pool -> Generate -> Result Update. <!-- id: 8 -->
