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
base_width = 200
base_depth = 100
main_plate_height = 300
plate_thickness = "PL12 (EST)"
conn_hole_dia = 18
insulator_hole_dia = 30
gusset_size = 100 # Gusset base and height
qty = 12 # Assuming 3 crossarms per side, 2 insulators per crossarm, 2 sides = 12

# --- Geometry ---
# Main plate (vertical part)
# Start from (0, base_depth)
main_plate_points = [
    (0, base_depth),
    (base_width, base_depth),
    (base_width, base_depth + main_plate_height),
    (0, base_depth + main_plate_height)
]
msp.add_lwpolyline(main_plate_points, close=True, dxfattribs={"layer": "GEOMETRY"})

# Base flange (horizontal part)
base_flange_points = [
    (0, 0),
    (base_width, 0),
    (base_width, base_depth),
    (0, base_depth)
]
msp.add_lwpolyline(base_flange_points, close=True, dxfattribs={"layer": "GEOMETRY"})

# Connection holes on base flange
conn_hole_offset_x = 50
conn_hole_offset_y = base_depth / 2
msp.add_circle((conn_hole_offset_x, conn_hole_offset_y), conn_hole_dia / 2, dxfattribs={"layer": "GEOMETRY"})
msp.add_circle((base_width - conn_hole_offset_x, conn_hole_offset_y), conn_hole_dia / 2, dxfattribs={"layer": "GEOMETRY"})

# Insulator hole at bottom of main plate
insulator_hole_center_x = base_width / 2
insulator_hole_center_y = base_depth + 50 # 50mm from the bottom of the main plate
msp.add_circle((insulator_hole_center_x, insulator_hole_center_y), insulator_hole_dia / 2, dxfattribs={"layer": "GEOMETRY"})

# Gussets (simplified as triangles on the main plate, assuming a side view)
# Gusset 1 (left)
gusset1_points = [
    (0, base_depth),
    (gusset_size, base_depth),
    (0, base_depth + gusset_size)
]
msp.add_lwpolyline(gusset1_points, close=True, dxfattribs={"layer": "GEOMETRY"})

# Gusset 2 (right)
gusset2_points = [
    (base_width, base_depth),
    (base_width - gusset_size, base_depth),
    (base_width, base_depth + gusset_size)
]
msp.add_lwpolyline(gusset2_points, close=True, dxfattribs={"layer": "GEOMETRY"})


# --- Annotations ---
text_height = 5.58
dim_text_height = 3.5
dim_offset = 30
arrow_len = 10

# Part Title
mt = msp.add_mtext("CROSSARM INSULATOR BRACKET", dxfattribs={"layer": "ANNOTATION", "char_height": text_height})
mt.set_location((base_width / 2, base_depth + main_plate_height + 50), attachment_point=5)

# Material and QTY
mt = msp.add_mtext(f"MATERIAL: {plate_thickness}\nQTY: {qty} PCS", dxfattribs={"layer": "ANNOTATION", "char_height": dim_text_height})
mt.set_location((base_width + 20, base_depth + main_plate_height), attachment_point=7)

# Overall Dimensions
# Total Height
msp.add_line((base_width + dim_offset, 0), (base_width + dim_offset, base_depth + main_plate_height), dxfattribs={"layer": "DIMENSION"})
msp.add_line((base_width, 0), (base_width + dim_offset, 0), dxfattribs={"layer": "DIMENSION"})
msp.add_line((base_width, base_depth + main_plate_height), (base_width + dim_offset, base_depth + main_plate_height), dxfattribs={"layer": "DIMENSION"})
# Arrowheads
msp.add_line((base_width + dim_offset, 0), (base_width + dim_offset - arrow_len/2, arrow_len), dxfattribs={"layer": "DIMENSION"})
msp.add_line((base_width + dim_offset, 0), (base_width + dim_offset + arrow_len/2, arrow_len), dxfattribs={"layer": "DIMENSION"})
msp.add_line((base_width + dim_offset, base_depth + main_plate_height), (base_width + dim_offset - arrow_len/2, base_depth + main_plate_height - arrow_len), dxfattribs={"layer": "DIMENSION"})
msp.add_line((base_width + dim_offset, base_depth + main_plate_height), (base_width + dim_offset + arrow_len/2, base_depth + main_plate_height - arrow_len), dxfattribs={"layer": "DIMENSION"})
mt_dim = msp.add_mtext(f"{base_depth + main_plate_height}", dxfattribs={"layer": "ANNOTATION", "char_height": dim_text_height})
mt_dim.set_location((base_width + dim_offset + 5, (base_depth + main_plate_height) / 2), attachment_point=5)

