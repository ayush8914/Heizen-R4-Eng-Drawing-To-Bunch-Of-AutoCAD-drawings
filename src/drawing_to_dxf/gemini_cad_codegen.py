"""Experimental parallel path: Gemini analyzes a drawing image and returns Python source per
component; scripts are executed to emit DXF files, then merged into one horizontal layout.

**Security:** runs model-generated Python with the same privileges as the user process. Use only
on trusted inputs and in an isolated environment for untrusted models/images.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import cv2
import ezdxf
import ezdxf.units
from ezdxf import bbox
from ezdxf.addons.importer import Importer
from ezdxf.math import Matrix44

from drawing_to_dxf.ai_structured import call_gemini_generate_content_raw
from drawing_to_dxf.component_sheet_report import SHEET_EXTRACT_OUTPUT_TOKENS
from drawing_to_dxf.preprocess import load_image_bgr, load_pdf_page_as_bgr


def _resolved_output_dir(output_dir: Path) -> Path:
    """Turn ``-o`` into an absolute folder path under the current working directory when relative."""
    p = Path(output_dir).expanduser()
    if not p.is_absolute():
        p = Path.cwd() / p
    return p.resolve(strict=False)


CODEGEN_INSTRUCTION_LEAD = """You are a senior mechanical/structural drafting assistant. The input is **always** treated as an **engineering production context** (shop drawings, part portfolios, lattice/component sheets, or assembly elevations). Your job is to **extract distinct engineering/manufacturing components** so each output DXF is usable **as a hand-off** to downstream CAD, nesting, or CAM—not a loose sketch.

Return ONLY valid JSON (no markdown fences, no commentary). Shape:
[
  {
    "part_740": "<full Python 3 source as one JSON string>",
    "part_721": "<full Python 3 source as one JSON string>"
  }
]

Split across several inner objects if needed; merge all key/value pairs logically.

Focus on parts that are **must-have to build the structure** and parts that need **separate fabrication drawings**.

Component selection rule (strict):
Prioritize **small, complex, connection-critical fabrication components** first.
Prefer: gusset plates, cleats, brackets, lug plates, splice/base plates, stiffeners/fish plates, hole templates.
De-prioritize: long/simple members (straight bars, long chords, plain angles) unless the drawing explicitly shows them as separate fabricated parts.
If both are present: choose the connection/detail part over the long/simple member, unless omitting the long member would remove a must-have fabricated component.

---
Prioritize **traceability**: another engineer should see **which printed dimensions** drove the DXF.
e.g. you can see as reference :

[
  {
    "figure-5-cross-arm-top-isa100x100x8": "import ezdxf\n\ndoc = ezdxf.new('R2010')\nmsp = doc.modelspace()\n\nlength = 7200\nheight = 1000\n\n# Outer frame\nmsp.add_line((0,0), (length,0))\nmsp.add_line((length,0), (length,height))\nmsp.add_line((length,height), (0,height))\nmsp.add_line((0,height), (0,0))\n\n# Bracing\nmsp.add_line((0,0), (1800,1000))\nmsp.add_line((1800,1000), (3600,0))\nmsp.add_line((3600,0), (5400,1000))\nmsp.add_line((5400,1000), (7200,0))\n\n# Holes\nfor x in range(300, 7200, 600):\n    msp.add_circle((x, 50), 9)\n    msp.add_circle((x, 950), 9)\n\nfilename = 'figure_5_crossarm_top.dxf'\ndoc.saveas(filename)\nprint(f'Saved {filename}')"
  },
  {
    "figure-9-bracing-isa65x65x6": "import ezdxf\n\ndoc = ezdxf.new('R2010')\nmsp = doc.modelspace()\n\nlength = 3000\nheight = 3000\nhole_radius = 8\n\n# Main member\nmsp.add_line((0,0), (length,height))\nmsp.add_line((65,0), (length+65,height))\n\n# Holes along member\npositions = [500, 1200, 1900, 2600]\n\nfor p in positions:\n    x = p\n    y = p\n    msp.add_circle((x,y), hole_radius)\n\nfilename = 'figure_9_bracing.dxf'\ndoc.saveas(filename)\nprint(f'Saved {filename}')"
  },
  {
    "figure-10-gusset-plate-pl10": "import ezdxf\n\ndoc = ezdxf.new('R2010')\nmsp = doc.modelspace()\n\npoints = [(0,0), (150,0), (150,120), (110,200), (40,200), (0,120)]\n\nmsp.add_lwpolyline(points, close=True)\n\nholes = [(30,40), (120,40), (30,100), (120,100), (50,160), (100,160)]\n\nfor h in holes:\n    msp.add_circle(h, 9)\n\nfilename = 'figure_10_gusset_plate.dxf'\ndoc.saveas(filename)\nprint(f'Saved {filename}')"
  },
  {
    "figure-11-base-plate-pl20": "import ezdxf\n\ndoc = ezdxf.new('R2010')\nmsp = doc.modelspace()\n\nsize = 500\n\nmsp.add_lwpolyline([(0,0), (size,0), (size,size), (0,size)], close=True)\n\nholes = [(75,75), (425,75), (75,425), (425,425)]\n\nfor h in holes:\n    msp.add_circle(h, 12)\n\nfilename = 'figure_11_base_plate.dxf'\ndoc.saveas(filename)\nprint(f'Saved {filename}')"
  },
  {
    "figure-14-earthing-lug-pl10": "import ezdxf\n\ndoc = ezdxf.new('R2010')\nmsp = doc.modelspace()\n\npoints = [(0,0), (50,0), (50,70), (35,100), (0,100)]\n\nmsp.add_lwpolyline(points, close=True)\n\nmsp.add_circle((25,55), 8)\n\nfilename = 'figure_14_earthing_lug.dxf'\ndoc.saveas(filename)\nprint(f'Saved {filename}')"
  }
]

