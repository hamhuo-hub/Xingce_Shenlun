# Session Summary - Refactoring to Web Print

## Accomplished
1.  **Refactoring Output**: Abandoned `python-docx` generation in favor of a direct **Web Print View** (`paper.html`).
2.  **Options Extraction**: Fixed regex to capture `A.` `(A)` `A、` style options.
3.  **Database Fix**: Added `options_html` column and enabled `UPDATE` on re-upload to fix corrupted data.
4.  **Layout**: Implemented basic "4 Part" grouping in the Web View.

## Current State
- **Server**: Stopped (Was running on Port 8006).
- **Database**: Wiped and ready for fresh uploads.
- **Frontend**: `index.html` generates a JSON payload, `paper.html` renders it.

## Bug Fixes
- **Missing Answer Analysis**: Fixed `extractor.py` to handle cases where the Analysis Keyword (e.g. `【答案】`) appears on the same line as the last Option. Implemented paragraph splitting logic to separate Option D from Answer.
- **Regex Robustness**: Updated `ANSWER_KEYWORDS` to use Regex, handling spaces (e.g. `【 解析 】`) and various punctuation.
- **Subtype Detection**: Updated `extractor.py` to detect Judgment subtypes (Graphical, Definition, Analogy, Logic).

## Features Added
- **Scoring System**: Implemented "Lost Score" display in the Preview UI based on Question Type.
- **Paper Sorting**: Updated `paper.html` to sort questions not just by main Type, but by Subtype order.
