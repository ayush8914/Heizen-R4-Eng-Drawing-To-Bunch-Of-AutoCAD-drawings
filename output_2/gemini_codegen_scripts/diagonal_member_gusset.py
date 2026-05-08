import sys
import ezdxf
import math

def draw_horizontal_dimension(msp, p1, p2, offset_y, text, char_height=5.58, layer="DIMENSION", text_layer="ANNOTATION"):
    msp.add_line((p1[0], p1[1]), (p1[0], p1[1] + offset_y), dxfattribs={"layer": layer})
    msp.add_line((p2[0], p2[1]), (p2[0], p2[1] + offset_y), dxfattribs={"layer": layer})
    dim_line_y = p1[1] + offset_y
    msp.add_line((p1[0], dim_line_y), (p2[0], dim_line_y), dxfattribs={"layer": layer})
    arrow_size = char_height * 0.8
    msp.add_line((p1[0], dim_line_y), (p1[0] + arrow_size, dim_line_y + arrow_size/2), dxfattribs={"layer": layer})
    msp.add_line((p1[0], dim_line_y), (p1[0] + arrow_size, dim_line_y - arrow_size/2), dxfattribs={"layer": layer})
    msp.add_line((p2[0], dim_line_y), (p2[0] - arrow_size, dim_line_y + arrow_size/2), dxfattribs={"layer": layer})
    msp.add_line((p2[0], dim_line_y), (p2[0] - arrow_size, dim_line_y - arrow_size/2), dxfattribs={"layer": layer})
    text_insert_point = ((p1[0] + p2[0]) / 2, dim_line_y + char_height / 2)
    mt = msp.add_mtext(text, dxfattribs={"layer": text_layer, "char_height": char_height})
    mt.set_location(text_insert_point, attachment_point=5)

def draw_vertical_dimension(msp, p1, p2, offset_x, text, char_height=5.58, layer="DIMENSION", text_layer="ANNOTATION"):
    msp.add_line((p1[0], p1[1]), (p1[0] + offset_x, p1[1]), dxfattribs={"layer": layer})
    msp.add_line((p2[0], p2[1]), (p2[0] + offset_x, p2[1]), dxfattribs={"layer": layer})
    dim_line_x = p1[0] + offset_x
    msp.add_line((dim_line_x, p1[1]), (dim_line_x, p2[1]), dxfattribs={"layer": layer})
    arrow_size = char_height * 0.8
    msp.add_line((dim_line_x, p1[1]), (dim_line_x + arrow_size/2, p1[1] + arrow_size), dxfattribs={"layer": layer})
    msp.add_line((dim_line_x, p1[1]), (dim_line_x - arrow_size/2, p1[1] + arrow_size), dxfattribs={"layer": layer})
    msp.add_line((dim_line_x, p2[1]), (dim_line_x + arrow_size/2, p2[1] - arrow_size), dxfattribs={"layer": layer})
    msp.add_line((dim_line_x, p2[1]), (dim_line_x - arrow_size/2, p2[1] - arrow_size), dxfattribs={"layer": layer})
    text_insert_point = (dim_line_x + char_height / 2, (p1[1] + p2[1]) / 2)
    mt = msp.add_mtext(text, dxfattribs={"layer": text_layer, "char_height": char_height})
    mt.set_location(text_insert_point, attachment_point=5)

def add_part_annotation(msp, part_name, material, thickness, qty, overall_dims, insert_point=(10, -50), char_height=5.58, layer="ANNOTATION"):
    text_lines = [
        f"PART: {part_name}",
        f"MATERIAL: {material}",
        f"THICKNESS: {thickness}mm",
        f"QTY: {qty}",
        f"OVERALL DIMS: {overall_dims} (EST)"
    ]
    y_offset = 0
    for line in text_lines:
        mt = msp.add_mtext(line, dxfattribs={"layer": layer, "char_height": char_height})
        mt.set_location((insert_point[0], insert_point[1] - y_offset), attachment_point=7)
        y_offset += char_height * 1.5

out = sys.argv[1]
doc = ezdxf.new("R2010", setup=True)
doc.units = ezdxf.units.MM
msp = doc.modelspace()

# Define layers
doc.layers.add("GEOMETRY", color=1) # Red
doc.layers.add("DIMENSION", color=3) # Green
doc.layers.add("ANNOTATION", color=7) # White/Black

# Part parameters (ESTIMATED)
part_name = "DIAGONAL MEMBER GUSSET"
material = "STEEL"
thickness = 10 # mm
qty = "EST. 1"

# Geometry (5-sided polygon)
p1 = (0,0)
p2 = (250,0)
p3 = (250,150)
p4 = (150,200)
p5 = (0,150)
outline_points = [p1, p2, p3, p4, p5]
msp.add_lwpolyline(outline_points, close=True, dxfattribs={"layer": "GEOMETRY"})

# Holes (6 holes, Ø18)
hole_diameter = 18 # mm (for M16 bolts)
edge_dist = 35 # mm
pitch = 70 # mm

holes = [
    (edge_dist, edge_dist), # Bottom-left
    (edge_dist + pitch, edge_dist), # Bottom-middle
    (edge_dist, p5[1] - edge_dist), # Left-middle
    (p4[0] - edge_dist, p4[1] - edge_dist), # Top-right (relative to p4)
    (p3[0] - edge_dist, p3[1] - edge_dist), # Right-middle (relative to p3)
    (p2[0] - edge_dist, edge_dist + pitch) # Bottom-right (relative to p2)
]

for h_pos in holes:
    msp.add_circle(h_pos, hole_diameter / 2, dxfattribs={"layer": "GEOMETRY"})

# Dimensions
char_height = 5.58

# Overall dimensions
draw_horizontal_dimension(msp, p1, p2, -30, f"{p2[0]} (EST)", char_height=char_height) # Base length
draw_vertical_dimension(msp, p1, p5, -30, f"{p5[1]} (EST)", char_height=char_height) # Left vertical height
draw_vertical_dimension(msp, p2, p3, 30, f"{p3[1]} (EST)", char_height=char_height) # Right vertical height
draw_horizontal_dimension(msp, (p5[0], p5[1]), (p4[0], p5[1]), 30, f"{p4[0] - p5[0]} (EST)", char_height=char_height) # Top horizontal segment length
draw_vertical_dimension(msp, (p4[0], p3[1]), p4, 30, f"{p4[1] - p3[1]} (EST)", char_height=char_height) # Vertical drop from p4 to p3's y-level
draw_horizontal_dimension(msp, (p1[0], p4[1]), p4, -60, f"{p4[0]} (EST)", char_height=char_height) # X-coord of p4 from origin

# Hole notes
mt = msp.add_mtext(f"6x Ø{hole_diameter} HOLES (EST)", dxfattribs={"layer": "ANNOTATION", "char_height": char_height})
mt.set_location((p2[0] / 2, p4[1] + 50), attachment_point=5)

# Part annotations
add_part_annotation(msp, part_name, material, thickness, qty, f"~{p2[0]}x{p4[1]} (Complex)", insert_point=(0, -100), char_height=char_height)

doc.saveas(out)