import sys
import ezdxf
import math

def add_dimension(msp, p1, p2, offset, text, orientation="horizontal", layer="DIMENSION", text_layer="ANNOTATION", char_height=3.5):
    """
    Adds a simplified dimension line with text and arrowheads.
    p1, p2: start and end points of the feature being dimensioned.
    offset: distance from the feature to the dimension line.
    text: dimension text.
    orientation: "horizontal" or "vertical".
    """
    arrow_len = 5 # Length of arrowhead lines
    arrow_angle = math.radians(25) # Angle for arrowhead lines

    if orientation == "horizontal":
        dim_y = p1[1] - offset
        # Extension lines
        msp.add_line((p1[0], p1[1]), (p1[0], dim_y), dxfattribs={"layer": layer})
        msp.add_line((p2[0], p2[1]), (p2[0], dim_y), dxfattribs={"layer": layer})
        # Dimension line
        msp.add_line((p1[0], dim_y), (p2[0], dim_y), dxfattribs={"layer": layer})
        # Arrowheads
        # Left arrow
        msp.add_line((p1[0], dim_y), (p1[0] + arrow_len * math.cos(arrow_angle), dim_y + arrow_len * math.sin(arrow_angle)), dxfattribs={"layer": layer})
        msp.add_line((p1[0], dim_y), (p1[0] + arrow_len * math.cos(arrow_angle), dim_y - arrow_len * math.sin(arrow_angle)), dxfattribs={"layer": layer})
        # Right arrow
        msp.add_line((p2[0], dim_y), (p2[0] - arrow_len * math.cos(arrow_angle), dim_y + arrow_len * math.sin(arrow_angle)), dxfattribs={"layer": layer})
        msp.add_line((p2[0], dim_y), (p2[0] - arrow_len * math.cos(arrow_angle), dim_y - arrow_len * math.sin(arrow_angle)), dxfattribs={"layer": layer})
        # Text
        mt = msp.add_mtext(text, dxfattribs={"layer": text_layer, "char_height": char_height})
        mt.set_location(((p1[0] + p2[0]) / 2, dim_y - char_height - 2), attachment_point=5) # Middle-center, slightly below dim line
    elif orientation == "vertical":
        dim_x = p1[0] - offset
        # Extension lines
        msp.add_line((p1[0], p1[1]), (dim_x, p1[1]), dxfattribs={"layer": layer})
        msp.add_line((p2[0], p2[1]), (dim_x, p2[1]), dxfattribs={"layer": layer})
        # Dimension line
        msp.add_line((dim_x, p1[1]), (dim_x, p2[1]), dxfattribs={"layer": layer})
        # Arrowheads
        # Bottom arrow
        msp.add_line((dim_x, p1[1]), (dim_x + arrow_len * math.sin(arrow_angle), p1[1] + arrow_len * math.cos(arrow_angle)), dxfattribs={"layer": layer})
        msp.add_line((dim_x, p1[1]), (dim_x - arrow_len * math.sin(arrow_angle), p1[1] + arrow_len * math.cos(arrow_angle)), dxfattribs={"layer": layer})
        # Top arrow
        msp.add_line((dim_x, p2[1]), (dim_x + arrow_len * math.sin(arrow_angle), p2[1] - arrow_len * math.cos(arrow_angle)), dxfattribs={"layer": layer})
        msp.add_line((dim_x, p2[1]), (dim_x - arrow_len * math.sin(arrow_angle), p2[1] - arrow_len * math.cos(arrow_angle)), dxfattribs={"layer": layer})
        # Text
        mt = msp.add_mtext(text, dxfattribs={"layer": text_layer, "char_height": char_height})
        mt.set_location((dim_x - char_height - 2, (p1[1] + p2[1]) / 2), attachment_point=5) # Middle-center, slightly left of dim line

def add_hole_note(msp, center, radius, text, layer="ANNOTATION", char_height=3.5, leader_offset=(20, 20)):
    """
    Adds a hole note with a leader line.
    center: (x, y) of the hole center.
    radius: radius of the hole.
    text: annotation text for the hole (e.g., "Ø22").
    leader_offset: (dx, dy) from hole center to start of text.
    """
    # Leader line from hole edge to text
    start_point = (center[0] + radius, center[1]) # Start from right edge of hole
    end_point = (center[0] + leader_offset[0], center[1] + leader_offset[1])
    msp.add_line(start_point, end_point, dxfattribs={"layer": layer})
    
    mt = msp.add_mtext(text, dxfattribs={"layer": layer, "char_height": char_height})
    mt.set_location(end_point, attachment_point=7) # Top-left for text after leader

