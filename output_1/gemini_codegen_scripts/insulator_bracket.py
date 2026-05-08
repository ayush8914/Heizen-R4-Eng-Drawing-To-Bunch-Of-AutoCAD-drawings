import ezdxf
import sys
import math

def draw_simple_arrowhead(msp, tip, angle_rad, size, layer="DIMENSION"):
    """Draws two lines for a simple arrowhead."""
    dx = size * math.cos(angle_rad + math.pi/6)
    dy = size * math.sin(angle_rad + math.pi/6)
    msp.add_line(tip, (tip[0] - dx, tip[1] - dy), dxfattribs={"layer": layer})
    dx = size * math.cos(angle_rad - math.pi/6)
    dy = size * math.sin(angle_rad - math.pi/6)
    msp.add_line(tip, (tip[0] - dx, tip[1] - dy), dxfattribs={"layer": layer})

def draw_linear_dimension(msp, p1, p2, offset, text, vertical=False, char_height=5.58):
    """Draws a linear dimension with extension lines and text."""
    
    arrow_size = 3

    # Define extension line start points
    ext_p1 = p1
    ext_p2 = p2

    # Define dimension line and text insertion points
    if vertical:
        # Sort points by Y-coordinate for consistent dimension line direction
        if ext_p1[1] > ext_p2[1]:
            ext_p1, ext_p2 = ext_p2, ext_p1

        ext_line_start1 = (ext_p1[0], ext_p1[1])
        ext_line_end1 = (ext_p1[0] + offset, ext_p1[1])
        ext_line_start2 = (ext_p2[0], ext_p2[1])
        ext_line_end2 = (ext_p2[0] + offset, ext_p2[1])

        dim_line_start = (ext_p1[0] + offset, ext_p1[1])
        dim_line_end = (ext_p2[0] + offset, ext_p2[1])
        
        text_insert = (dim_line_start[0] + 5, (dim_line_start[1] + dim_line_end[1]) / 2)
        text_rotation = 90
        text_attachment_point = 4 # Middle-Left

    else: # Horizontal
        # Sort points by X-coordinate for consistent dimension line direction
        if ext_p1[0] > ext_p2[0]:
            ext_p1, ext_p2 = ext_p2, ext_p1

        ext_line_start1 = (ext_p1[0], ext_p1[1])
        ext_line_end1 = (ext_p1[0], ext_p1[1] - offset)
        ext_line_start2 = (ext_p2[0], ext_p2[1])
        ext_line_end2 = (ext_p2[0], ext_p2[1] - offset)

        dim_line_start = (ext_p1[0], ext_p1[1] - offset)
        dim_line_end = (ext_p2[0], ext_p2[1] - offset)

        text_insert = ((dim_line_start[0] + dim_line_end[0]) / 2, dim_line_start[1] - 5)
        text_rotation = 0
        text_attachment_point = 5 # Middle-Center
        
    # Extension Lines
    msp.add_line(ext_line_start1, ext_line_end1, dxfattribs={"layer": "DIMENSION"})
    msp.add_line(ext_line_start2, ext_line_end2, dxfattribs={"layer": "DIMENSION"})

    # Dimension Line
    msp.add_line(dim_line_start, dim_line_end, dxfattribs={"layer": "DIMENSION"})

    # Arrowheads
    if vertical:
        draw_simple_arrowhead(msp, dim_line_start, math.pi/2, arrow_size, "DIMENSION")
        draw_simple_arrowhead(msp, dim_line_end, -math.pi/2, arrow_size, "DIMENSION")
    else:
        draw_simple_arrowhead(msp, dim_line_start, math.pi, arrow_size, "DIMENSION")
        draw_simple_arrowhead(msp, dim_line_end, 0, arrow_size, "DIMENSION")

    # Dimension Text
    mt = msp.add_mtext(str(text), dxfattribs={"layer": "ANNOTATION", "char_height": char_height})
    mt.set_location(insert=text_insert, attachment_point=text_attachment_point)
    mt.set_rotation(text_rotation)

def draw_diameter_dimension(msp, center, radius, text, char_height=5.58):
    """Draws a diameter dimension (for a circle)."""
    # Horizontal line through center
    p1 = (center[0] - radius, center[1])
    p2 = (center[0] + radius, center[1])
    msp.add_line(p1, p2, dxfattribs={"layer": "DIMENSION"})
    
    # Arrowheads
    draw_simple_arrowhead(msp, p1, math.pi, 3, "DIMENSION")
    draw_simple_arrowhead(msp, p2, 0, 3, "DIMENSION")
    
    # Text
    text_insert = (center[0], center[1] + radius + 5) # Above the circle
    mt = msp.add_mtext(f"Ø{text}", dxfattribs={"layer": "ANNOTATION", "char_height": char_height})
    mt.set_location(insert=text_insert, attachment_point=5) # Middle-Center

def draw_mtext(msp, text, insert_point, layer="ANNOTATION", char_height=5.58, attachment_point=1):
    mt = msp.add_mtext(text, dxfattribs={"layer": layer, "char_height": char_height})
    mt.set_location(insert=insert_point, attachment_point=attachment_point)

