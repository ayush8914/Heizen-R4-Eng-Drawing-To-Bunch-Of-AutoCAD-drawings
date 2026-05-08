import sys
import ezdxf
import math

out = sys.argv[1]

doc = ezdxf.new("R2010", setup=True)
doc.units = ezdxf.units.MM
msp = doc.modelspace()

# Define layers
doc.layers.add("GEOMETRY", color=7) # White/Black
doc.layers.add("DIMENSION", color=3) # Green
doc.layers.add("ANNOTATION", color=1) # Red

# --- Part specific variables ---
gusset_base = 400
gusset_height = 400
chamfer_size = 50
plate_thickness = "PL10 (EST)"
bolt_hole_dia = 20
hole_offset = 100 # Offset from edges for holes
hole_pitch = 100 # Pitch between holes
qty = 8 # Assuming 4 crossarms, 2 gussets per connection point

# --- Geometry ---
# Gusset outline with clipped corner
# Start at (0,0)
gusset_points = [
    (0, 0),
    (gusset_base, 0),
    (gusset_base, gusset_height - chamfer_size),
    (gusset_base - chamfer_size, gusset_height),
    (0, gusset_height)
]
msp.add_lwpolyline(gusset_points, close=True, dxfattribs={"layer": "GEOMETRY"})

# Bolt holes
# Holes along base (x-axis)
for i in range(3): # 3 holes
    x = hole_offset + i * hole_pitch
    y = hole_offset / 2 # Slightly offset from edge for clarity, or on a bolt line
    msp.add_circle((x, y), bolt_hole_dia / 2, dxfattribs={"layer": "GEOMETRY"})

# Holes along height (y-axis)
for i in range(3): # 3 holes
    x = hole_offset / 2
    y = hole_offset + i * hole_pitch
    msp.add_circle((x, y), bolt_hole_dia / 2, dxfattribs={"layer": "GEOMETRY"})

# Hole near clipped corner (EST)
msp.add_circle((gusset_base - chamfer_size - hole_offset, gusset_height - chamfer_size - hole_offset), bolt_hole_dia / 2, dxfattribs={"layer": "GEOMETRY"})


# --- Annotations ---
text_height = 5.58
dim_text_height = 3.5
dim_offset = 30
arrow_len = 10

# Part Title
mt = msp.add_mtext("CROSSARM TO TOWER GUSSET", dxfattribs={"layer": "ANNOTATION", "char_height": text_height})
mt.set_location((gusset_base / 2, gusset_height + 50), attachment_point=5)

# Material and QTY
mt = msp.add_mtext(f"MATERIAL: {plate_thickness}\nQTY: {qty} PCS", dxfattribs={"layer": "ANNOTATION", "char_height": dim_text_height})
mt.set_location((gusset_base + 20, gusset_height), attachment_point=7)

# Overall Dimensions
# Base Width
msp.add_line((0, -dim_offset), (gusset_base, -dim_offset), dxfattribs={"layer": "DIMENSION"})
msp.add_line((0, 0), (0, -dim_offset), dxfattribs={"layer": "DIMENSION"})
msp.add_line((gusset_base, 0), (gusset_base, -dim_offset), dxfattribs={"layer": "DIMENSION"})
# Arrowheads
msp.add_line((0, -dim_offset), (arrow_len, -dim_offset + arrow_len/2), dxfattribs={"layer": "DIMENSION"})
msp.add_line((0, -dim_offset), (arrow_len, -dim_offset - arrow_len/2), dxfattribs={"layer": "DIMENSION"})
msp.add_line((gusset_base, -dim_offset), (gusset_base - arrow_len, -dim_offset + arrow_len/2), dxfattribs={"layer": "DIMENSION"})
msp.add_line((gusset_base, -dim_offset), (gusset_base - arrow_len, -dim_offset - arrow_len/2), dxfattribs={"layer": "DIMENSION"})
mt_dim = msp.add_mtext(f"{gusset_base}", dxfattribs={"layer": "ANNOTATION", "char_height": dim_text_height})
mt_dim.set_location((gusset_base / 2, -dim_offset - 5), attachment_point=5)