# Get output filename from command line argument
out = sys.argv[1]

doc = ezdxf.new("R2010", setup=True)
doc.units = ezdxf.units.MM
msp = doc.modelspace()

# Define layers
doc.layers.add("GEOMETRY", color=7) # White/Black
doc.layers.add("DIMENSION", color=3) # Green
doc.layers.add("ANNOTATION", color=1) # Red

# --- Part specific geometry and annotations: Horizontal Member Gusset ---
part_name = "HORIZONTAL MEMBER GUSSET"
base_width = 300 # EST
height = 250 # EST
chamfer_size = 50 # EST for clipped corners
thickness = 12 # EST PL12
material = "S355JR"
qty = "VARIES" # Many throughout the tower
bolt_dia = 18 # EST for M16 bolts

# Geometry (triangular with clipped corners)
# Origin (0,0) at bottom-left corner
points = [
    (0, 0),
    (base_width, 0),
    (base_width - chamfer_size, height), # Top-right clipped corner
    (chamfer_size, height) # Top-left clipped corner
]
msp.add_lwpolyline(points, close=True, dxfattribs={"layer": "GEOMETRY"})

# Bolt holes (EST locations)
holes = [
    (50, 50), # Bottom-left
    (base_width - 50, 50), # Bottom-right
    (base_width / 2, height - 50) # Top-center
]
for h_center in holes:
    msp.add_circle(h_center, bolt_dia / 2, dxfattribs={"layer": "GEOMETRY"})

# Annotations
mt = msp.add_mtext(
    f"PART: {part_name}\nMATERIAL: {material}\nTHICKNESS: PL{thickness}\nQTY: {qty} (EST)",
    dxfattribs={"layer": "ANNOTATION", "char_height": 5.58}
)
mt.set_location((base_width / 2, height + 50), attachment_point=5) # Middle-center

# Dimensions
dim_offset_h = 20
dim_offset_v = 20
text_height = 3.5

# Overall width
add_dimension(msp, (0, 0), (base_width, 0), dim_offset_h, f"{base_width}", orientation="horizontal", char_height=text_height)
# Overall height
add_dimension(msp, (base_width, 0), (base_width, height), dim_offset_v, f"{height}", orientation="vertical", char_height=text_height)

# Chamfer dimensions
add_dimension(msp, (0, height), (chamfer_size, height), dim_offset_h + 20, f"{chamfer_size}", orientation="horizontal", char_height=text_height)
add_dimension(msp, (base_width, height), (base_width - chamfer_size, height), dim_offset_h + 20, f"{chamfer_size}", orientation="horizontal", char_height=text_height)

# Hole dimensions (horizontal)
add_dimension(msp, (0, 0), (holes[0][0], 0), dim_offset_h + 40, f"{holes[0][0]}", orientation="horizontal", char_height=text_height)
add_dimension(msp, (holes[0][0], 0), (holes[1][0], 0), dim_offset_h + 40, f"{holes[1][0] - holes[0][0]}", orientation="horizontal", char_height=text_height)
add_dimension(msp, (holes[1][0], 0), (base_width, 0), dim_offset_h + 40, f"{base_width - holes[1][0]}", orientation="horizontal", char_height=text_height)

# Hole dimensions (vertical)
add_dimension(msp, (base_width, 0), (base_width, holes[0][1]), dim_offset_v + 40, f"{holes[0][1]}", orientation="vertical", char_height=text_height)
add_dimension(msp, (base_width, holes[0][1]), (base_width, holes[2][1]), dim_offset_v + 40, f"{holes[2][1] - holes[0][1]}", orientation="vertical", char_height=text_height)
add_dimension(msp, (base_width, holes[2][1]), (base_width, height), dim_offset_v + 40, f"{height - holes[2][1]}", orientation="vertical", char_height=text_height)

# Hole notes
add_hole_note(msp, holes[0], bolt_dia / 2, f"3x Ø{bolt_dia}", char_height=text_height, leader_offset=(chamfer_size + 10, chamfer_size + 10))

doc.saveas(out)