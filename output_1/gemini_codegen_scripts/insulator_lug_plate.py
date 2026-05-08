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

def draw_radius_dimension(msp, center, radius, text, angle_deg, char_height=5.58):
    """Draws a radius dimension line and text for an arc/fillet."""
    angle_rad = math.radians(angle_deg)
    # Point on the arc where the dimension line starts
    arc_point = (center[0] + radius * math.cos(angle_rad),
                 center[1] + radius * math.sin(angle_rad))
    
    # End point of the dimension line away from the arc
    dim_line_end_point = (center[0] + (radius + 20) * math.cos(angle_rad + math.pi/4),
                          center[1] + (radius + 20) * math.sin(angle_rad + math.pi/4))
    
    msp.add_line(arc_point, dim_line_end_point, dxfattribs={"layer": "DIMENSION"})
    
    # Text
    text_insert = (dim_line_end_point[0] + 5, dim_line_end_point[1] + 5) # Offset text slightly
    mt = msp.add_mtext(f"R{text}", dxfattribs={"layer": "ANNOTATION", "char_height": char_height})
    mt.set_location(insert=text_insert, attachment_point=1) # Top-Left

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
lug_length = 150 # mm
lug_width = 80 # mm
radius_end = lug_width / 2 # for rounded end
plate_thickness = 12 # mm (PL12)

hole_dia_shackle = 30 # mm
hole_dia_bracket = 18 # mm (for M16 bolts)

# Geometry
# Start with the rectangular part, then add the rounded end
# Datum (0,0) is bottom-left of the rectangular base
points = [
    (0, 0),
    (lug_length - radius_end, 0),
    (lug_length - radius_end, lug_width)
]
msp.add_lwpolyline(points, dxfattribs={"layer": "GEOMETRY"})

# Rounded end
center_arc = (lug_length - radius_end, lug_width / 2)
msp.add_arc(center_arc, radius_end, 90, 270, dxfattribs={"layer": "GEOMETRY"})

# Other lines to close the shape
msp.add_line((0, lug_width), (lug_length - radius_end, lug_width), dxfattribs={"layer": "GEOMETRY"})
msp.add_line((0, lug_width), (0, 0), dxfattribs={"layer": "GEOMETRY"})

# Shackle hole (centered in the rounded end)
shackle_hole_center = (lug_length, lug_width / 2)
msp.add_circle(shackle_hole_center, hole_dia_shackle / 2, dxfattribs={"layer": "GEOMETRY"})

# Bracket connection holes (2 holes)
bracket_holes = [
    (50, lug_width / 2 - 25),
    (50, lug_width / 2 + 25)
]
for h_pos in bracket_holes:
    msp.add_circle(h_pos, hole_dia_bracket / 2, dxfattribs={"layer": "GEOMETRY"})

# Annotations
draw_mtext(msp, "PART: INSULATOR LUG PLATE", (10, lug_width + 50), attachment_point=1)
draw_mtext(msp, f"MATERIAL: PL{plate_thickness} (EST)", (10, lug_width + 40), attachment_point=1)
draw_mtext(msp, "QTY: 12 (EST)", (10, lug_width + 30), attachment_point=1)

# Dimensions
# Overall dimensions
draw_linear_dimension(msp, (0, 0), (lug_length, 0), 20, lug_length, vertical=False)
draw_linear_dimension(msp, (lug_length, 0), (lug_length, lug_width), 20, lug_width, vertical=True)

# Bracket hole dimensions
draw_linear_dimension(msp, (0, bracket_holes[0][1]), (bracket_holes[0][0], bracket_holes[0][1]), -20, bracket_holes[0][0], vertical=False)
draw_linear_dimension(msp, (bracket_holes[0][0], bracket_holes[0][1]), (bracket_holes[1][0], bracket_holes[1][1]), -20, abs(bracket_holes[1][1] - bracket_holes[0][1]), vertical=True)
draw_diameter_dimension(msp, bracket_holes[0], hole_dia_bracket / 2, hole_dia_bracket)

# Shackle hole dimension
draw_linear_dimension(msp, (lug_length - radius_end, lug_width/2), (shackle_hole_center[0], shackle_hole_center[1]), 20, radius_end, vertical=False)
draw_diameter_dimension(msp, shackle_hole_center, hole_dia_shackle / 2, hole_dia_shackle)

# Radius dimension for rounded end
draw_radius_dimension(msp, center_arc, radius_end, radius_end, 180) # Angle for horizontal dimension line

doc.saveas(out)