##Critical : try to give professional design code for each component.
"""


def _codegen_goal_section(target_component_count: int) -> str:
    t = max(1, min(6, int(target_component_count)))
    if t == 1:
        return (
            "**Component count (required):** Emit **exactly one** top-level JSON key "
            "(one DXF script). Pick the **single most important** fabricated part on the drawing "
            "(prefer a clear numbered detail or primary plate/bracket). Do **not** output "
            "additional keys.\n\n"
            "---\n\n"
            "## Goal: manufacturing-style extraction (match professional shop output)\n\n"
            "1. **Single part this run:** Build **one** cohesive fabrication model; combine views "
            "only when they describe that **same** item—not multiple unrelated DXFs.\n\n"
            "2. **Discipline:** One clear script; prefer **MTEXT** for sizes where helpful.\n\n"
        )
    return (
        f"**Component count (required):** Return **3–6** top-level JSON keys "
        "(each key = one DXF script for one component). "
        f"Prefer around **{max(3, min(6, t))}** components when supported by the drawing. "
        "**Never output more than 6** keys. If the drawing clearly has fewer than 3 justified fabricated "
        "items, output only real parts and do not hallucinate.\n\n"
        "---\n\n"
        "## Goal: manufacturing-style extraction (match professional shop output)\n\n"
        "1. **Find identifiable parts** (target 3–6, never more than 6):\n"
        "   - **Numbered part blocks** (e.g. 3-digit callouts): prefer **one JSON key per distinct "
        "numbered detail**, using `part_740`, `part_721`, etc.\n"
        "   - **Priority order (strict):** pick **small, complex, connection-critical** fabricated parts first "
        "(gusset/cleat/bracket/lug plates, splice/base plates, stiffeners/fish plates, hole templates). "
        "De-prioritize long/simple members unless the drawing explicitly shows them as separate fabricated parts.\n"
        "   - **Tables / BOM rows**: read **QTY**, **material**, **section**, **thickness**, "
        "**length** where shown; echo key fields as **MTEXT** on layer ANNOTATION.\n"
        "   - **Assemblies / elevations:** **Decompose** into fabrication-oriented pieces when "
        "the drawing implies separate items.\n"
        "   - **If the sheet shows more than 6 parts:** keep the **6** most important; "
        "**do not** exceed 6 keys.\n"
        "   - **If fewer than 3** clearly separable items exist: output only justified items; "
        "do not invent hardware.\n\n"
        "2. **Part count discipline:** Prefer **3–6** scripts (cap 6). "
        "Merge identical multiples into **one script** with QTY in ANNOTATION when the drawing "
        "says so.\n\n"
    )


CODEGEN_INSTRUCTION_TAIL = """3. **Geometry fidelity**
   - Build the **2D plan/profile** of that part: outline as `LWPOLYLINE`/`LINE`, chamfers/cuts as segmented lines, holes as `msp.add_circle` in mm.
   - **Dimensions**: **Prefer numbers printed on the image.** Read extension lines and digit strings (including comma decimals if European style). Use **Ø / R** callouts for hole and fillet radii (circle radius = Ø/2).
   - **Hole grids**: When coordinates are chained from edges, reproduce those **X/Y from datum** in code variables; place circles accordingly.
   - If a number is **unreadable**, interpolate from proportions **once**, prefix annotation with `EST` or `~`, and keep relative layout consistent.

   - **Engineering-style dimension communication:** use extension lines + dimension line + arrowheads +
     numeric text (e.g. `350`, `Ø18`, `4× Ø22 @ PCD 120`). This should look like a real shop-detail
     drawing. If native ezdxf dimension entities are risky, draw arrowheads/dimension lines manually
     using `LINE`/`LWPOLYLINE` on the `DIMENSION` layer and put the numeric value in `MTEXT` on
     the `ANNOTATION` layer.

4. **Annotations (required in every script)**
   - Layers: create `GEOMETRY`, `DIMENSION`, `ANNOTATION` (e.g. `doc.layers.add("GEOMETRY")`).
   - Place **visible text**: part ID/title, **overall W×L** or length, **hole notes** (`Ø18`, `4× Ø24 PCD…`), **thickness/section** (`PL10`, `ISA 75×75×6`), **QTY** and **material** if present.
   - **ezdxf MTEXT (strict):**
     - Use **`char_height`** in `dxfattribs` for text size — **never** `height` (raises *Invalid DXF attribute "height" for entity MTEXT*).
     - Position: either pass `insert` inside `dxfattribs`, OR call `mt.set_location((x, y), attachment_point=...)`.
     - Do **not** use `mt.set_location(insert=(x,y), ...)` (can raise a TypeError in ezdxf).
     - Valid example: `mt = msp.add_mtext(..., dxfattribs={"layer": "ANNOTATION", "char_height": 5.58}); mt.set_location((x, y), attachment_point=1)`.
   - **`msp.add_text`:** uses **`height`** (not `char_height`) and typically **`insert`** `(x, y)`; keep **2–5 mm** for readability at 1:1.
   - **Engineering-style dimensioning (shop-detail style):**
     - Always include extension lines + dimension line + arrowheads + numeric text, and add part/feature callouts.
     - Draw engineering dimension graphics using basic `LINE`/`LWPOLYLINE` plus `msp.add_mtext` for numeric values if native ezdxf dimension entities are risky.
   - **Avoid ezdxf dimension API misuses:**
     - Do **not** call `dim.set_text(..., align=...)`.
     - Do **not** call nonexistent helpers like `dim.set_text_align_bottom()` / `dim.set_text_align_left()`.
     - If you use `msp.add_linear_dim`, keep it API-safe: `base=...`, `p1=...`, `p2=...`, and call `.set_text("...")` with no unsupported keyword arguments.

5. **Key naming**
   - **Primary**: printed detail/callout number.
   - **Secondary**: role + index (`cross_arm_top`, `gusset_10`) if no number is visible.

6. **Script contract** (each value string is a full program)
   - Imports: **only** `sys`, `ezdxf`, `math`, optional `pathlib`.
   - Read `out = sys.argv[1]`; `doc = ezdxf.new("R2010", setup=True)`; `doc.units = ezdxf.units.MM`.
   - Draw **only** that part's geometry + annotations; `doc.saveas(out)` once.
   - No subprocess, network, file reads beyond save, `eval`/`exec`.

7. **Order of work inside your head** (must reflect in code quality)
   - Classify views/schedules → unify constraints for one fabrication model per part (do not flatten unrelated views into one sketch).
   - Read datums and dimension chains → build the **parametric spec** (variables/dict) → derive hole grids from labels/symmetry/pitch, not pixels.
   - Outline from overall dims → holes via loops from the spec → centerlines/conventions as needed → ANNOTATION text.
   - **Self-check** (symmetry, counts, chain sums, edge matches) before returning JSON; fix inconsistencies in the code you emit.
    - Lay out entities shop-drawing style (alignment, spacing, non-overlapping notes).
    - If helpful, infer simple 3D intent from multi-view drawings (front/top/side) to disambiguate
      fabrication geometry, but still output the final deliverable as fabrication-ready DXF entities.

Prioritize **traceability**: another engineer should see **which printed dimensions** drove the DXF. Stay compact in Python but **do not** skip holes or part metadata when they appear on the sheet."""


def build_gemini_codegen_user_prompt(*, target_component_count: int) -> str:
    """Assemble the Gemini instruction text (component count changes the goal section)."""
    return (
        CODEGEN_INSTRUCTION_LEAD
        + _codegen_goal_section(target_component_count)
        + CODEGEN_INSTRUCTION_TAIL
    )


COMPONENT_PLAN_INSTRUCTION = """You are a senior mechanical/structural drafting assistant. The input is **always** treated as an **engineering production context** (shop drawings, part portfolios, lattice/component sheets, or assembly elevations).

Your job in this stage is **analysis only**: identify the **small, complex, must-have fabrication components** needed to build the structure shown in the image. Focus on parts that require **separate fabrication drawings**.

Return ONLY valid JSON (no markdown fences, no commentary). Shape:
{
  "component_id_1": "3–4 line description: Name + what it is + key dimensions/features + hole patterns + thickness/section + any symbols/callouts to use (Ø, R, PCD, slots) + dimensioning guidance (datums, chain dims).",
  "component_id_2": "..."
}

Component selection rule (strict):
- Prioritize **small, complex, connection-critical fabrication components** first.
- Prefer: gusset plates, cleats, brackets, lug plates, splice/base plates, stiffeners/fish plates, hole templates, insulator brackets, connection plates.
- De-prioritize: long/simple members (straight bars, long chords, plain angles) unless explicitly shown as separate fabricated parts.

Key naming:
- Use stable snake_case IDs. If a printed detail/part number exists, include it (e.g. `part_740_gusset_plate`).
- Otherwise use role-based IDs (e.g. `insulator_lug_plate_upper`, `tower_leg_base_plate`).

