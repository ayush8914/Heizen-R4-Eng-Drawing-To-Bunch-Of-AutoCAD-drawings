import sys
import ezdxf
import math

def draw_horizontal_dimension(msp, p1, p2, offset_y, text, char_height=5.58, layer="DIMENSION", text_layer="ANNOTATION"):
    # p1 and p2 are points on the geometry (e.g., (x1, y1), (x2, y2))
    # offset_y is the vertical distance from the geometry to the dimension line
    
    # Extension lines
    msp.add_line((p1[0], p1[1]), (p1[0], p1[1] + offset_y), dxfattribs={"layer": layer})
    msp.add_line((p2[0], p2[1]), (p2[0], p2[1] + offset_y), dxfattribs={"layer": layer})
    
    # Dimension line
    dim_line_y = p1[1] + offset_y
    msp.add_line((p1[0], dim_line_y), (p2[0], dim_line_y), dxfattribs={"layer": layer})
    
    # Arrowheads (simple lines)
    arrow_size = char_height * 0.8
    # Left arrow
    msp.add_line((p1[0], dim_line_y), (p1[0] + arrow_size, dim_line_y + arrow_size/2), dxfattribs={"layer": layer})
    msp.add_line((p1[0], dim_line_y), (p1[0] + arrow_size, dim_line_y - arrow_size/2), dxfattribs={"layer": layer})
    # Right arrow
    msp.add_line((p2[0], dim_line_y), (p2[0] - arrow_size, dim_line_y + arrow_size/2), dxfattribs={"layer": layer})
    msp.add_line((p2[0], dim_line_y), (p2[0] - arrow_size, dim_line_y - arrow_size/2), dxfattribs={"layer": layer})

    # Dimension text
    text_insert_point = ((p1[0] + p2[0]) / 2, dim_line_y + char_height / 2)
    mt = msp.add_mtext(text, dxfattribs={"layer": text_layer, "char_height": char_height})
    mt.set_location(text_insert_point, attachment_point=5) # Middle-center

def draw_vertical_dimension(msp, p1, p2, offset_x, text, char_height=5.58, layer="DIMENSION", text_layer="ANNOTATION"):
    # p1 and p2 are points on the geometry (e.g., (x1, y1), (x2, y2))
    # offset_x is the horizontal distance from the geometry to the dimension line
    
    # Extension lines
    msp.add_line((p1[0], p1[1]), (p1[0] + offset_x, p1[1]), dxfattribs={"layer": layer})
    msp.add_line((p2[0], p2[1]), (p2[0] + offset_x, p2[1]), dxfattribs={"layer": layer})
    
    # Dimension line
    dim_line_x = p1[0] + offset_x
    msp.add_line((dim_line_x, p1[1]), (dim_line_x, p2[1]), dxfattribs={"layer": layer})

    # Arrowheads (simple lines)
    arrow_size = char_height * 0.8
    # Bottom arrow
    msp.add_line((dim_line_x, p1[1]), (dim_line_x + arrow_size/2, p1[1] + arrow_size), dxfattribs={"layer": layer})
    msp.add_line((dim_line_x, p1[1]), (dim_line_x - arrow_size/2, p1[1] + arrow_size), dxfattribs={"layer": layer})
    # Top arrow
    msp.add_line((dim_line_x, p2[1]), (dim_line_x + arrow_size/2, p2[1] - arrow_size), dxfattribs={"layer": layer})
    msp.add_line((dim_line_x, p2[1]), (dim_line_x - arrow_size/2, p2[1] - arrow_size), dxfattribs={"layer": layer})

    # Dimension text
    text_insert_point = (dim_line_x + char_height / 2, (p1[1] + p2[1]) / 2)
    mt = msp.add_mtext(text, dxfattribs={"layer": text_layer, "char_height": char_height})
    mt.set_location(text_insert_point, attachment_point=5) # Middle-center

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
        mt.set_location((insert_point[0], insert_point[1] - y_offset), attachment_point=7) # Top-left
        y_offset += char_height * 1.5 # Line spacing

