# Implementation Plan - Question Reservoir System

## Goal
Build a local "Mistake Reservoir & Paper Generation" system.
**Workflow**: User records mistakes -> System stores them in a "Pool" -> When pool is full, user generates a **shuffle-order DOCX paper** -> User tests offline -> Updates status (Mastered/Still Wrong).

## User Review Required
> [!IMPORTANT]
> **Media Storage**: Images will be extracted from DOCX and saved to a local `media/` folder. The database will only store file paths.
> **Material Handling**: "Data Analysis" (资料分析) questions will be linked to a shared "Material" entry in the database.

## Architecture

### 1. Database Schema (SQLite)
*   **Sources**: `id`, `filename`, `upload_date`
*   **Materials**: `id`, `source_id`, `content_html`, `images` (JSON list of paths), `type` (e.g., 'data_analysis')
*   **Questions**: 
    *   `id`, `source_id`, `material_id` (FK, Nullable), `original_num` (int)
    *   `type` (Const/Verbal/Logic/Quant/Data)
    *   `content_html` (stem), `options_html`, `analysis_html`
    *   `images` (JSON list of paths)
*   **ReviewStats**: 
    *   `question_id` (FK), `status` (Pool/Archived)
    *   `mistake_count`, `last_wrong_date`, `last_right_date`

### 2. Core Logic: The Reservoir (Pooling)
*   **Input Phase**: User inputs numbers (e.g., "1-5"). System extracts them.
    *   If a question belongs to a Material (Data Analysis), the Material is automatically linked.
    *   Status set to `Pool`.
*   **Dashboard**: Shows "Pool Level" (e.g., "Logic: 15/20").
*   **Output Phase (Web Print)**:
    *   Trigger: User clicks "Generate Paper".
    *   Process: Open `paper.html`. Fetch N random questions.
    *   Rendering: Groups questions by Type. "Compact" CSS.
    *   Material Logic: Print material once per group.
    *   User prints to PDF via Browser.

### 3. Extraction Engine (`QuestionExtractor`)
*   **Image Handling**: Extract `blip` -> Save to `media/{uuid}.png` -> Return Path.
*   **Material Detection**:
    *   Scan for keys like `根据...回答`, `材料`, `第x部分`.
    *   Store text between Header and next Question as "Material".
    *   Link subsequent Questions to this Material until a new Header/Type switch.
*   **Parsing Fixes**:
    *   Apply `complete_converter.py` logic (strong deletion of "故", cleanup).
    *   Separate Stem, Options, and Analysis.

## Proposed Components

### [Backend] `main.py`
*   `POST /extract`: Input (File, Range String "1-5, 12") -> Returns Preview -> Save to DB.
*   `GET /pool_status`: Stats by Type.
*   `POST /generate_docx`: Input (Types, Count) -> Returns Download URL.
*   `POST /update_results`: Input (Question IDs, Result) -> Archives or Keeps in Pool.

### [Frontend] `static/`
*   **Entry Page**: Drag & Drop DOCX -> Input Numbers.
*   **Pool Dashboard**: Progress Bars. "Generate Paper" Button.
*   **Result Entry**: List generated questions -> Checkbox for "Still Wrong".

## Phase 4: Scoring System (New)
### Logic
*   **Score Map**:
    *   Verbal (言语): 0.8
    *   Quant (数量): 0.8
    *   Data (资料): 1.0
    *   Const (常识): 0.5
    *   Logic (判断推理):
        - Graphical (图形): 0.6
        - Definition (定义): 0.7
        - Analogy (类比): 0.5
        - Logic (逻辑): 0.8

### Implementation Update
*   **Extraction**: Enhance `extractor.py` to regex match sub-headers inside Judgment section (e.g. "一、图形推理") and store fine-grained `type`.
*   **Scoring**: In `confirm_save`, sum up the total score of questions being added (Lost Points).

## Verification Plan
1.  **Extraction Test**: Import "Set 12". Input "116-120" (Data Analysis). Verify DB has 1 Material linked to 5 Questions. Verify Images in `media/`.
2.  **Generation Test**: Generate a DOCX. Check if Material appears correctly (not duplicated 5 times, or handled gracefully). Check if Images render.
