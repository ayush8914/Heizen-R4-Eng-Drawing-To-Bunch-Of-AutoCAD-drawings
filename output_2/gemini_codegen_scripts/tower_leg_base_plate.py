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
plate_width = 600
plate_height = 600
plate_thickness = "PL20 (EST)"
anchor_hole_dia = 24
anchor_hole_offset = 100
leg_opening_size = 150 # Square opening for leg
qty = 4 # Assuming 4 legs per tower

# --- Geometry ---
# Outer plate boundary
msp.add_lwpolyline([(0, 0), (plate_width, 0), (plate_width, plate_height), (0, plate_height)], close=True, dxfattribs={"layer": "GEOMETRY"})

# Anchor bolt holes
anchor_holes = [
    (anchor_hole_offset, anchor_hole_offset),
    (plate_width - anchor_hole_offset, anchor_hole_offset),
    (plate_width - anchor_hole_offset, plate_height - anchor_hole_offset),
    (anchor_hole_offset, plate_height - anchor_hole_offset)
]
for x, y in anchor_holes:
    msp.add_circle((x, y), anchor_hole_dia / 2, dxfattribs={"layer": "GEOMETRY"})

# Central opening for leg
leg_opening_x_start = (plate_width - leg_opening_size) / 2
leg_opening_y_start = (plate_height - leg_opening_size) / 2
msp.add_lwpolyline([
    (leg_opening_x_start, leg_opening_y_start),
    (leg_opening_x_start + leg_opening_size, leg_opening_y_start),
    (leg_opening_x_start + leg_opening_size, leg_opening_y_start + leg_opening_size),
    (leg_opening_x_start, leg_opening_y_start + leg_opening_size)
], close=True, dxfattribs={"layer": "GEOMETRY"})

# --- Annotations ---
text_height = 5.58
dim_text_height = 3.5
dim_offset = 30
arrow_len = 10

# Part Title
mt = msp.add_mtext("TOWER LEG BASE PLATE", dxfattribs={"layer": "ANNOTATION", "char_height": text_height})
mt.set_location((plate_width / 2, plate_height + 50), attachment_point=5) # Middle Center

# Material and QTY
mt = msp.add_mtext(f"MATERIAL: {plate_thickness}\nQTY: {qty} PCS", dxfattribs={"layer": "ANNOTATION", "char_height": dim_text_height})
mt.set_location((plate_width + 20, plate_height), attachment_point=7) # Middle Left

# Overall Dimensions
# Width
msp.add_line((0, 0), (0, -dim_offset), dxfattribs={"layer": "DIMENSION"})
msp.add_line((plate_width, 0), (plate_width, -dim_offset), dxfattribs={"layer": "DIMENSION"})
msp.add_line((0, -dim_offset), (plate_width, -dim_offset), dxfattribs={"layer": "DIMENSION"})
# Arrowheads
msp.add_line((0, -dim_offset), (arrow_len, -dim_offset + arrow_len/2), dxfattribs={"layer": "DIMENSION"})
msp.add_line((0, -dim_offset), (arrow_len, -dim_offset - arrow_len/2), dxfattribs={"layer": "DIMENSION"})
msp.add_line((plate_width, -dim_offset), (plate_width - arrow_len, -dim_offset + arrow_len/2), dxfattribs={"layer": "DIMENSION"})
msp.add_line((plate_width, -dim_offset), (plate_width - arrow_len, -dim_offset - arrow_len/2), dxfattribs={"layer": "DIMENSION"})
mt_dim = msp.add_mtext(f"{plate_width}", dxfattribs={"layer": "ANNOTATION", "char_height": dim_text_height})
mt_dim.set_location((plate_width / 2, -dim_offset - 5), attachment_point=5)

# Height
msp.add_line((plate_width, 0), (plate_width + dim_offset, 0), dxfattribs={"layer": "DIMENSION"})
msp.add_line((plate_width, plate_height), (plate_width + dim_offset, plate_height), dxfattribs={"layer": "DIMENSION"})
msp.add_line((plate_width + dim_offset, 0), (plate_width + dim_offset, plate_height), dxfattribs={"layer": "DIMENSION"})
# Arrowheads
msp.add_line((plate_width + dim_offset, 0), (plate_width + dim_offset - arrow_len/2, arrow_len), dxfattribs={"layer": "DIMENSION"})
msp.add_line((plate_width + dim_offset, 0), (plate_width + dim_offset + arrow_len/2, arrow_len), dxfattribs={"layer": "DIMENSION"})
msp.add_line((plate_width + dim_offset, plate_height), (plate_width + dim_offset - arrow_len/2, plate_height - arrow_len), dxfattribs={"layer": "DIMENSION"})
msp.add_line((plate_width + dim_offset, plate_height), (plate_width + dim_offset + arrow_len/2, plate_height - arrow_len), dxfattribs={"layer": "DIMENSION"})
mt_dim = msp.add_mtext(f"{plate_height}", dxfattribs={"layer": "ANNOTATION", "char_height": dim_text_height})
mt_dim.set_location((plate_width + dim_offset + 5, plate_height / 2), attachment_point=5)