out = sys.argv[1]
doc = ezdxf.new("R2010", setup=True)
doc.units = ezdxf.units.MM
msp = doc.modelspace()

# Define layers
doc.layers.add("GEOMETRY", color=1) # Red
doc.layers.add("DIMENSION", color=3) # Green
doc.layers.add("ANNOTATION", color=7) # White/Black

# Part parameters (ESTIMATED)
part_name = "TOWER LEG SPLICE PLATE"
material = "STEEL"
thickness = 12 # mm
qty = "EST. 4 per splice location"
plate_length = 400 # mm
plate_width = 200 # mm
hole_diameter = 22 # mm (for M20 bolts)
edge_dist_long = 35 # mm
edge_dist_short = 35 # mm
pitch_long = 80 # mm
stagger_offset = 40 # mm (half pitch_long)

# Geometry
points = [(0,0), (plate_length,0), (plate_length,plate_width), (0,plate_width)]
msp.add_lwpolyline(points, close=True, dxfattribs={"layer": "GEOMETRY"})

# Holes (8 holes, staggered pattern, 2 rows)
holes = []
# Row 1 (bottom)
for i in range(4):
    x = edge_dist_long + i * pitch_long
    y = edge_dist_short
    holes.append((x, y))
# Row 2 (top, staggered)
for i in range(4):
    x = edge_dist_long + stagger_offset + i * pitch_long
    y = plate_width - edge_dist_short
    holes.append((x, y))

for h_pos in holes:
    msp.add_circle(h_pos, hole_diameter / 2, dxfattribs={"layer": "GEOMETRY"})

# Dimensions
char_height = 5.58
# Overall dimensions
draw_horizontal_dimension(msp, (0,0), (plate_length,0), -30, f"{plate_length} (EST)", char_height=char_height)
draw_vertical_dimension(msp, (plate_length,0), (plate_length,plate_width), 30, f"{plate_width} (EST)", char_height=char_height)

# Hole dimensions (bottom row example)
draw_horizontal_dimension(msp, (0, edge_dist_short), (holes[0][0], edge_dist_short), 60, f"{edge_dist_long}", char_height=char_height)
for i in range(3):
    draw_horizontal_dimension(msp, (holes[i][0], edge_dist_short), (holes[i+1][0], edge_dist_short), 60, f"{pitch_long}", char_height=char_height)
draw_horizontal_dimension(msp, (holes[3][0], edge_dist_short), (plate_length, edge_dist_short), 60, f"{plate_length - holes[3][0]}", char_height=char_height)

draw_vertical_dimension(msp, (edge_dist_long, 0), (edge_dist_long, edge_dist_short), -30, f"{edge_dist_short}", char_height=char_height)
draw_vertical_dimension(msp, (edge_dist_long, edge_dist_short), (edge_dist_long, plate_width - edge_dist_short), -30, f"{plate_width - 2 * edge_dist_short}", char_height=char_height)
draw_vertical_dimension(msp, (edge_dist_long, plate_width - edge_dist_short), (edge_dist_long, plate_width), -30, f"{edge_dist_short}", char_height=char_height)

# Stagger offset dimension
# Draw a leader line from a hole in the top row to indicate stagger
leader_start = (holes[4][0], holes[4][1])
leader_end = (holes[4][0] - 50, holes[4][1] + 50)
msp.add_line(leader_start, leader_end, dxfattribs={"layer": "DIMENSION"})
mt = msp.add_mtext(f"STAGGER {stagger_offset} (EST)", dxfattribs={"layer": "ANNOTATION", "char_height": char_height})
mt.set_location((leader_end[0] - 5, leader_end[1] + char_height/2), attachment_point=6) # Middle-right

# Hole notes
mt = msp.add_mtext(f"8x Ø{hole_diameter} HOLES (EST)", dxfattribs={"layer": "ANNOTATION", "char_height": char_height})
mt.set_location((plate_length / 2, plate_width + 50), attachment_point=5)

# Part annotations
add_part_annotation(msp, part_name, material, thickness, qty, f"{plate_length}x{plate_width}", insert_point=(0, -100), char_height=char_height)

doc.saveas(out)