# Base Width
msp.add_line((0, -dim_offset), (base_width, -dim_offset), dxfattribs={"layer": "DIMENSION"})
msp.add_line((0, 0), (0, -dim_offset), dxfattribs={"layer": "DIMENSION"})
msp.add_line((base_width, 0), (base_width, -dim_offset), dxfattribs={"layer": "DIMENSION"})
# Arrowheads
msp.add_line((0, -dim_offset), (arrow_len, -dim_offset + arrow_len/2), dxfattribs={"layer": "DIMENSION"})
msp.add_line((0, -dim_offset), (arrow_len, -dim_offset - arrow_len/2), dxfattribs={"layer": "DIMENSION"})
msp.add_line((base_width, -dim_offset), (base_width - arrow_len, -dim_offset + arrow_len/2), dxfattribs={"layer": "DIMENSION"})
msp.add_line((base_width, -dim_offset), (base_width - arrow_len, -dim_offset - arrow_len/2), dxfattribs={"layer": "DIMENSION"})
mt_dim = msp.add_mtext(f"{base_width}", dxfattribs={"layer": "ANNOTATION", "char_height": dim_text_height})
mt_dim.set_location((base_width / 2, -dim_offset - 5), attachment_point=5)

# Base Depth
msp.add_line((-dim_offset, 0), (-dim_offset, base_depth), dxfattribs={"layer": "DIMENSION"})
msp.add_line((0, 0), (-dim_offset, 0), dxfattribs={"layer": "DIMENSION"})
msp.add_line((0, base_depth), (-dim_offset, base_depth), dxfattribs={"layer": "DIMENSION"})
# Arrowheads
msp.add_line((-dim_offset, 0), (-dim_offset - arrow_len/2, arrow_len), dxfattribs={"layer": "DIMENSION"})
msp.add_line((-dim_offset, 0), (-dim_offset + arrow_len/2, arrow_len), dxfattribs={"layer": "DIMENSION"})
msp.add_line((-dim_offset, base_depth), (-dim_offset - arrow_len/2, base_depth - arrow_len), dxfattribs={"layer": "DIMENSION"})
msp.add_line((-dim_offset, base_depth), (-dim_offset + arrow_len/2, base_depth - arrow_len), dxfattribs={"layer": "DIMENSION"})
mt_dim = msp.add_mtext(f"{base_depth}", dxfattribs={"layer": "ANNOTATION", "char_height": dim_text_height})
mt_dim.set_location((-dim_offset - 5, base_depth / 2), attachment_point=5)

# Connection hole callout
msp.add_mtext(f"2x Ø{conn_hole_dia} THRU", dxfattribs={"layer": "ANNOTATION", "char_height": dim_text_height}).set_location((conn_hole_offset_x, conn_hole_offset_y + 15), attachment_point=7)

# Insulator hole callout
msp.add_mtext(f"1x Ø{insulator_hole_dia} THRU (INSULATOR PIN)", dxfattribs={"layer": "ANNOTATION", "char_height": dim_text_height}).set_location((insulator_hole_center_x, insulator_hole_center_y + 20), attachment_point=5)

doc.saveas(out)
print(f"Saved {out}")