Critical:
- Descriptions must be detailed enough that another engineer can create a professional shop detail from the text alone.
- Prefer dimensions printed on the image; if something is unreadable, mark it `EST`.
"""


def parse_component_plan_json_payload(text: str) -> dict[str, str]:
    """Parse Stage-1 planner response into component_id -> description."""
    t = _repair_llm_json_string_control_chars(_strip_json_fence(text))
    data = _decode_json_codegen_root(t)
    if not isinstance(data, dict):
        raise ValueError("Planner JSON must be an object mapping component_id -> description")
    out: dict[str, str] = {}
    for k, v in data.items():
        if not isinstance(k, str) or not isinstance(v, str):
            continue
        kk = k.strip()
        vv = v.strip()
        if kk and vv:
            out[kk] = vv
    if not out:
        raise ValueError("Planner JSON contained no component descriptions")
    return out


def _batched_keys(keys: list[str], batch_size: int) -> list[list[str]]:
    if batch_size < 1:
        batch_size = 1
    return [keys[i : i + batch_size] for i in range(0, len(keys), batch_size)]


def _build_stage2_prompt_for_batch(
    *,
    target_component_count: int,
    required_components: dict[str, str],
    compact: bool = False,
) -> str:
    """Stage-2 codegen prompt: keep base prompt, add strict 'required components' tail."""
    base = build_gemini_codegen_user_prompt(target_component_count=target_component_count)
    comp_lines = "\n".join(f'- "{cid}": {desc}' for cid, desc in required_components.items())
    compact_tail = ""
    if compact:
        # Keep the existing prompt, but add a small constraint to reduce truncation risk.
        compact_tail = (
            "\n\n**Compactness (required):** Keep the Python script concise to avoid truncation. "
            "Avoid long helper libraries, excessive comments, and repeated dimension helper functions. "
            "Prefer simple geometry + essential annotations/dimensions only.\n"
        )
    tail = (
        "\n\n---\n\n"
        f"**Required components (strict):** Emit **exactly {len(required_components)}** "
        "top-level JSON keys, and they **must match** these component ids exactly. "
        "Do **not** emit any other keys.\n\n"
        "Use the descriptions below as the authoritative part intent for what to draw.\n\n"
        f"{comp_lines}\n"
    )
    return base + compact_tail + tail




def _gemini_api_key() -> str:
    k = (
        os.environ.get("GEMINI_API_KEY", "").strip()
        or os.environ.get("GOOGLE_API_KEY", "").strip()
    )
    if not k:
        raise RuntimeError("Set GEMINI_API_KEY or GOOGLE_API_KEY for Gemini CAD codegen.")
    return k


def _load_input_bgr(path: Path, *, pdf_page: int, pdf_dpi: float) -> Any:
    p = str(path.resolve())
    suf = path.suffix.lower()
    if suf == ".pdf":
        img = load_pdf_page_as_bgr(p, page_index=pdf_page, dpi=pdf_dpi)
    else:
        img = load_image_bgr(p)
    if img is None:
        raise FileNotFoundError(f"Could not load image: {path}")
    return img


def _bgr_to_png_bytes(bgr: Any, max_side: int) -> bytes:
    h, w = bgr.shape[:2]
    m = max(h, w)
    if max_side > 0 and m > max_side:
        s = max_side / float(m)
        bgr = cv2.resize(
            bgr,
            (max(1, int(w * s)), max(1, int(h * s))),
            interpolation=cv2.INTER_AREA,
        )
    ok, buf = cv2.imencode(".png", bgr)
    if not ok:
        raise RuntimeError("Failed to encode PNG for Gemini request")
    return buf.tobytes()


def _strip_json_fence(text: str) -> str:
    t = text.strip()
    if t.startswith("```"):
        t = re.sub(r"^```[a-zA-Z0-9]*\s*", "", t)
        t = re.sub(r"\s*```\s*$", "", t)
    return t.strip()


def _first_top_level_json_start(s: str) -> int:
    """Index of the first `{` or `[` that starts the payload (not inside a JSON string)."""
    in_string = False
    escape = False
    for i, c in enumerate(s):
        if in_string:
            if escape:
                escape = False
            elif c == "\\":
                escape = True
            elif c == '"':
                in_string = False
            continue
        if c == '"':
            in_string = True
            continue
        if c in "{[":
            return i
    return -1


def _repair_llm_json_string_control_chars(s: str) -> str:
    """Escape raw U+0000–U+001F inside JSON string literals.

    Models often paste Python source into JSON values using real line breaks instead of
    ``\\n``, which makes :func:`json.loads` raise *Invalid control character*.
    """
    start = _first_top_level_json_start(s)
    if start < 0:
        return s
    out: list[str] = [s[:start]]
    in_string = False
    escape = False
    for c in s[start:]:
        if not in_string:
            if c == '"':
                in_string = True
            out.append(c)
            continue
        if escape:
            escape = False
            out.append(c)
            continue
        if c == "\\":
            escape = True
            out.append(c)
            continue
        if c == '"':
            in_string = False
            out.append(c)
            continue
        o = ord(c)
        if o < 0x20:
            if c == "\n":
                out.append("\\n")
            elif c == "\r":
                out.append("\\r")
            elif c == "\t":
                out.append("\\t")
            else:
                out.append(f"\\u{o:04x}")
            continue
        out.append(c)
    return "".join(out)


def _decode_json_string_literal(s: str, start: int) -> tuple[str, int] | None:
    """Decode one JSON string starting at ``start`` (must point at ``\"``)."""
    if start >= len(s) or s[start] != '"':
        return None
    dec = json.JSONDecoder()
    try:
        val, end = dec.raw_decode(s, start)
    except json.JSONDecodeError:
        return None
    if not isinstance(val, str):
        return None
    return val, end


def _salvage_codegen_string_pairs(t: str) -> dict[str, str]:
    """When the model truncates mid-response, recover fully closed ``\"id\": \"code\"`` pairs."""
    out: dict[str, str] = {}
    i = 0
    n = len(t)
    while i < n:
        if t[i] != '"':
            i += 1
            continue
        kr = _decode_json_string_literal(t, i)
        if kr is None:
            i += 1
            continue
        key, j = kr
        k = j
        while k < n and t[k] in " \t\n\r":
            k += 1
        if k >= n or t[k] != ":":
            i += 1
            continue
        k += 1
        while k < n and t[k] in " \t\n\r":
            k += 1
        vr = _decode_json_string_literal(t, k)
        if vr is None:
            break
        val, after = vr
        if key and val:
            out[key] = val.replace("\r\n", "\n")
        i = after
    return out


def _decode_json_codegen_root(t: str) -> Any:
    t = t.strip()
    exc: json.JSONDecodeError | None = None
    try:
        return json.loads(t)
    except json.JSONDecodeError as e:
        exc = e
    start = _first_top_level_json_start(t)
    if start < 0:
        raise ValueError(
            "Expected a JSON object or array in the model response"
        ) from exc
    fragment = t[start:]
    try:
        data, _end = json.JSONDecoder().raw_decode(fragment)
        return data
    except json.JSONDecodeError as e:
        suffix = ""
        msg = str(e)
        if "Unterminated string" in msg or "Expecting" in msg:
            suffix = (
                "; model output likely hit the token limit (use "
                "`--gemini-max-output-tokens 65536` if below the model cap, or "
                "fewer/lighter components in the prompt / smaller image)."
            )
        raise ValueError(f"{msg}{suffix}") from e


def parse_codegen_json_payload(
    text: str,
    *,
    parse_warnings: list[str] | None = None,
) -> dict[str, str]:
    """Parse Gemini response into component_id -> python source."""
    t = _repair_llm_json_string_control_chars(_strip_json_fence(text))
    try:
        data = _decode_json_codegen_root(t)
    except ValueError as e:
        salvaged = _salvage_codegen_string_pairs(t)
        chunk_out: dict[str, str] = {}
        for _k, code in salvaged.items():
            if code:
                chunk_out[_k] = code
        if not chunk_out:
            raise ValueError(
                f"{e}\n"
                "Salvage found no complete key/script pairs (truncation likely inside the first "
                "JSON string). Try fewer components, lower image detail (--max-side), raise "
                "output tokens if supported, or split the drawing into separate runs."
            ) from e
        if parse_warnings is not None:
            parse_warnings.append(
                f"JSON was truncated or invalid ({e}); recovered {len(chunk_out)} "
                "complete component script(s). Re-run with a smaller prompt/image or fewer "
                "parts if you need every script."
            )
        return chunk_out
    out: dict[str, str] = {}
    chunks: list[dict[Any, Any]] = []
    if isinstance(data, dict):
        chunks = [data]
    elif isinstance(data, list):
        chunks = [x for x in data if isinstance(x, dict)]
    else:
        raise ValueError("Top-level JSON must be an object or array of objects")
    for item in chunks:
        for k, v in item.items():
            if not isinstance(k, str) or not isinstance(v, str):
                continue
            key = k.strip()
            if not key:
                continue
            code = str(v).replace("\r\n", "\n")
            if code:
                out[key] = code
    if not out:
        raise ValueError("No component scripts found in parsed JSON")
    return out


def _safe_stem(name: str) -> str:
    s = re.sub(r"[^\w\-+]+", "_", name.strip())[:64].strip("_").strip("-")
    return s or "component"


def sanitize_codegen_python_source(source: str) -> tuple[str, list[str]]:
    """Patch known LLM-hallucinated ezdxf snippets before executing generated scripts.

    ``ezdxf.new(..., setup=True)`` ships a dimension style named ``EZDXF``. Models often
    invent names like ``EZDXF_DIMSTYLE_STD``; guarding with ``if ... in doc.dimstyles``
    never runs because that entry does not exist.
    """
    applied: list[str] = []
    out = source.replace("\r\n", "\n")

    # Fix common ezdxf kwarg typo: dxfattrib -> dxfattribs
    if "dxfattrib=" in out:
        out2 = re.sub(r"\bdxfattrib\s*=", "dxfattribs=", out)
        if out2 != out:
            applied.append("replaced dxfattrib= with dxfattribs=")
            out = out2

    # Fix MTEXT paragraph escape sequences in Python string literals: "\P" -> "\\P"
    # (keeps the intended DXF control code while avoiding future Python errors)
    out2 = re.sub(r"(?<!\\)\\P", r"\\\\P", out)
    if out2 != out:
        applied.append("escaped MTEXT paragraph control \\P -> \\\\P")
        out = out2

    # Fix invalid attachment_point enums hallucinated by the model.
    # ezdxf expects an integer attachment point 1..9 for MTEXT set_location(..., attachment_point=?)
    ap_map = {
        "TOP_LEFT": 1,
        "TOP_CENTER": 2,
        "TOP_RIGHT": 3,
        "MIDDLE_LEFT": 4,
        "MIDDLE_CENTER": 5,
        "MIDDLE_RIGHT": 6,
        "BOTTOM_LEFT": 7,
        "BOTTOM_CENTER": 8,
        "BOTTOM_RIGHT": 9,
    }

    def _ap_repl(m: re.Match) -> str:
        name = str(m.group(1))
        v = ap_map.get(name)
        if v is None:
            return m.group(0)
        applied.append(f"attachment_point enum {name} -> {v}")
        return f"attachment_point={v}"

    out2 = re.sub(
        r"attachment_point\s*=\s*ezdxf\.enums\.MTextParagraphAlignment\.([A-Z_]+)",
        _ap_repl,
        out,
    )
    if out2 != out:
        out = out2

    out, ezdxf_notes = _sanitize_common_ezdxf_runtime_misuses(out)
    applied.extend(ezdxf_notes)

    # Fix hallucinated ezdxf dimtype override enums (not present in many ezdxf versions).
    # Safer to omit `dimtype=` and let add_linear_dim infer orientation from points/base.
    if "ezdxf.enums.DimStyleOverride" in out:
        out2 = re.sub(
            r",?\s*dimtype\s*=\s*ezdxf\.enums\.DimStyleOverride\.[A-Z0-9_]+\s*,?",
            ",",
            out,
        )
        if out2 != out:
            applied.append("removed unsupported dimtype=ezdxf.enums.DimStyleOverride.* argument")
            out = out2
        out2 = re.sub(r"\bezx?dxf\.enums\.DimStyleOverride\.[A-Z0-9_]+\b", "0", out)
        if out2 != out:
            out = out2

    subs = (
        ("EZDXF_DIMSTYLE_STD", "EZDXF"),
        ("EZDXF_DIMSTYLE_STANDARD", "EZDXF"),
    )
    for bad, good in subs:
        pat = re.compile(
            rf"(dimstyles\.duplicate_entry\s*\(\s*)['\"]{re.escape(bad)}['\"]",
            re.IGNORECASE,
        )

        def _repl(m: re.Match, *, good_name: str = good, bad_name: str = bad) -> str:
            applied.append(
                f"dimstyles.duplicate_entry source {bad_name!r} -> {good_name!r}"
            )
            return f'{m.group(1)}"{good_name}"'

        out = pat.sub(_repl, out)
    healed, heal_notes = _heal_truncated_codegen_python(out)
    out = healed
    applied.extend(heal_notes)
    out, undef_notes = _strip_undefined_symbol_attribute_lines(out)
    applied.extend(undef_notes)
    out, save_notes = _ensure_codegen_saves_dxf(out)
    applied.extend(save_notes)
    return out, applied


def _sanitize_common_ezdxf_runtime_misuses(source: str) -> tuple[str, list[str]]:
    """Patch ezdxf API misuses that frequently crash model-generated scripts."""
    notes: list[str] = []
    s = source.replace("\r\n", "\n")
    lines = s.splitlines()
    out_lines: list[str] = []

    # 1) ezdxf LWPolyline has no `.set_bulges(...)` method in common versions.
    #    Bulges should be supplied at creation time; for safety just drop the call.
    for i, ln in enumerate(lines):
        if ".set_bulges(" in ln:
            notes.append(f"line {i + 1}: removed unsupported LWPolyline.set_bulges(...) call")
            continue
        out_lines.append(ln)

    s2 = "\n".join(out_lines) + ("\n" if s.endswith("\n") else "")

    # 2) add_mtext() must be called with text (string) plus optional attrib dict.
    #    Models sometimes call add_mtext(a, b, c, ...) which raises TypeError.
    #    Replace those calls with a safe single-string note.
    def _fix_add_mtext_call(m: re.Match) -> str:
        notes.append("replaced invalid msp.add_mtext(...) call with safe single-string note")
        return "msp.add_mtext('NOTE: annotation simplified (sanitized)', dxfattribs={'layer': 'ANNOTATION', 'char_height': 5.58})"

    # Match a single-line call with >1 positional args before any dxfattribs=
    s3 = re.sub(
        r"\bmsp\.add_mtext\(\s*[^'\"]+?\s*,\s*[^'\"]+?\)",
        _fix_add_mtext_call,
        s2,
    )
    return s3, notes


def _strip_undefined_symbol_attribute_lines(source: str) -> tuple[str, list[str]]:
    """Remove lines like `mt_x.set_location(...)` when `mt_x` was never assigned.

    This commonly occurs when truncation healing removes the `mt_x = msp.add_mtext(...)` line
    but leaves subsequent `mt_x.set_location(...)` calls, which then crash at runtime.
    """
    notes: list[str] = []
    s = source.replace("\r\n", "\n")
    lines = s.splitlines()

    assigned: set[str] = set()
    # Collect simple assignments (`name = ...`) across the script.
    for ln in lines:
        m = re.match(r"^\s*([A-Za-z_]\w*)\s*=", ln)
        if m:
            assigned.add(m.group(1))

    out_lines: list[str] = []
    removed = 0
    for i, ln in enumerate(lines):
        m = re.match(r"^\s*([A-Za-z_]\w*)\s*\.\s*set_location\s*\(", ln)
        if m:
            name = m.group(1)
            if name not in assigned:
                removed += 1
                notes.append(
                    f"line {i + 1}: removed set_location on undefined symbol {name!r}"
                )
                continue
        out_lines.append(ln)

    if removed:
        return "\n".join(out_lines) + ("\n" if s.endswith("\n") else ""), notes
    return s, notes

def _ensure_codegen_saves_dxf(source: str) -> tuple[str, list[str]]:
    """Ensure model-generated scripts always save to sys.argv[1].

    Some truncation-heal paths remove trailing `doc.saveas(...)`, causing "exit 0 but DXF missing".
    """
    notes: list[str] = []
    s = source.replace("\r\n", "\n")
    if "doc.saveas(" in s and "doc = " in s:
        return s, notes
    # If the script already defines `out = sys.argv[1]`, reuse it; otherwise add a robust footer.
    footer = (
        "\n\n"
        "# --- cursor recovery footer: ensure DXF is written ---\n"
        "if 'doc' not in globals():\n"
        "    doc = ezdxf.new('R2010', setup=True)\n"
        "    doc.units = ezdxf.units.MM\n"
        "    msp = doc.modelspace()\n"
        "try:\n"
        "    out = sys.argv[1]\n"
        "except Exception:\n"
        "    out = 'out.dxf'\n"
        "doc.saveas(out)\n"
    )
    notes.append("appended recovery footer to ensure doc/saveas(out) exists")
    return s.rstrip() + footer, notes


def _strip_dangling_set_attribut_calls(source: str) -> tuple[str, list[str]]:
    """Drop truncated chained ``.set_attribut(`` tails left by model truncation."""
    notes: list[str] = []
    lines = source.splitlines()
    changed = False
    for i, line in enumerate(lines):
        needle = ".set_attribut("
        pos = line.find(needle)
        if pos < 0:
            continue
        tail = line[pos:]
        if ")" in tail:
            continue
        lines[i] = line[:pos].rstrip()
        changed = True
        notes.append(
            f"line {i + 1}: removed dangling '.set_attribut(' chain from truncated call"
        )
    if not changed:
        return source, notes
    return "\n".join(lines) + ("\n" if source.endswith("\n") else ""), notes


def _heal_truncated_codegen_python(source: str) -> tuple[str, list[str]]:
    """Best-effort recovery for partially truncated model-generated Python."""
    notes: list[str] = []
    out, strip_notes = _strip_dangling_set_attribut_calls(source)
    notes.extend(strip_notes)
    lines = out.splitlines()

    # If still syntactically invalid, trim trailing lines until code compiles.
    # This preserves as much geometry as possible while avoiding hard script failure.
    while lines:
        candidate = "\n".join(lines) + ("\n" if out.endswith("\n") else "")
        try:
            compile(candidate, "<gemini_codegen>", "exec")
            return candidate, notes
        except SyntaxError as e:
            if e.lineno is None:
                break
            ln = int(e.lineno)
            if ln >= len(lines):
                removed = lines.pop()
                notes.append(
                    f"removed trailing line {len(lines) + 1} after SyntaxError: {removed[:120]}"
                )
                continue
            # If parser points to a specific bad line, drop that line and retry once.
            bad = lines.pop(max(0, ln - 1))
            notes.append(f"removed invalid line {ln} after SyntaxError: {bad[:120]}")
            continue

    return out, notes


def merge_dxfs_horizontal(
    labeled_paths: list[tuple[str, Path]],
    out_path: Path,
    *,
    gap_mm: float = 40.0,
) -> None:
    """Append each DXF's MODELSPACE into a new document, translating along +X."""
    dst = ezdxf.new("R2010", setup=True)
    dst.units = ezdxf.units.MM
    cursor_x = 0.0

    for _label, src_path in labeled_paths:
        if not src_path.is_file():
            continue
        try:
            src = ezdxf.readfile(str(src_path))
        except Exception:
            continue
        msp_src = src.modelspace()
        try:
            ext = bbox.extents(msp_src)
            min_x = float(ext.extmin.x) if ext.has_data else 0.0
            width = float(ext.size.x) if ext.has_data else 80.0
        except Exception:
            min_x, width = 0.0, 80.0

        n_before = len(list(dst.modelspace()))
        try:
            Importer(src, dst).import_modelspace()
        except Exception:
            continue
        ents = list(dst.modelspace())[n_before:]
        tx = cursor_x - min_x
        for e in ents:
            try:
                e.transform(Matrix44.translate(tx, 0.0, 0.0))
            except Exception:
                continue
        cursor_x += max(width, 1.0) + float(gap_mm)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    dst.saveas(str(out_path))


def merge_dxfs_grid(
    labeled_paths: list[tuple[str, Path]],
    out_path: Path,
    *,
    gap_mm: float = 40.0,
    ncols: int = 3,
    cell_width_mm: float | None = None,
    cell_height_mm: float | None = None,
    center_in_cell: bool = True,
    scale_to_fit: bool = True,
) -> None:
    """Append each DXF's MODELSPACE into a new document, tiling in rows of ``ncols`` along +X, next row −Y.

    Uses a uniform cell size (max width/height across parts) for professional, equal spacing.
    """
    if ncols < 1:
        ncols = 1
    dst = ezdxf.new("R2010", setup=True)
    dst.units = ezdxf.units.MM
    # First pass: measure extents to compute uniform cell size (or validate requested fixed cell size).
    measured: list[tuple[Path, float, float, float, float]] = []
    cell_w = 80.0
    cell_h = 80.0
    for _label, src_path in labeled_paths:
        if not src_path.is_file():
            continue
        try:
            src = ezdxf.readfile(str(src_path))
        except Exception:
            continue
        msp_src = src.modelspace()
        try:
            ext = bbox.extents(msp_src)
            min_x = float(ext.extmin.x) if ext.has_data else 0.0
            min_y = float(ext.extmin.y) if ext.has_data else 0.0
            width = float(ext.size.x) if ext.has_data else 80.0
            height = float(ext.size.y) if ext.has_data else 80.0
        except Exception:
            min_x, min_y = 0.0, 0.0
            width, height = 80.0, 80.0
        width = max(float(width), 1.0)
        height = max(float(height), 1.0)
        cell_w = max(cell_w, width)
        cell_h = max(cell_h, height)
        measured.append((src_path, min_x, min_y, width, height))

    # If caller requested a fixed cell size, use it (must be >= max extents to avoid overlap).
    if cell_width_mm is not None:
        cell_w = max(float(cell_width_mm), 1.0)
    if cell_height_mm is not None:
        cell_h = max(float(cell_height_mm), 1.0)

    # Second pass: import and place each part into a uniform grid cell (equal spacing).
    for idx, (src_path, min_x, min_y, _w, _h) in enumerate(measured):
        col = idx % ncols
        row = idx // ncols
        x0 = col * (cell_w + float(gap_mm))
        y0 = -row * (cell_h + float(gap_mm))

        try:
            src = ezdxf.readfile(str(src_path))
        except Exception:
            continue
        n_before = len(list(dst.modelspace()))
        try:
            Importer(src, dst).import_modelspace()
        except Exception:
            continue
        ents = list(dst.modelspace())[n_before:]
        # Normalize each part so its extmin is at (0,0), then translate into the cell.
        # Optionally center within the fixed cell for professional sheet-style layout.
        s = 1.0
        if scale_to_fit:
            sx = float(cell_w) / float(_w) if _w > 0 else 1.0
            sy = float(cell_h) / float(_h) if _h > 0 else 1.0
            s = max(0.01, min(1.0, sx, sy))
        sw = float(_w) * s
        sh = float(_h) * s

        if center_in_cell:
            off_x = max(0.0, (cell_w - sw) / 2.0)
            off_y = max(0.0, (cell_h - sh) / 2.0)
        else:
            off_x = 0.0
            off_y = 0.0

        # Transform order:
        # 1) translate so extmin -> origin
        # 2) scale to fit (optional)
        # 3) translate into cell (and center)
        tx0 = -float(min_x)
        ty0 = -float(min_y)
        tx1 = x0 + off_x
        ty1 = y0 + off_y

        m = Matrix44.translate(tx0, ty0, 0.0) @ Matrix44.scale(s, s, 1.0) @ Matrix44.translate(
            tx1, ty1, 0.0
        )
        for e in ents:
            try:
                e.transform(m)
            except Exception:
                continue

    out_path.parent.mkdir(parents=True, exist_ok=True)
    dst.saveas(str(out_path))


@dataclass
class GeminiCadCodegenConfig:
    input_path: Path
    output_dir: Path
    gemini_model: str = "gemini-2.5-flash"
    two_stage: bool = True
    stage1_model: str = "gemini-2.0-flash"
    stage2_model: str = "gemini-2.5-flash"
    stage2_batch_size: int = 3
    stage2_max_workers: int = 4
    pdf_page: int = 0
    pdf_dpi: float = 150.0
    max_side: int = 2048
    layout_gap_mm: float = 40.0
    assembly_layout: str = "horizontal"
    grid_columns: int = 3
    grid_cell_width_mm: float | None = None
    grid_cell_height_mm: float | None = None
    grid_center_in_cell: bool = True
    grid_scale_to_fit: bool = True
    script_timeout_s: float = 90.0
    gemini_timeout_s: float = 600.0
    gemini_max_output_tokens: int = 65536
    sheet_report: bool = False
    sheet_gemini_max_output_tokens: int = SHEET_EXTRACT_OUTPUT_TOKENS
    target_component_count: int = 4
    gemini_single_json_call: bool = False


@dataclass
class GeminiCadCodegenResult:
    manifest_path: Path
    assembly_dxf: Path | None
    raw_model_text_path: Path
    ai_response_json_path: Path | None = None
    component_scripts: dict[str, Path] = field(default_factory=dict)
    component_dxfs: dict[str, Path] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    script_errors: dict[str, str] = field(default_factory=dict)
    component_sheet_json: Path | None = None
    component_sheet_markdown: Path | None = None
    component_sheet_warnings: list[str] = field(default_factory=list)
    component_plan_json_path: Path | None = None
    component_plan_raw_text_path: Path | None = None


def _gemini_codegen_multisegment_raw_and_components(
    *,
    api_key: str,
    cfg: GeminiCadCodegenConfig,
    png_bytes: bytes,
    segment_count: int,
    warnings: list[str],
) -> tuple[str, dict[str, str]]:
    """One Gemini request per part so each script fits in the output token budget."""
    blocks: list[str] = []
    merged: dict[str, str] = {}
    prior_ids: set[str] = set()
    for idx in range(segment_count):
        if prior_ids:
            tail = (
                f"\n\n**Segment {idx + 1} of {segment_count}:** Emit **exactly one** top-level "
                "JSON key (one DXF script). Pick a **different** fabricated component than any of "
                f"these ids already emitted in this run: {', '.join(sorted(prior_ids))}."
            )
        else:
            tail = (
                f"\n\n**Segment {idx + 1} of {segment_count}:** Emit **exactly one** top-level "
                "JSON key (first of several parts for this drawing)."
            )
        prompt = (
            build_gemini_codegen_user_prompt(target_component_count=cfg.target_component_count)
            + tail
        )
        raw_seg = call_gemini_generate_content_raw(
            api_key=api_key,
            model=cfg.gemini_model,
            png_bytes=png_bytes,
            user_prompt=prompt,
            timeout_s=cfg.gemini_timeout_s,
            max_output_tokens=cfg.gemini_max_output_tokens,
        )
        blocks.append(f"<!-- gemini_codegen segment {idx + 1} of {segment_count} -->\n{raw_seg}")
        try:
            chunk = parse_codegen_json_payload(raw_seg, parse_warnings=warnings)
        except ValueError as e:
            warnings.append(f"Codegen segment {idx + 1}/{segment_count} JSON parse failed: {e}")
            continue
        took_new = False
        for k, v in chunk.items():
            if k in merged:
                warnings.append(
                    f"Codegen segment {idx + 1}/{segment_count}: duplicate key {k!r}; skipped."
                )
                continue
            merged[k] = v
            prior_ids.add(k)
            took_new = True
            break
        if not took_new:
            warnings.append(
                f"Codegen segment {idx + 1}/{segment_count} added no new component "
                f"(returned {list(chunk.keys())!r}; already have {sorted(prior_ids)!r})."
            )
    return "\n\n".join(blocks), merged


def run_gemini_cad_codegen(cfg: GeminiCadCodegenConfig) -> GeminiCadCodegenResult:
    api_key = _gemini_api_key()
    output_dir = _resolved_output_dir(cfg.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = cfg.input_path.stem
    warnings: list[str] = []
    script_errors: dict[str, str] = {}
    sheet_json_path: Path | None = None
    sheet_md_path: Path | None = None
    sheet_warnings: list[str] = []

    bgr = _load_input_bgr(cfg.input_path, pdf_page=cfg.pdf_page, pdf_dpi=cfg.pdf_dpi)
    png_bytes = _bgr_to_png_bytes(bgr, cfg.max_side)

    if cfg.sheet_report:
        from drawing_to_dxf.component_sheet_report import (
            ComponentSheetExtractConfig,
            run_component_sheet_extract,
        )

        try:
            ser = run_component_sheet_extract(
                ComponentSheetExtractConfig(
                    input_path=cfg.input_path,
                    output_dir=output_dir,
                    gemini_model=cfg.gemini_model,
                    pdf_page=cfg.pdf_page,
                    pdf_dpi=cfg.pdf_dpi,
                    max_side=cfg.max_side,
                    gemini_timeout_s=cfg.gemini_timeout_s,
                    gemini_max_output_tokens=cfg.sheet_gemini_max_output_tokens,
                )
            )
            sheet_json_path = ser.json_path
            sheet_md_path = ser.markdown_path
            sheet_warnings = list(ser.warnings)
            for sw in sheet_warnings:
                warnings.append(f"Sheet report: {sw}")
        except Exception as e:
            warnings.append(f"Sheet report failed: {e}")

    # Token limits are handled by batching/segmentation, so allow more than 8 parts per run.
    t_req = max(1, min(60, int(cfg.target_component_count)))
    plan_json_path: Path | None = None
    plan_raw_path: Path | None = None

    # In two-stage mode, we do:
    #   Stage 1 (gemini-2.0-flash): plan component ids + descriptions
    #   Stage 2 (gemini-2.5-flash): codegen for those ids in batches of N, in parallel
    two_stage_components: dict[str, str] | None = None
    two_stage_raw_blocks: list[str] = []
    if cfg.two_stage:
        plan_raw_path = output_dir / f"{stem}_gemini_component_plan_raw.txt"
        plan_prompt = (
            COMPONENT_PLAN_INSTRUCTION
            + f"\n\n**Component count (required):** Return **exactly {t_req}** keys.\n"
        )
        plan_raw = call_gemini_generate_content_raw(
            api_key=api_key,
            model=cfg.stage1_model,
            png_bytes=png_bytes,
            user_prompt=plan_prompt,
            timeout_s=cfg.gemini_timeout_s,
            max_output_tokens=min(int(cfg.gemini_max_output_tokens), 8192),
        )
        plan_raw_path.write_text(plan_raw, encoding="utf-8")
        try:
            component_plan = parse_component_plan_json_payload(plan_raw)
            # Hard discipline: keep only the first t_req components if the planner over-emits.
            ordered_ids = list(component_plan.keys())[:t_req]
            component_plan = {k: component_plan[k] for k in ordered_ids if k in component_plan}
        except Exception as e:
            warnings.append(f"Stage-1 planner JSON parse failed: {e}")
            component_plan = {}

        if component_plan:
            plan_json_path = output_dir / f"{stem}_gemini_component_plan.json"
            plan_json_path.write_text(
                json.dumps(component_plan, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )

            batches = _batched_keys(list(component_plan.keys()), int(cfg.stage2_batch_size))

            def _run_one_batch(batch_index: int, ids: list[str]) -> tuple[int, list[str], str]:
                req = {cid: component_plan[cid] for cid in ids if cid in component_plan}
                prompt = _build_stage2_prompt_for_batch(
                    target_component_count=len(req),
                    required_components=req,
                )
                raw = call_gemini_generate_content_raw(
                    api_key=api_key,
                    model=cfg.stage2_model,
                    png_bytes=png_bytes,
                    user_prompt=prompt,
                    timeout_s=cfg.gemini_timeout_s,
                    max_output_tokens=cfg.gemini_max_output_tokens,
                )
                return batch_index, ids, raw

            batch_raw_blocks: list[str] = []
            merged: dict[str, str] = {}
            max_workers = max(1, int(cfg.stage2_max_workers))
            with ThreadPoolExecutor(max_workers=max_workers) as ex:
                futs = [ex.submit(_run_one_batch, i, ids) for i, ids in enumerate(batches)]
                for fut in as_completed(futs):
                    try:
                        bi, ids, raw = fut.result()
                    except Exception as e:
                        warnings.append(f"Stage-2 batch failed: {e}")
                        continue
                    batch_raw_blocks.append(
                        f"<!-- gemini_codegen stage2 batch {bi + 1} of {len(batches)}: {ids!r} -->\n{raw}"
                    )
                    try:
                        chunk = parse_codegen_json_payload(raw, parse_warnings=warnings)
                    except ValueError as e:
                        warnings.append(
                            f"Stage-2 batch {bi + 1}/{len(batches)} JSON parse failed: {e}"
                        )
                        chunk = {}
                    # Keep exact requested ids only.
                    for cid in ids:
                        if cid in merged:
                            continue
                        if cid in chunk and chunk[cid]:
                            merged[cid] = chunk[cid]
                        else:
                            warnings.append(
                                f"Stage-2 batch {bi + 1}/{len(batches)} missing key {cid!r} in response."
                            )

            # Auto-retry any missing components as single-component requests (reduces truncation risk).
            missing = [cid for cid in component_plan.keys() if cid not in merged]
            if missing:
                warnings.append(
                    f"Stage-2 retry: {len(missing)} component(s) missing; retrying individually to avoid truncation."
                )
                for cid in missing:
                    try:
                        prompt = _build_stage2_prompt_for_batch(
                            target_component_count=1,
                            required_components={cid: component_plan[cid]},
                            compact=True,
                        )
                        raw_single = call_gemini_generate_content_raw(
                            api_key=api_key,
                            model=cfg.stage2_model,
                            png_bytes=png_bytes,
                            user_prompt=prompt,
                            timeout_s=cfg.gemini_timeout_s,
                            max_output_tokens=cfg.gemini_max_output_tokens,
                        )
                        batch_raw_blocks.append(
                            f"<!-- gemini_codegen stage2 retry single: {cid!r} -->\n{raw_single}"
                        )
                        chunk2 = parse_codegen_json_payload(raw_single, parse_warnings=warnings)
                        if cid in chunk2 and chunk2[cid] and cid not in merged:
                            merged[cid] = chunk2[cid]
                    except Exception as e:
                        warnings.append(f"Stage-2 single retry failed for {cid!r}: {e}")

            if merged:
                two_stage_components = merged
                two_stage_raw_blocks = batch_raw_blocks
                # We'll write stage-2 raw blocks into the standard raw_path below.
            else:
                warnings.append(
                    "Two-stage mode produced no component scripts; falling back to single-stage codegen."
                )

    use_multisegment = (t_req > 1 and not cfg.gemini_single_json_call) and not (
        cfg.two_stage and two_stage_components is not None
    )
    raw_path = output_dir / f"{stem}_gemini_codegen_raw.txt"
    ai_response_json_path: Path | None = None
    raw_path.parent.mkdir(parents=True, exist_ok=True)

    used_two_stage = cfg.two_stage and two_stage_components is not None
    if used_two_stage:
        components = dict(two_stage_components)
        raw_text = "\n\n".join(two_stage_raw_blocks).strip()
        raw_path.write_text(raw_text, encoding="utf-8")

    if use_multisegment:
        raw_text, components = _gemini_codegen_multisegment_raw_and_components(
            api_key=api_key,
            cfg=cfg,
            png_bytes=png_bytes,
            segment_count=t_req,
            warnings=warnings,
        )
        raw_path.write_text(raw_text, encoding="utf-8")
        if not components:
            warnings.append("Multi-segment codegen produced no component scripts.")
            manifest = {
                "stem": stem,
                "input": str(cfg.input_path.resolve()),
                "two_stage": bool(cfg.two_stage),
                "stage1_model": cfg.stage1_model,
                "stage2_model": cfg.stage2_model,
                "stage2_batch_size": int(cfg.stage2_batch_size),
                "stage2_max_workers": int(cfg.stage2_max_workers),
                "warnings": warnings,
                "target_component_count": t_req,
                "gemini_single_json_call": cfg.gemini_single_json_call,
                "raw_text_path": str(raw_path.resolve()),
                "component_plan_raw_text_path": str(plan_raw_path.resolve()) if plan_raw_path else None,
                "component_plan_json_path": str(plan_json_path.resolve()) if plan_json_path else None,
                "ai_response_json_path": None,
                "components": {},
                "assembly_layout": cfg.assembly_layout,
                "grid_columns": cfg.grid_columns,
                "component_sheet": {
                    "json": str(sheet_json_path.resolve()) if sheet_json_path else None,
                    "markdown": str(sheet_md_path.resolve()) if sheet_md_path else None,
                    "warnings": sheet_warnings,
                },
            }
            mp = output_dir / f"{stem}_gemini_codegen_manifest.json"
            mp.parent.mkdir(parents=True, exist_ok=True)
            mp.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
            return GeminiCadCodegenResult(
                manifest_path=mp,
                assembly_dxf=None,
                raw_model_text_path=raw_path,
                ai_response_json_path=None,
                warnings=warnings,
                component_sheet_json=sheet_json_path,
                component_sheet_markdown=sheet_md_path,
                component_sheet_warnings=sheet_warnings,
                component_plan_json_path=plan_json_path,
                component_plan_raw_text_path=plan_raw_path,
            )
    else:
        if not used_two_stage:
            raw_text = call_gemini_generate_content_raw(
                api_key=api_key,
                model=cfg.gemini_model,
                png_bytes=png_bytes,
                user_prompt=build_gemini_codegen_user_prompt(
                    target_component_count=cfg.target_component_count,
                ),
                timeout_s=cfg.gemini_timeout_s,
                max_output_tokens=cfg.gemini_max_output_tokens,
            )
            raw_path.write_text(raw_text, encoding="utf-8")

    if (not use_multisegment) and (not used_two_stage):
        try:
            components = parse_codegen_json_payload(raw_text, parse_warnings=warnings)
        except ValueError as e:
            warnings.append(f"JSON parse failed: {e}")
            manifest = {
                "stem": stem,
                "input": str(cfg.input_path.resolve()),
                "two_stage": bool(cfg.two_stage),
                "stage1_model": cfg.stage1_model,
                "stage2_model": cfg.stage2_model,
                "stage2_batch_size": int(cfg.stage2_batch_size),
                "stage2_max_workers": int(cfg.stage2_max_workers),
                "warnings": warnings,
                "target_component_count": max(1, min(60, int(cfg.target_component_count))),
                "gemini_single_json_call": cfg.gemini_single_json_call,
                "raw_text_path": str(raw_path.resolve()),
                "component_plan_raw_text_path": str(plan_raw_path.resolve()) if plan_raw_path else None,
                "component_plan_json_path": str(plan_json_path.resolve()) if plan_json_path else None,
                "ai_response_json_path": None,
                "components": {},
                "assembly_layout": cfg.assembly_layout,
                "grid_columns": cfg.grid_columns,
                "component_sheet": {
                    "json": str(sheet_json_path.resolve()) if sheet_json_path else None,
                    "markdown": str(sheet_md_path.resolve()) if sheet_md_path else None,
                    "warnings": sheet_warnings,
                },
            }
            mp = output_dir / f"{stem}_gemini_codegen_manifest.json"
            mp.parent.mkdir(parents=True, exist_ok=True)
            mp.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
            return GeminiCadCodegenResult(
                manifest_path=mp,
                assembly_dxf=None,
                raw_model_text_path=raw_path,
                ai_response_json_path=None,
                warnings=warnings,
                component_sheet_json=sheet_json_path,
                component_sheet_markdown=sheet_md_path,
                component_sheet_warnings=sheet_warnings,
                component_plan_json_path=plan_json_path,
                component_plan_raw_text_path=plan_raw_path,
            )

    n_comp = len(components)
    ai_response_json_path = output_dir / f"{stem}_gemini_codegen_ai_response.json"
    ai_response_json_path.write_text(
        json.dumps(components, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    if n_comp > t_req:
        warnings.append(
            f"{n_comp} component script(s) returned; target was at most {t_req} (--target-components)."
        )
    elif n_comp < t_req:
        warnings.append(
            f"Only {n_comp} component script(s) returned; target was {t_req} — "
            "try --gemini-max-output-tokens, a sharper image, or a clearer primary detail."
        )

    scripts_dir = output_dir / "gemini_codegen_scripts"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    dxfs_dir = output_dir / "gemini_codegen_dxfs"
    dxfs_dir.mkdir(parents=True, exist_ok=True)

    script_paths: dict[str, Path] = {}
    dxf_paths: dict[str, Path] = {}

    for comp_id, code in components.items():
        stem_c = _safe_stem(comp_id)
        py_path = scripts_dir / f"{stem_c}.py"
        sanitized, san_notes = sanitize_codegen_python_source(code)
        for note in san_notes:
            warnings.append(f"Sanitized {comp_id}: {note}")
        py_path.write_text(sanitized, encoding="utf-8")
        script_paths[comp_id] = py_path
        out_dxf = dxfs_dir / f"{stem_c}.dxf"
        py_abs = py_path.resolve()
        dxf_abs = out_dxf.resolve()
        try:
            proc = subprocess.run(
                [sys.executable, str(py_abs), str(dxf_abs)],
                capture_output=True,
                text=True,
                timeout=cfg.script_timeout_s,
                cwd=str(scripts_dir.resolve()),
            )
            if proc.returncode != 0:
                err = (proc.stderr or proc.stdout or "").strip() or f"exit {proc.returncode}"
                script_errors[comp_id] = err[:4000]
                warnings.append(f"Script failed for {comp_id}: {err[:500]}")
                continue
            if not out_dxf.is_file():
                script_errors[comp_id] = "Script exited 0 but DXF missing"
                warnings.append(f"No DXF written for {comp_id}")
                continue
            dxf_paths[comp_id] = out_dxf
        except subprocess.TimeoutExpired:
            script_errors[comp_id] = "timeout"
            warnings.append(f"Script timeout for {comp_id}")

    assembly: Path | None = None
    if dxf_paths:
        ordered = [(k, dxf_paths[k]) for k in components if k in dxf_paths]
        assembly = output_dir / f"{stem}_gemini_codegen_assembly.dxf"
        try:
            lay = (cfg.assembly_layout or "horizontal").strip().lower()
            if lay == "grid":
                merge_dxfs_grid(
                    ordered,
                    assembly,
                    gap_mm=cfg.layout_gap_mm,
                    ncols=int(cfg.grid_columns),
                    cell_width_mm=cfg.grid_cell_width_mm,
                    cell_height_mm=cfg.grid_cell_height_mm,
                    center_in_cell=bool(cfg.grid_center_in_cell),
                    scale_to_fit=bool(cfg.grid_scale_to_fit),
                )
            else:
                merge_dxfs_horizontal(ordered, assembly, gap_mm=cfg.layout_gap_mm)
        except Exception as e:
            warnings.append(f"Assembly merge failed: {e}")
            assembly = None

    manifest = {
        "stem": stem,
        "input": str(cfg.input_path.resolve()),
        "gemini_model": cfg.gemini_model,
        "two_stage": bool(cfg.two_stage),
        "stage1_model": cfg.stage1_model,
        "stage2_model": cfg.stage2_model,
        "stage2_batch_size": int(cfg.stage2_batch_size),
        "stage2_max_workers": int(cfg.stage2_max_workers),
        "gemini_max_output_tokens": cfg.gemini_max_output_tokens,
        "target_component_count": max(1, min(60, int(cfg.target_component_count))),
        "gemini_single_json_call": cfg.gemini_single_json_call,
        "component_count_requested": len(components),
        "warnings": warnings,
        "raw_text_path": str(raw_path.resolve()),
        "component_plan_raw_text_path": str(plan_raw_path.resolve()) if plan_raw_path else None,
        "component_plan_json_path": str(plan_json_path.resolve()) if plan_json_path else None,
        "ai_response_json_path": str(ai_response_json_path.resolve()),
        "components": {k: {"script": str(v.resolve())} for k, v in script_paths.items()},
        "dxfs": {k: str(v.resolve()) for k, v in dxf_paths.items()},
        "script_errors": script_errors,
        "assembly_dxf": str(assembly.resolve()) if assembly else None,
        "assembly_layout": cfg.assembly_layout,
        "grid_columns": cfg.grid_columns,
        "component_sheet": {
            "json": str(sheet_json_path.resolve()) if sheet_json_path else None,
            "markdown": str(sheet_md_path.resolve()) if sheet_md_path else None,
            "warnings": sheet_warnings,
        },
    }
    mp = output_dir / f"{stem}_gemini_codegen_manifest.json"
    mp.parent.mkdir(parents=True, exist_ok=True)
    mp.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    return GeminiCadCodegenResult(
        manifest_path=mp,
        assembly_dxf=assembly,
        raw_model_text_path=raw_path,
        ai_response_json_path=ai_response_json_path,
        component_scripts=script_paths,
        component_dxfs=dxf_paths,
        warnings=warnings,
        script_errors=script_errors,
        component_sheet_json=sheet_json_path,
        component_sheet_markdown=sheet_md_path,
        component_sheet_warnings=sheet_warnings,
        component_plan_json_path=plan_json_path,
        component_plan_raw_text_path=plan_raw_path,
    )
