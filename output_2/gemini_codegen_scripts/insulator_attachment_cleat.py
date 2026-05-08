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

# --- Part specific geometry and annotations: Insulator Attachment Cleat (Developed Flat Pattern) ---
part_name = "INSULATOR ATTACHMENT CLEAT"
base_width = 100 # EST
flange_height = 150 # EST
flange_depth = 50 # EST (this is the bend depth, so it's part of the developed length)
thickness = 10 # EST PL10
material = "S355JR"
qty = 6 # EST (3 crossarms * 2 ends)
bolt_dia_attachment = 18 # EST for M16 bolts
bolt_dia_insulator = 25 # EST for insulator pin

# Developed flat pattern points
# Assuming origin (0,0) at bottom-left of the first flange
points = [
    (0, 0),
    (flange_depth, 0), # End of first flange, start of base
    (flange_depth + base_width, 0), # End of base, start of second flange
    (flange_depth + base_width + flange_depth, 0), # End of second flange
    (flange_depth + base_width + flange_depth, flange_height),
    (flange_depth + base_width, flange_height),
    (flange_depth, flange_height),
    (0, flange_height)
]
msp.add_lwpolyline(points, close=True, dxfattribs={"layer": "GEOMETRY"})

# Bend lines (indicated by dashed lines)
msp.add_line((flange_depth, 0), (flange_depth, flange_height), dxfattribs={"layer": "GEOMETRY", "linetype": "DASHED"})
msp.add_line((flange_depth + base_width, 0), (flange_depth + base_width, flange_height), dxfattribs={"layer": "GEOMETRY", "linetype": "DASHED"})

# Attachment holes on the base (top edge of the base section in flat pattern)
hole_spacing_base = 40
hole_offset_base_x = (base_width - hole_spacing_base) / 2 + flange_depth
hole_offset_base_y = flange_height - 30 # EST from top edge of flange
holes_attachment = [
    (hole_offset_base_x, hole_offset_base_y),
    (hole_offset_base_x + hole_spacing_base, hole_offset_base_y)
]
for h_center in holes_attachment:
    msp.add_circle(h_center, bolt_dia_attachment / 2, dxfattribs={"layer": "GEOMETRY"})

# Insulator holes on the flanges (centered vertically on each flange)
hole_offset_flange_y = flange_height / 2
holes_insulator = [
    (flange_depth / 2, hole_offset_flange_y),
    (flange_depth + base_width + flange_depth / 2, hole_offset_flange_y)
]
for h_center in holes_insulator:
    msp.add_circle(h_center, bolt_dia_insulator / 2, dxfattribs={"layer": "GEOMETRY"})

# Annotations
mt = msp.add_mtext(
    f"PART: {part_name}\nMATERIAL: {material}\nTHICKNESS: PL{thickness}\nQTY: {qty} (EST)",
    dxfattribs={"layer": "ANNOTATION", "char_height": 5.58}
)
mt.set_location((flange_depth + base_width / 2, flange_height + 50), attachment_point=5) # Middle-center

# Dimensions
dim_offset_h = 20
dim_offset_v = 20
text_height = 3.5

# Overall developed length
add_dimension(msp, (0, 0), (flange_depth + base_width + flange_depth, 0), dim_offset_h, f"{flange_depth + base_width + flange_depth}", orientation="horizontal", char_height=text_height)
# Individual sections
add_dimension(msp, (0, 0), (flange_depth, 0), dim_offset_h + 20, f"{flange_depth}", orientation="horizontal", char_height=text_height)
add_dimension(msp, (flange_depth, 0), (flange_depth + base_width, 0), dim_offset_h + 20, f"{base_width}", orientation="horizontal", char_height=text_height)
add_dimension(msp, (flange_depth + base_width, 0), (flange_depth + base_width + flange_depth, 0), dim_offset_h + 20, f"{flange_depth}", orientation="horizontal", char_height=text_height)

# Overall height
add_dimension(msp, (flange_depth + base_width + flange_depth, 0), (flange_depth + base_width + flange_depth, flange_height), dim_offset_v, f"{flange_height}", orientation="vertical", char_height=text_height)

# Hole dimensions (attachment holes)
add_dimension(msp, (holes_attachment[0][0], flange_height), (holes_attachment[1][0], flange_height), dim_offset_h + 40, f"{hole_spacing_base}", orientation="horizontal", char_height=text_height)
add_dimension(msp, (flange_depth, flange_height), (holes_attachment[0][0], flange_height), dim_offset_h + 40, f"{hole_offset_base_x - flange_depth}", orientation="horizontal", char_height=text_height)
add_dimension(msp, (flange_depth + base_width, flange_height), (holes_attachment[1][0], flange_height), dim_offset_h + 40, f"{flange_depth + base_width - holes_attachment[1][0]}", orientation="horizontal", char_height=text_height)

add_dimension(msp, (flange_depth + base_width + flange_depth, holes_attachment[0][1]), (flange_depth + base_width + flange_depth, flange_height), dim_offset_v + 20, f"{flange_height - holes_attachment[0][1]}", orientation="vertical", char_height=text_height)

# Hole notes
add_hole_note(msp, holes_attachment[0], bolt_dia_attachment / 2, f"2x Ø{bolt_dia_attachment}", char_height=text_height, leader_offset=(flange_depth + 10, flange_height - 10))
add_hole_note(msp, holes_insulator[0], bolt_dia_insulator / 2, f"2x Ø{bolt_dia_insulator}", char_height=text_height, leader_offset=(flange_depth + 10, flange_height / 2 + 10))

doc.saveas(out)