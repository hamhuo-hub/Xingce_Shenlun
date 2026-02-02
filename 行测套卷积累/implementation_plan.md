# Pivot to DOCX Generation

## Goal
Replace the unstable Web Print view with a robust DOCX generator. The generated DOCX must follow strict formatting rules (Reverse-engineered from `extractor.py`) to ensure it looks like a standard exam paper and can potentially be re-parsed.
User specifically requested fixing "Mixed options", "Unknown Types", and "Format inconsistencies".

## User Review Required
> [!IMPORTANT]
> The "Generate Paper" button will now strictly DOWNLOAD a .docx file instead of showing a web preview. The web preview will be removed or repurposed just for status checking.

## Proposed Changes

### Backend Logic (`generator.py`)
- **Structure**:
    - **Sections**: Use logical mapping for Headers (e.g., "第一部分 常识判断", "第二部分 言语理解").
    - **Questions**: Format as `1. [Stem]`.
    - **Options**: ensure Options are placed on new lines or in a table if needed, strictly following `A.`, `B.` format.
    - **Materials**: Insert "根据以下材料，回答..." before the group of questions.
    - **Images**: Ensure all images from `media/` are inserted correctly into the DOCX.
    - **Answers**: Append a "Answer Key" section at the end with `1. 【答案】X 【解析】...`.

### API (`main.py`)
- Modify `/generate` endpoint:
    - Instead of returning JSON, it calls `PaperBuilder.create_paper`.
    - Returns a `FileResponse` or a JSON with `download_url`.
    - Allow passing "Include Answers" flag (default True, probably at end).

### Frontend (`index.html`)
- Update "Generate Paper" (生成错题卷) button behavior:
    - POST `/generate` -> Receive Blob/Link -> Trigger Download.
    - Remove the Web Preview (Layout `paper.html`) as it is being deprecated.

## Verification Plan

### Manual Verification
1.  **Generate**: Select questions -> Click Generate.
2.  **Open DOCX**: Open the downloaded file in Word/WPS.
3.  **Check Layout**:
    - Are questions grouped by Type? (e.g. all "常识" together under "第一部分").
    - Are Materials shown once before their questions?
    - Are Images visible?
    - Are Options A/B/C/D clearly separated?
    - Is Question Type visible (or implied by Section)?
4.  **Re-Import Test** (Optional but good validation):
    - Upload the GENERATED docx back to the system.
    - Verify `extractor.py` parses it correctly. (This proves the format is "Standard").