# Total Height
msp.add_line((gusset_base + dim_offset, 0), (gusset_base + dim_offset, gusset_height), dxfattribs={"layer": "DIMENSION"})
msp.add_line((gusset_base, 0), (gusset_base + dim_offset, 0), dxfattribs={"layer": "DIMENSION"})
msp.add_line((gusset_base - chamfer_size, gusset_height), (gusset_base + dim_offset, gusset_height), dxfattribs={"layer": "DIMENSION"}) # Extension from top point
# Arrowheads
msp.add_line((gusset_base + dim_offset, 0), (gusset_base + dim_offset - arrow_len/2, arrow_len), dxfattribs={"layer": "DIMENSION"})
msp.add_line((gusset_base + dim_offset, 0), (gusset_base + dim_offset + arrow_len/2, arrow_len), dxfattribs={"layer": "DIMENSION"})
msp.add_line((gusset_base + dim_offset, gusset_height), (gusset_base + dim_offset - arrow_len/2, gusset_height - arrow_len), dxfattribs={"layer": "DIMENSION"})
msp.add_line((gusset_base + dim_offset, gusset_height), (gusset_base + dim_offset + arrow_len/2, gusset_height - arrow_len), dxfattribs={"layer": "DIMENSION"})
mt_dim = msp.add_mtext(f"{gusset_height}", dxfattribs={"layer": "ANNOTATION", "char_height": dim_text_height})
mt_dim.set_location((gusset_base + dim_offset + 5, gusset_height / 2), attachment_point=5)

# Chamfer dimension
msp.add_line((gusset_base - chamfer_size, gusset_height), (gusset_base - chamfer_size, gusset_height + dim_offset), dxfattribs={"layer": "DIMENSION"})
msp.add_line((gusset_base, gusset_height - chamfer_size), (gusset_base + dim_offset, gusset_height - chamfer_size), dxfattribs={"layer": "DIMENSION"})
msp.add_line((gusset_base - chamfer_size, gusset_height + dim_offset), (gusset_base + dim_offset, gusset_height + dim_offset), dxfattribs={"layer": "DIMENSION"})
# Arrowheads
msp.add_line((gusset_base - chamfer_size, gusset_height + dim_offset), (gusset_base - chamfer_size + arrow_len, gusset_height + dim_offset + arrow_len/2), dxfattribs={"layer": "DIMENSION"})
msp.add_line((gusset_base - chamfer_size, gusset_height + dim_offset), (gusset_base - chamfer_size + arrow_len, gusset_height + dim_offset - arrow_len/2), dxfattribs={"layer": "DIMENSION"})
msp.add_line((gusset_base + dim_offset, gusset_height + dim_offset), (gusset_base + dim_offset - arrow_len/2, gusset_height + dim_offset - arrow_len), dxfattribs={"layer": "DIMENSION"})
msp.add_line((gusset_base + dim_offset, gusset_height + dim_offset), (gusset_base + dim_offset + arrow_len/2, gusset_height + dim_offset - arrow_len), dxfattribs={"layer": "DIMENSION"})
mt_dim = msp.add_mtext(f"C{chamfer_size}", dxfattribs={"layer": "ANNOTATION", "char_height": dim_text_height})
mt_dim.set_location((gusset_base - chamfer_size / 2, gusset_height + dim_offset + 5), attachment_point=5)

# Hole callout (example for one set)
msp.add_mtext(f"3x Ø{bolt_hole_dia} THRU @ {hole_pitch} PITCH", dxfattribs={"layer": "ANNOTATION", "char_height": dim_text_height}).set_location((hole_offset, hole_offset + 30), attachment_point=7)
msp.add_mtext(f"3x Ø{bolt_hole_dia} THRU @ {hole_pitch} PITCH", dxfattribs={"layer": "ANNOTATION", "char_height": dim_text_height}).set_location((hole_offset + 100, hole_offset + 30), attachment_point=7) # For the other set of holes

doc.saveas(out)
print(f"Saved {out}")