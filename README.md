# drawing-to-dxf

**Engineering drawing (image or PDF) → Gemini vision → Python script per component → DXF files + optional assembly DXF.**

No AutoCAD required to generate DXF (open in AutoCAD, BricsCAD, LibreCAD, etc.).

## Install

```powershell
cd C:\Users\admin\Desktop\HyzenInterview
python -m venv .venv
.\.venv\Scripts\activate
pip install -e .
```

Set **`GEMINI_API_KEY`**  as environment variable

## Usage

```powershell
 drawing-to-dxf gemini-codegen "Resource/Sample.png" -o out_gemini_codegen \
  --target-components 9 \
  --assembly-layout grid --grid-columns 3

```

**Useful flags:** `--gemini-model`,  `--gemini-max-output-tokens`, `--layout-gap-mm`, `--assembly-layout`, `--grid-columns`

# Heizen-R4-Eng-Drawing-To-Bunch-Of-AutoCAD-drawings