# Anchor hole dimensions (one set for clarity)
# X-offset
msp.add_line((0, anchor_hole_offset), (-dim_offset, anchor_hole_offset), dxfattribs={"layer": "DIMENSION"})
msp.add_line((0, 0), (-dim_offset, 0), dxfattribs={"layer": "DIMENSION"})
msp.add_line((-dim_offset, 0), (-dim_offset, anchor_hole_offset), dxfattribs={"layer": "DIMENSION"})
# Arrowheads
msp.add_line((-dim_offset, 0), (-dim_offset - arrow_len/2, arrow_len), dxfattribs={"layer": "DIMENSION"})
msp.add_line((-dim_offset, 0), (-dim_offset + arrow_len/2, arrow_len), dxfattribs={"layer": "DIMENSION"})
msp.add_line((-dim_offset, anchor_hole_offset), (-dim_offset - arrow_len/2, anchor_hole_offset - arrow_len), dxfattribs={"layer": "DIMENSION"})
msp.add_line((-dim_offset, anchor_hole_offset), (-dim_offset + arrow_len/2, anchor_hole_offset - arrow_len), dxfattribs={"layer": "DIMENSION"})
mt_dim = msp.add_mtext(f"{anchor_hole_offset}", dxfattribs={"layer": "ANNOTATION", "char_height": dim_text_height})
mt_dim.set_location((-dim_offset - 5, anchor_hole_offset / 2), attachment_point=5)

# Y-offset
msp.add_line((anchor_hole_offset, 0), (anchor_hole_offset, -dim_offset), dxfattribs={"layer": "DIMENSION"})
msp.add_line((0, 0), (0, -dim_offset), dxfattribs={"layer": "DIMENSION"}) # Extension line from origin
msp.add_line((0, -dim_offset), (anchor_hole_offset, -dim_offset), dxfattribs={"layer": "DIMENSION"})
# Arrowheads
msp.add_line((0, -dim_offset), (arrow_len, -dim_offset + arrow_len/2), dxfattribs={"layer": "DIMENSION"})
msp.add_line((0, -dim_offset), (arrow_len, -dim_offset - arrow_len/2), dxfattribs={"layer": "DIMENSION"})
msp.add_line((anchor_hole_offset, -dim_offset), (anchor_hole_offset - arrow_len, -dim_offset + arrow_len/2), dxfattribs={"layer": "DIMENSION"})
msp.add_line((anchor_hole_offset, -dim_offset), (anchor_hole_offset - arrow_len, -dim_offset - arrow_len/2), dxfattribs={"layer": "DIMENSION"})
mt_dim = msp.add_mtext(f"{anchor_hole_offset}", dxfattribs={"layer": "ANNOTATION", "char_height": dim_text_height})
mt_dim.set_location((anchor_hole_offset / 2, -dim_offset - 5), attachment_point=5)

# Hole callout
msp.add_mtext(f"4x Ø{anchor_hole_dia} THRU", dxfattribs={"layer": "ANNOTATION", "char_height": dim_text_height}).set_location((anchor_hole_offset, anchor_hole_offset + 15), attachment_point=7)

# Central opening dimensions
msp.add_line((leg_opening_x_start, plate_height + dim_offset), (leg_opening_x_start, plate_height), dxfattribs={"layer": "DIMENSION"})
msp.add_line((leg_opening_x_start + leg_opening_size, plate_height + dim_offset), (leg_opening_x_start + leg_opening_size, plate_height), dxfattribs={"layer": "DIMENSION"})
msp.add_line((leg_opening_x_start, plate_height + dim_offset), (leg_opening_x_start + leg_opening_size, plate_height + dim_offset), dxfattribs={"layer": "DIMENSION"})
# Arrowheads
msp.add_line((leg_opening_x_start, plate_height + dim_offset), (leg_opening_x_start + arrow_len, plate_height + dim_offset + arrow_len/2), dxfattribs={"layer": "DIMENSION"})
msp.add_line((leg_opening_x_start, plate_height + dim_offset), (leg_opening_x_start + arrow_len, plate_height + dim_offset - arrow_len/2), dxfattribs={"layer": "DIMENSION"})
msp.add_line((leg_opening_x_start + leg_opening_size, plate_height + dim_offset), (leg_opening_x_start + leg_opening_size - arrow_len, plate_height + dim_offset + arrow_len/2), dxfattribs={"layer": "DIMENSION"})
msp.add_line((leg_opening_x_start + leg_opening_size, plate_height + dim_offset), (leg_opening_x_start + leg_opening_size - arrow_len, plate_height + dim_offset - arrow_len/2), dxfattribs={"layer": "DIMENSION"})
mt_dim = msp.add_mtext(f"{leg_opening_size}", dxfattribs={"layer": "ANNOTATION", "char_height": dim_text_height})
mt_dim.set_location((leg_opening_x_start + leg_opening_size / 2, plate_height + dim_offset + 5), attachment_point=5)

msp.add_mtext(f"LEG OPENING {leg_opening_size}x{leg_opening_size}", dxfattribs={"layer": "ANNOTATION", "char_height": dim_text_height}).set_location((plate_width / 2, leg_opening_y_start + leg_opening_size / 2), attachment_point=5)

doc.saveas(out)
print(f"Saved {out}")