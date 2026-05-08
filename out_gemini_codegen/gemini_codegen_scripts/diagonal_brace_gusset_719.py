import sys
import ezdxf
import math

# Output filename is passed as a command-line argument
try:
    out = sys.argv[1]
except IndexError:
    print("Error: Please provide an output DXF filename as an argument.")
    sys.exit(1)

doc = ezdxf.new('R2010', setup=True)
doc.units = ezdxf.units.MM # Set drawing units to millimeters
msp = doc.modelspace()

# Add layers
doc.layers.add("GEOMETRY", color=1)  # Red for main geometry
doc.layers.add("DIMENSION", color=5) # Blue for dimensions
doc.layers.add("ANNOTATION", color=3) # Green for text annotations
doc.layers.add("HOLES", color=2) # Yellow for holes

# Define char_height for MTEXT (ezdxf recommends char_height, not height)
text_height_mtext = 5.58 # Standard text height for MTEXT
text_height_text = 5.58 # Standard text height for TEXT (for dimension values)

# --- Geometry Definition ---
# Part 719: Diagonal Brace Gusset (L50x15 connection)
# Based on 'BLE 15x236-719' callout and visual interpretation.
# Thickness: 15mm
# Material: S235JR
# QTY: Multiple (implied)

plate_thickness = 15
plate_height = 236 # Dimension from 'BLE 15x236' (EST)
plate_bottom_width = 250 # Estimated from proportionality (same as 714 for standardization) (EST)
plate_top_width = 150 # Estimated from proportionality (same as 714 for standardization) (EST)

# Gusset profile points (trapezoid) - same as 714 for standardization
points = [
    (0, 0),
    (plate_bottom_width, 0),
    (plate_top_width, plate_height),
    (0, plate_height)
]
msp.add_lwpolyline(points, close=True, dxfattribs={"layer": "GEOMETRY"})

# Hole dimensions (M27 bolts -> Ø30 holes)
hole_diameter = 30
hole_radius = hole_diameter / 2

# Hole positions (estimated based on typical patterns and M27 bolt spacing) - same as 714 for standardization
# Two holes for connection to main column (bottom edge)
hole1_pos = (60, 50)
hole2_pos = (plate_bottom_width - 60, 50)
# Two holes for connection to diagonal brace (upper section)
hole3_pos = (30, plate_height - 50)
hole4_pos = (plate_top_width - 30, plate_height - 50)

msp.add_circle(hole1_pos, hole_radius, dxfattribs={"layer": "HOLES"})
msp.add_circle(hole2_pos, hole_radius, dxfattribs={"layer": "HOLES"})
msp.add_circle(hole3_pos, hole_radius, dxfattribs={"layer": "HOLES"})
msp.add_circle(hole4_pos, hole_radius, dxfattribs={"layer": "HOLES"})

# --- Annotations Definition ---
# Part Title
msp.add_mtext("PART: diagonal_brace_gusset_719", dxfattribs={"layer": "ANNOTATION", "char_height": text_height_mtext}).set_location((plate_bottom_width / 2, -50), attachment_point=5)
msp.add_mtext("DESCRIPTION: Gusset plate for L50x15 brace", dxfattribs={"layer": "ANNOTATION", "char_height": text_height_mtext}).set_location((plate_bottom_width / 2, -60), attachment_point=5)
msp.add_mtext(f"MATERIAL: S235JR", dxfattribs={"layer": "ANNOTATION", "char_height": text_height_mtext}).set_location((plate_bottom_width / 2, -70), attachment_point=5)
msp.add_mtext(f"THICKNESS: {plate_thickness} mm", dxfattribs={"layer": "ANNOTATION", "char_height": text_height_mtext}).set_location((plate_bottom_width / 2, -80), attachment_point=5)
msp.add_mtext("QTY: 1 (as distinct fabrication item)", dxfattribs={"layer": "ANNOTATION", "char_height": text_height_mtext}).set_location((plate_bottom_width / 2, -90), attachment_point=5)
msp.add_mtext("HOLES: 4x Ø30 (for M27 bolts)", dxfattribs={"layer": "ANNOTATION", "char_height": text_height_mtext}).set_location((plate_bottom_width / 2, -100), attachment_point=5)

