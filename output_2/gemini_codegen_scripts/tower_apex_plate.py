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

# --- Part specific geometry and annotations: Tower Apex Plate ---
part_name = "TOWER APEX PLATE"
part_width = 300 # EST
part_height = 300 # EST
thickness = 16 # EST PL16
material = "S355JR"
qty = 1
bolt_dia_main = 22 # EST for M20 bolts
bolt_dia_center = 30 # EST for finial/lightning rod

# Geometry
points = [(0,0), (part_width,0), (part_width,part_height), (0,part_height)]
msp.add_lwpolyline(points, close=True, dxfattribs={"layer": "GEOMETRY"})

# Main member bolt holes (4 corners)
hole_offset = 50 # EST from edges
holes_main = [
    (hole_offset, hole_offset),
    (part_width - hole_offset, hole_offset),
    (part_width - hole_offset, part_height - hole_offset),
    (hole_offset, part_height - hole_offset)
]
for h_center in holes_main:
    msp.add_circle(h_center, bolt_dia_main / 2, dxfattribs={"layer": "GEOMETRY"})

# Central hole
center_hole_pos = (part_width / 2, part_height / 2)
msp.add_circle(center_hole_pos, bolt_dia_center / 2, dxfattribs={"layer": "GEOMETRY"})

# Annotations
mt = msp.add_mtext(
    f"PART: {part_name}\nMATERIAL: {material}\nTHICKNESS: PL{thickness}\nQTY: {qty} (EST)",
    dxfattribs={"layer": "ANNOTATION", "char_height": 5.58}
)
mt.set_location((part_width / 2, part_height + 50), attachment_point=5) # Middle-center

# Dimensions
dim_offset_h = 20
dim_offset_v = 20
text_height = 3.5

# Overall width
add_dimension(msp, (0, 0), (part_width, 0), dim_offset_h, f"{part_width}", orientation="horizontal", char_height=text_height)
# Overall height
add_dimension(msp, (part_width, 0), (part_width, part_height), dim_offset_v, f"{part_height}", orientation="vertical", char_height=text_height)

# Hole dimensions (horizontal)
add_dimension(msp, (holes_main[0][0], 0), (holes_main[1][0], 0), dim_offset_h + 20, f"{part_width - 2 * hole_offset}", orientation="horizontal", char_height=text_height)
add_dimension(msp, (0, 0), (holes_main[0][0], 0), dim_offset_h + 20, f"{hole_offset}", orientation="horizontal", char_height=text_height)
add_dimension(msp, (holes_main[1][0], 0), (part_width, 0), dim_offset_h + 20, f"{hole_offset}", orientation="horizontal", char_height=text_height)

# Hole dimensions (vertical)
add_dimension(msp, (part_width, holes_main[0][1]), (part_width, holes_main[2][1]), dim_offset_v + 20, f"{part_height - 2 * hole_offset}", orientation="vertical", char_height=text_height)
add_dimension(msp, (part_width, 0), (part_width, holes_main[0][1]), dim_offset_v + 20, f"{hole_offset}", orientation="vertical", char_height=text_height)
add_dimension(msp, (part_width, holes_main[2][1]), (part_width, part_height), dim_offset_v + 20, f"{hole_offset}", orientation="vertical", char_height=text_height)

# Hole notes
add_hole_note(msp, holes_main[0], bolt_dia_main / 2, f"4x Ø{bolt_dia_main}", char_height=text_height, leader_offset=(hole_offset + 10, hole_offset + 10))
add_hole_note(msp, center_hole_pos, bolt_dia_center / 2, f"1x Ø{bolt_dia_center}", char_height=text_height, leader_offset=(hole_offset + 10, -hole_offset - 10))

doc.saveas(out)