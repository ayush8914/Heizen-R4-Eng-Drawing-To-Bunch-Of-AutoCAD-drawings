# drawing-to-dxf

Turn an **engineering drawing** (PNG, JPG) into **AutoCAD-compatible DXF** files—**without** requiring AutoCAD to generate them (open outputs in AutoCAD, BricsCAD, LibreCAD, etc.).

Implemented **two-stage Gemini strategy** (plan → code) described below.

---
<img width="1430" height="804" alt="Screenshot 2026-05-08 at 8 30 08 AM" src="https://github.com/user-attachments/assets/eded0fc4-0802-46e6-af71-52bc46cb8a11" />

---
## Example 

### Input
<img width="660" height="558" alt="Screenshot 2026-05-08 at 8 43 06 AM" src="https://github.com/user-attachments/assets/a6b96100-f150-437a-bffe-7643e07097ea" />

### Output
<img width="1052" height="774" alt="Screenshot 2026-05-08 at 8 47 40 AM" src="https://github.com/user-attachments/assets/f72cd0eb-db5f-4f83-8e09-6e399ed46f82" />



## What each flow is for

### Flow A — `component-sheet` (analysis only)

**Purpose:** Extract a readable **component sheet** from the image: title block cues, ~5–7 fabrication items, key dimensions, hole notes, and a compact summary-style table per row.

**Pipeline:**

1. Load **image** 
2. Optionally downscale longest side (`--max-side`) and encode **PNG** for the API.
3. **Gemini** `generateContent` with image + a strict JSON schema prompt (`component_sheet_report.py`).
4. Write **JSON**, **Markdown** report, and **raw model text**—no Python execution, no DXF.

**Default model:** `gemini-2.0-flash` (`cli.py`). Suited for **structured extraction** within a moderate output budget (`SHEET_EXTRACT_OUTPUT_TOKENS`).

---

### Flow B — `gemini-codegen` (DXF generation)

**Purpose:** Ask a vision model to emit **executable Python** (one script per fabricated part) that uses **ezdxf** to write a **per-part DXF**, then **merge** those into a single **assembly DXF** (horizontal strip or grid).

**Pipeline (simplified):**

1. Same **load → PNG** preprocessing as Flow A.
2. Optional **`--sheet-report`:** run Flow A once first for an extra JSON/Markdown artifact (one more API call).
3. **Default: two-stage codegen** (`gemini_cad_codegen.py`, `two_stage=True`):
   - **Stage 1 — component plan:** Gemini returns JSON mapping `component_id →` rich text description (what to fabricate, datums, holes, thickness). **Model:** `gemini-2.0-flash` (`stage1_model`). Smaller `maxOutputTokens` cap is enough for a plan, not full code.
   - **Stage 2 — batched codegen:** Descriptions are batched (default batch size 3); each batch calls Gemini for JSON whose values are **full Python sources**. Batches run in parallel (`ThreadPoolExecutor`). **Model:** `gemini-2.5-flash` (`stage2_model`). Missing parts after batching trigger **per-id retry** with a more compact prompt.
4. **Fallback paths** when two-stage fails or is disabled:
   - **Multi-segment:** one Gemini call **per part** so each script gets its own output token budget.
   - **Single JSON call:** one response for all parts (`--gemini-single-json-call`; risk of **truncation** when many parts).
5. **Sanitize** generated Python (fix common ezdxf / MTEXT / JSON-in-string issues), then **`subprocess`** run each script with `sys.argv[1]` = output DXF path.
6. **Merge** successful DXFs with **ezdxf** `Importer` + translation (`merge_dxfs_horizontal` or `merge_dxfs_grid`).

**Default codegen model (`--gemini-model`):** `gemini-2.5-flash` for single-stage calls; two-stage defaults split **2.0 (plan)** vs **2.5 (long code)** as above.

---

## Why these models?

| Role | Typical model | Rationale |
|------|----------------|-----------|
| Component sheet & Stage-1 plan | `gemini-2.0-flash` | Fast, cost-efficient; output is **JSON/text plans**, not thousand-line programs. |
| Stage-2 / single-stage codegen | `gemini-2.5-flash` | Stronger for **long, structured Python** and DXF-minded instructions; aligns with large `--gemini-max-output-tokens` (e.g. 65536) for multi-part payloads. |

You can override with `--gemini-model` where the CLI wires it (see `--help`). Sheet-only defaults differ from codegen defaults intentionally.

---

## Tech stack (what is used for what)

| Piece | Purpose |
|-------|---------|
| **OpenCV** | Load images, resize (`--max-side`), PNG encode for Gemini. |
| **urllib** (+ stdlib SSL) | **REST** calls to Gemini `v1beta` `generateContent` (`ai_structured.py`)—no heavyweight SDK requirement for the core path. |
| **ezdxf** | Generated scripts create DXFs; merger builds assembly DXFs (units mm, R2010-style doc). |
| **ThreadPoolExecutor** | Parallel Stage-2 batch requests to reduce wall-clock time. |

Optional utilities in `ai_structured.py` (OpenAI-compatible, Ollama) exist for other experiments; the **shipping CLI** is Gemini-centric.

---

## Problems you are likely to hit (and what the code does about them)

1. **doing it in one ai call** : results in less detailed and error prone json data. -> broken .dxf files
2. **expecting data into json** : component design data into json and then converting them to .dxf (details loss)
3. **solution** : use two stage pipeline making ai call parallel and generating python code for each component intead of json data. result -> detailed component design.

---

## Install

```powershell
cd C:\Users\admin\Desktop\R4EngDrawingAutoCAD\Heizen-R4-Eng-Drawing-To-Bunch-Of-AutoCAD-drawings
python -m venv .venv
.\.venv\Scripts\activate
pip install -e .
```

Set**`GOOGLE_API_KEY`** in the environment.

---

## Usage


```powershell
 drawing-to-dxf gemini-codegen "Resource/Sample.png" -o out_gemini_codegen \
  --target-components 9 \
  --assembly-layout grid --grid-columns 3

```
---

## Outputs (typical)

Under `-o` / `--output-dir`:

---

**Heizen-R4-Eng-Drawing-To-Bunch-Of-AutoCAD-drawings** — interview / demo project: engineering drawing → Gemini vision → DXF deliverables.