out = sys.argv[1]
doc = ezdxf.new("R2010", setup=True)
doc.units = ezdxf.units.MM
msp = doc.modelspace()

# Add layers
doc.layers.add("GEOMETRY", color=1) # Red
doc.layers.add("DIMENSION", color=2) # Yellow
doc.layers.add("ANNOTATION", color=7) # White

# Part parameters (ESTIMATED)
# Representing a simplified profile of an insulator bracket for fabrication
base_width = 250 # mm (attaches to tower)
base_height = 100 # mm
arm_extension = 100 # mm (extends out for insulator)
arm_width = 80 # mm
plate_thickness = 15 # mm (PL15)

hole_dia_tower = 22 # mm (for M20 bolts)
hole_dia_insulator = 26 # mm (for insulator shackle/pin)

# Geometry: A base rectangle with an arm extending from the top center
points = [
    (0, 0),
    (base_width, 0),
    (base_width, base_height),
    (base_width/2 + arm_width/2, base_height),
    (base_width/2 + arm_width/2, base_height + arm_extension),
    (base_width/2 - arm_width/2, base_height + arm_extension),
    (base_width/2 - arm_width/2, base_height),
    (0, base_height)
]
msp.add_lwpolyline(points, close=True, dxfattribs={"layer": "GEOMETRY"})

# Tower connection holes (4 holes on the base)
tower_holes = [
    (50, 25),
    (base_width - 50, 25),
    (50, base_height - 25),
    (base_width - 50, base_height - 25)
]
for h_pos in tower_holes:
    msp.add_circle(h_pos, hole_dia_tower / 2, dxfattribs={"layer": "GEOMETRY"})

# Insulator connection holes (2 holes on the extended arm)
insulator_holes = [
    (base_width/2 - 25, base_height + arm_extension - 25),
    (base_width/2 + 25, base_height + arm_extension - 25)
]
for h_pos in insulator_holes:
    msp.add_circle(h_pos, hole_dia_insulator / 2, dxfattribs={"layer": "GEOMETRY"})

# Annotations
draw_mtext(msp, "PART: INSULATOR BRACKET", (10, base_height + arm_extension + 50), attachment_point=1)
draw_mtext(msp, f"MATERIAL: PL{plate_thickness} (EST)", (10, base_height + arm_extension + 40), attachment_point=1)
draw_mtext(msp, "QTY: 6 (EST)", (10, base_height + arm_extension + 30), attachment_point=1)

# Dimensions
# Overall dimensions
draw_linear_dimension(msp, (0, 0), (base_width, 0), 20, base_width, vertical=False)
draw_linear_dimension(msp, (0, 0), (0, base_height + arm_extension), 20, base_height + arm_extension, vertical=True)

# Base width dimension
draw_linear_dimension(msp, (0, base_height), (base_width/2 - arm_width/2, base_height), 20, base_width/2 - arm_width/2, vertical=False)
draw_linear_dimension(msp, (base_width/2 + arm_width/2, base_height), (base_width, base_height), 20, base_width/2 - arm_width/2, vertical=False)
draw_linear_dimension(msp, (base_width/2 - arm_width/2, base_height), (base_width/2 + arm_width/2, base_height), -20, arm_width, vertical=False)

# Arm extension height
draw_linear_dimension(msp, (base_width/2 - arm_width/2, base_height), (base_width/2 - arm_width/2, base_height + arm_extension), 20, arm_extension, vertical=True)

# Tower hole dimensions (example for one set of holes)
draw_linear_dimension(msp, (0, tower_holes[0][1]), (tower_holes[0][0], tower_holes[0][1]), -20, tower_holes[0][0], vertical=False)
draw_linear_dimension(msp, (tower_holes[0][0], tower_holes[0][1]), (tower_holes[1][0], tower_holes[1][1]), -20, abs(tower_holes[1][0] - tower_holes[0][0]), vertical=False)
draw_linear_dimension(msp, (0, 0), (0, tower_holes[0][1]), 20, tower_holes[0][1], vertical=True)
draw_linear_dimension(msp, (0, tower_holes[2][1]), (0, tower_holes[0][1]), 20, abs(tower_holes[0][1]-tower_holes[2][1]), vertical=True)
draw_diameter_dimension(msp, tower_holes[0], hole_dia_tower / 2, hole_dia_tower)

# Insulator hole dimensions
draw_linear_dimension(msp, (0, insulator_holes[0][1]), (insulator_holes[0][0], insulator_holes[0][1]), 20, insulator_holes[0][0], vertical=False)
draw_linear_dimension(msp, (insulator_holes[0][0], insulator_holes[0][1]), (insulator_holes[1][0], insulator_holes[1][1]), 20, abs(insulator_holes[1][0] - insulator_holes[0][0]), vertical=False)
draw_linear_dimension(msp, (0, base_height + arm_extension), (0, insulator_holes[0][1]), 20, abs(base_height + arm_extension - insulator_holes[0][1]), vertical=True)
draw_diameter_dimension(msp, insulator_holes[0], hole_dia_insulator / 2, hole_dia_insulator)

doc.saveas(out)