# Overall dimensions
# Bottom Width dimension
dim_offset_x = 30
msp.add_line((0, 0 - dim_offset_x), (0, -10 - dim_offset_x), dxfattribs={"layer": "DIMENSION"})
msp.add_line((plate_bottom_width, 0 - dim_offset_x), (plate_bottom_width, -10 - dim_offset_x), dxfattribs={"layer": "DIMENSION"})
msp.add_line((0, -20 - dim_offset_x), (plate_bottom_width, -20 - dim_offset_x), dxfattribs={"layer": "DIMENSION"})
msp.add_line((0, -20 - dim_offset_x), (5, -15 - dim_offset_x), dxfattribs={"layer": "DIMENSION"})
msp.add_line((0, -20 - dim_offset_x), (5, -25 - dim_offset_x), dxfattribs={"layer": "DIMENSION"})
msp.add_line((plate_bottom_width, -20 - dim_offset_x), (plate_bottom_width - 5, -15 - dim_offset_x), dxfattribs={"layer": "DIMENSION"})
msp.add_line((plate_bottom_width, -20 - dim_offset_x), (plate_bottom_width - 5, -25 - dim_offset_x), dxfattribs={"layer": "DIMENSION"})
msp.add_mtext(f"{plate_bottom_width}", dxfattribs={"layer": "ANNOTATION", "char_height": text_height_text}).set_location((plate_bottom_width / 2, -20 - dim_offset_x), attachment_point=5)

# Height dimension
dim_offset_y = 30
msp.add_line((-dim_offset_y, 0), (-10 - dim_offset_y, 0), dxfattribs={"layer": "DIMENSION"})
msp.add_line((-dim_offset_y, plate_height), (-10 - dim_offset_y, plate_height), dxfattribs={"layer": "DIMENSION"})
msp.add_line((-20 - dim_offset_y, 0), (-20 - dim_offset_y, plate_height), dxfattribs={"layer": "DIMENSION"})
msp.add_line((-20 - dim_offset_y, 0), (-15 - dim_offset_y, 5), dxfattribs={"layer": "DIMENSION"})
msp.add_line((-20 - dim_offset_y, 0), (-25 - dim_offset_y, 5), dxfattribs={"layer": "DIMENSION"})
msp.add_line((-20 - dim_offset_y, plate_height), (-15 - dim_offset_y, plate_height - 5), dxfattribs={"layer": "DIMENSION"})
msp.add_line((-20 - dim_offset_y, plate_height), (-25 - dim_offset_y, plate_height - 5), dxfattribs={"layer": "DIMENSION"})
msp.add_mtext(f"{plate_height}", dxfattribs={"layer": "ANNOTATION", "char_height": text_height_text}).set_location((-20 - dim_offset_y, plate_height / 2), attachment_point=5)

# Top Width dimension
dim_offset_top_x = 30
msp.add_line((0, plate_height + dim_offset_top_x), (0, plate_height + 10 + dim_offset_top_x), dxfattribs={"layer": "DIMENSION"})
msp.add_line((plate_top_width, plate_height + dim_offset_top_x), (plate_top_width, plate_height + 10 + dim_offset_top_x), dxfattribs={"layer": "DIMENSION"})
msp.add_line((0, plate_height + 20 + dim_offset_top_x), (plate_top_width, plate_height + 20 + dim_offset_top_x), dxfattribs={"layer": "DIMENSION"})
msp.add_line((0, plate_height + 20 + dim_offset_top_x), (5, plate_height + 15 + dim_offset_top_x), dxfattribs={"layer": "DIMENSION"})
msp.add_line((0, plate_height + 20 + dim_offset_top_x), (5, plate_height + 25 + dim_offset_top_x), dxfattribs={"layer": "DIMENSION"})
msp.add_line((plate_top_width, plate_height + 20 + dim_offset_top_x), (plate_top_width - 5, plate_height + 15 + dim_offset_top_x), dxfattribs={"layer": "DIMENSION"})
msp.add_line((plate_top_width, plate_height + 20 + dim_offset_top_x), (plate_top_width - 5, plate_height + 25 + dim_offset_top_x), dxfattribs={"layer": "DIMENSION"})
msp.add_mtext(f"{plate_top_width}", dxfattribs={"layer": "ANNOTATION", "char_height": text_height_text}).set_location((plate_top_width / 2, plate_height + 20 + dim_offset_top_x), attachment_point=5)

# Hole dimensions
msp.add_mtext(f"Ø{hole_diameter}", dxfattribs={"layer": "ANNOTATION", "char_height": text_height_text}).set_location((hole1_pos[0] + 15, hole1_pos[1] + 15), attachment_point=7)
msp.add_line((hole1_pos[0], hole1_pos[1]), (hole1_pos[0] + 10, hole1_pos[1] + 10), dxfattribs={"layer": "DIMENSION"}) # Leader line

# Save the DXF document
doc.saveas(out)
print(f"Saved {out}")