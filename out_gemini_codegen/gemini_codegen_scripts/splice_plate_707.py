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
# Part 707: Splice Plate
# Based on 'Steigbügel für geschweißte Doppelbleche nach 'G75' M35' detail and 'Schnitt A-A'
# Overall Dimensions: 477mm L x 399mm W
# Thickness: 20mm (inferred from 'BLE 20...' and 'Schnitt A-A')
# Material: S235JR
# QTY: Multiple (implied)

plate_thickness = 20
plate_length = 477
plate_width = 399
outer_corner_radius = 12
inner_cutout_width = 125
inner_cutout_height = 100
hole_diameter = 38 # M35 bolts -> Ø38 holes
inner_cutout_corner_radius = 10 # R10 on inner corners

# Bulge value for a 90-degree counter-clockwise arc (tan(45/2) = tan(22.5) = 0.41421356)
BULGE_CCW_90 = 0.41421356

# Outer profile with rounded corners using LWPOLYLINE with bulge
# Datum (0,0) at bottom-left corner of the bounding box.

outer_boundary_points = []

# Start point for LWPOLYLINE: (outer_corner_radius, 0) (bottom edge after first corner arc)
outer_boundary_points.append((outer_corner_radius, 0))
# Arc to (0, outer_corner_radius) for bottom-left corner
outer_boundary_points.append((0, outer_corner_radius, BULGE_CCW_90))

# Line up to (0, plate_width - outer_corner_radius)
outer_boundary_points.append((0, plate_width - outer_corner_radius))
# Arc to (outer_corner_radius, plate_width) for top-left corner
outer_boundary_points.append((outer_corner_radius, plate_width, BULGE_CCW_90))

# Line right to (plate_length - outer_corner_radius, plate_width)
outer_boundary_points.append((plate_length - outer_corner_radius, plate_width))
# Arc to (plate_length, plate_width - outer_corner_radius) for top-right corner
outer_boundary_points.append((plate_length, plate_width - outer_corner_radius, BULGE_CCW_90))

# Line down to (plate_length, outer_corner_radius)
outer_boundary_points.append((plate_length, outer_corner_radius))
# Arc to (plate_length - outer_corner_radius, 0) for bottom-right corner
outer_boundary_points.append((plate_length - outer_corner_radius, 0, BULGE_CCW_90))

msp.add_lwpolyline(outer_boundary_points, close=True, dxfattribs={"layer": "GEOMETRY"})


# Central cutout (rectangular with rounded corners)
center_x = plate_length / 2
center_y = plate_width / 2

cutout_half_width = inner_cutout_width / 2
cutout_half_height = inner_cutout_height / 2

# Coordinates for the rectangle that defines the central cutout (before fillets)
cutout_bl = (center_x - cutout_half_width, center_y - cutout_half_height) # Bottom-left
cutout_br = (center_x + cutout_half_width, center_y - cutout_half_height) # Bottom-right
cutout_tr = (center_x + cutout_half_width, center_y + cutout_half_height) # Top-right
cutout_tl = (center_x - cutout_half_width, center_y + cutout_half_height) # Top-left

# LWPOLYLINE points for inner cutout (counter-clockwise)
inner_cutout_points = []

# Start point: (cutout_bl[0] + inner_cutout_corner_radius, cutout_bl[1])
inner_cutout_points.append((cutout_bl[0] + inner_cutout_corner_radius, cutout_bl[1]))
# Arc to (cutout_bl[0], cutout_bl[1] + inner_cutout_corner_radius) for bottom-left inner corner
inner_cutout_points.append((cutout_bl[0], cutout_bl[1] + inner_cutout_corner_radius, BULGE_CCW_90))

# Line up to (cutout_tl[0], cutout_tl[1] - inner_cutout_corner_radius)
inner_cutout_points.append((cutout_tl[0], cutout_tl[1] - inner_cutout_corner_radius))
# Arc to (cutout_tl[0] + inner_cutout_corner_radius, cutout_tl[1]) for top-left inner corner
inner_cutout_points.append((cutout_tl[0] + inner_cutout_corner_radius, cutout_tl[1], BULGE_CCW_90))

# Line right to (cutout_tr[0] - inner_cutout_corner_radius, cutout_tr[1])
inner_cutout_points.append((cutout_tr[0] - inner_cutout_corner_radius, cutout_tr[1]))
# Arc to (cutout_tr[0], cutout_tr[1] - inner_cutout_corner_radius) for top-right inner corner
inner_cutout_points.append((cutout_tr[0], cutout_tr[1] - inner_cutout_corner_radius, BULGE_CCW_90))

# Line down to (cutout_br[0], cutout_br[1] + inner_cutout_corner_radius)
inner_cutout_points.append((cutout_br[0], cutout_br[1] + inner_cutout_corner_radius))
# Arc to (cutout_br[0] - inner_cutout_corner_radius, cutout_br[1]) for bottom-right inner corner
inner_cutout_points.append((cutout_br[0] - inner_cutout_corner_radius, cutout_br[1], BULGE_CCW_90))

msp.add_lwpolyline(inner_cutout_points, close=True, dxfattribs={"layer": "GEOMETRY"})


# Bolt holes (4x Ø38)
hole_radius = hole_diameter / 2
hole_spacing_x = 125 # From drawing
hole_spacing_y = 125 # From drawing

# Calculate hole centers relative to plate center
hole_x_offset = hole_spacing_x / 2
hole_y_offset = hole_spacing_y / 2

hole_positions = [
    (center_x - hole_x_offset, center_y - hole_y_offset),
    (center_x + hole_x_offset, center_y - hole_y_offset),
    (center_x - hole_x_offset, center_y + hole_y_offset),
    (center_x + hole_x_offset, center_y + hole_y_offset)
]

for pos in hole_positions:
    msp.add_circle(pos, hole_radius, dxfattribs={"layer": "HOLES"})

# --- Annotations Definition ---
# Part Title
msp.add_mtext("PART: splice_plate_707", dxfattribs={"layer": "ANNOTATION", "char_height": text_height_mtext}).set_location((plate_length / 2, -50), attachment_point=5)
msp.add_mtext("DESCRIPTION: Splice Plate for 4-member intersection", dxfattribs={"layer": "ANNOTATION", "char_height": text_height_mtext}).set_location((plate_length / 2, -60), attachment_point=5)
msp.add_mtext(f"MATERIAL: S235JR", dxfattribs={"layer": "ANNOTATION", "char_height": text_height_mtext}).set_location((plate_length / 2, -70), attachment_point=5)
msp.add_mtext(f"THICKNESS: {plate_thickness} mm", dxfattribs={"layer": "ANNOTATION", "char_height": text_height_mtext}).set_location((plate_length / 2, -80), attachment_point=5)
msp.add_mtext("QTY: 1 (as distinct fabrication item)", dxfattribs={"layer": "ANNOTATION", "char_height": text_height_mtext}).set_location((plate_length / 2, -90), attachment_point=5)
msp.add_mtext(f"HOLES: 4x Ø{hole_diameter} (for M35 bolts)", dxfattribs={"layer": "ANNOTATION", "char_height": text_height_mtext}).set_location((plate_length / 2, -100), attachment_point=5)

# Overall dimensions
# Length dimension
dim_offset_x = 30
msp.add_line((0, 0 - dim_offset_x), (0, -10 - dim_offset_x), dxfattribs={"layer": "DIMENSION"})
msp.add_line((plate_length, 0 - dim_offset_x), (plate_length, -10 - dim_offset_x), dxfattribs={"layer": "DIMENSION"})
msp.add_line((0, -20 - dim_offset_x), (plate_length, -20 - dim_offset_x), dxfattribs={"layer": "DIMENSION"})
msp.add_line((0, -20 - dim_offset_x), (5, -15 - dim_offset_x), dxfattribs={"layer": "DIMENSION"})
msp.add_line((0, -20 - dim_offset_x), (5, -25 - dim_offset_x), dxfattribs={"layer": "DIMENSION"})
msp.add_line((plate_length, -20 - dim_offset_x), (plate_length - 5, -15 - dim_offset_x), dxfattribs={"layer": "DIMENSION"})
msp.add_line((plate_length, -20 - dim_offset_x), (plate_length - 5, -25 - dim_offset_x), dxfattribs={"layer": "DIMENSION"})
msp.add_mtext(f"{plate_length}", dxfattribs={"layer": "ANNOTATION", "char_height": text_height_text}).set_location((plate_length / 2, -20 - dim_offset_x), attachment_point=5)

# Width dimension
dim_offset_y = 30
msp.add_line((-dim_offset_y, 0), (-10 - dim_offset_y, 0), dxfattribs={"layer": "DIMENSION"})
msp.add_line((-dim_offset_y, plate_width), (-10 - dim_offset_y, plate_width), dxfattribs={"layer": "DIMENSION"})
msp.add_line((-20 - dim_offset_y, 0), (-20 - dim_offset_y, plate_width), dxfattribs={"layer": "DIMENSION"})
msp.add_line((-20 - dim_offset_y, 0), (-15 - dim_offset_y, 5), dxfattribs={"layer": "DIMENSION"})
msp.add_line((-20 - dim_offset_y, 0), (-25 - dim_offset_y, 5), dxfattribs={"layer": "DIMENSION"})
msp.add_line((-20 - dim_offset_y, plate_width), (-15 - dim_offset_y, plate_width - 5), dxfattribs={"layer": "DIMENSION"})
msp.add_line((-20 - dim_offset_y, plate_width), (-25 - dim_offset_y, plate_width - 5), dxfattribs={"layer": "DIMENSION"})
msp.add_mtext(f"{plate_width}", dxfattribs={"layer": "ANNOTATION", "char_height": text_height_text}).set_location((-20 - dim_offset_y, plate_width / 2), attachment_point=5)

# Central cutout dimensions
# Width dimension for central cutout
cutout_center_x = plate_length / 2
cutout_center_y = plate_width / 2
cutout_start_x = cutout_center_x - inner_cutout_width / 2
cutout_end_x = cutout_center_x + inner_cutout_width / 2
cutout_start_y = cutout_center_y - inner_cutout_height / 2
cutout_end_y = cutout_center_y + inner_cutout_height / 2

dim_offset_cutout_y = cutout_start_y - 20
msp.add_line((cutout_start_x, cutout_start_y), (cutout_start_x, dim_offset_cutout_y + 10), dxfattribs={"layer": "DIMENSION"})
msp.add_line((cutout_end_x, cutout_start_y), (cutout_end_x, dim_offset_cutout_y + 10), dxfattribs={"layer": "DIMENSION"})
msp.add_line((cutout_start_x, dim_offset_cutout_y), (cutout_end_x, dim_offset_cutout_y), dxfattribs={"layer": "DIMENSION"})
msp.add_line((cutout_start_x, dim_offset_cutout_y), (cutout_start_x + 5, dim_offset_cutout_y - 5), dxfattribs={"layer": "DIMENSION"})
msp.add_line((cutout_start_x, dim_offset_cutout_y), (cutout_start_x + 5, dim_offset_cutout_y + 5), dxfattribs={"layer": "DIMENSION"})
msp.add_line((cutout_end_x, dim_offset_cutout_y), (cutout_end_x - 5, dim_offset_cutout_y - 5), dxfattribs={"layer": "DIMENSION"})
msp.add_line((cutout_end_x, dim_offset_cutout_y), (cutout_end_x - 5, dim_offset_cutout_y + 5), dxfattribs={"layer": "DIMENSION"})
msp.add_mtext(f"{inner_cutout_width}", dxfattribs={"layer": "ANNOTATION", "char_height": text_height_text}).set_location((cutout_center_x, dim_offset_cutout_y - 10), attachment_point=5)

# Height dimension for central cutout
dim_offset_cutout_x = cutout_start_x - 20
msp.add_line((cutout_start_x, cutout_start_y), (dim_offset_cutout_x + 10, cutout_start_y), dxfattribs={"layer": "DIMENSION"})
msp.add_line((cutout_start_x, cutout_end_y), (dim_offset_cutout_x + 10, cutout_end_y), dxfattribs={"layer": "DIMENSION"})
msp.add_line((dim_offset_cutout_x, cutout_start_y), (dim_offset_cutout_x, cutout_end_y), dxfattribs={"layer": "DIMENSION"})
msp.add_line((dim_offset_cutout_x, cutout_start_y), (dim_offset_cutout_x - 5, cutout_start_y + 5), dxfattribs={"layer": "DIMENSION"})
msp.add_line((dim_offset_cutout_x, cutout_start_y), (dim_offset_cutout_x + 5, cutout_start_y + 5), dxfattribs={"layer": "DIMENSION"})
msp.add_line((dim_offset_cutout_x, cutout_end_y), (dim_offset_cutout_x - 5, cutout_end_y - 5), dxfattribs={"layer": "DIMENSION"})
msp.add_line((dim_offset_cutout_x, cutout_end_y), (dim_offset_cutout_x + 5, cutout_end_y - 5), dxfattribs={"layer": "DIMENSION"})
msp.add_mtext(f"{inner_cutout_height}", dxfattribs={"layer": "ANNOTATION", "char_height": text_height_text}).set_location((dim_offset_cutout_x - 10, cutout_center_y), attachment_point=5)

# Hole pattern dimensioning (show spacing)
msp.add_line((hole_positions[0][0], hole_positions[0][1]), (hole_positions[0][0], hole_positions[0][1] - 30), dxfattribs={"layer": "DIMENSION"})
msp.add_line((hole_positions[2][0], hole_positions[2][1]), (hole_positions[2][0], hole_positions[2][1] - 30), dxfattribs={"layer": "DIMENSION"})
msp.add_line((hole_positions[0][0], hole_positions[0][1] - 40), (hole_positions[2][0], hole_positions[2][1] - 40), dxfattribs={"layer": "DIMENSION"})
msp.add_mtext(f"{hole_spacing_y}", dxfattribs={"layer": "ANNOTATION", "char_height": text_height_text}).set_location((hole_positions[0][0], hole_positions[0][1] - 50), attachment_point=5)
# Add arrowheads for hole spacing dimension (vertical)
msp.add_line((hole_positions[0][0], hole_positions[0][1] - 40), (hole_positions[0][0] - 5, hole_positions[0][1] - 35), dxfattribs={"layer": "DIMENSION"})
msp.add_line((hole_positions[0][0], hole_positions[0][1] - 40), (hole_positions[0][0] + 5, hole_positions[0][1] - 35), dxfattribs={"layer": "DIMENSION"})
msp.add_line((hole_positions[2][0], hole_positions[2][1] - 40), (hole_positions[2][0] - 5, hole_positions[2][1] - 45), dxfattribs={"layer": "DIMENSION"})
msp.add_line((hole_positions[2][0], hole_positions[2][1] - 40), (hole_positions[2][0] + 5, hole_positions[2][1] - 45), dxfattribs={"layer": "DIMENSION"})


msp.add_line((hole_positions[0][0], hole_positions[0][1]), (hole_positions[0][0] - 30, hole_positions[0][1]), dxfattribs={"layer": "DIMENSION"})
msp.add_line((hole_positions[1][0], hole_positions[1][1]), (hole_positions[1][0] - 30, hole_positions[1][1]), dxfattribs={"layer": "DIMENSION"})
msp.add_line((hole_positions[0][0] - 40, hole_positions[0][1]), (hole_positions[1][0] - 40, hole_positions[1][1]), dxfattribs={"layer": "DIMENSION"})
msp.add_mtext(f"{hole_spacing_x}", dxfattribs={"layer": "ANNOTATION", "char_height": text_height_text}).set_location((hole_positions[0][0] - 50, hole_positions[0][1]), attachment_point=5)
# Add arrowheads for hole spacing dimension (horizontal)
msp.add_line((hole_positions[0][0] - 40, hole_positions[0][1]), (hole_positions[0][0] - 35, hole_positions[0][1] - 5), dxfattribs={"layer": "DIMENSION"})
msp.add_line((hole_positions[0][0] - 40, hole_positions[0][1]), (hole_positions[0][0] - 35, hole_positions[0][1] + 5), dxfattribs={"layer": "DIMENSION"})
msp.add_line((hole_positions[1][0] - 40, hole_positions[1][1]), (hole_positions[1][0] - 45, hole_positions[1][1] - 5), dxfattribs={"layer": "DIMENSION"})
msp.add_line((hole_positions[1][0] - 40, hole_positions[1][1]), (hole_positions[1][0] - 45, hole_positions[1][1] + 5), dxfattribs={"layer": "DIMENSION"})


# Annotate one hole diameter
msp.add_mtext(f"Ø{hole_diameter}", dxfattribs={"layer": "ANNOTATION", "char_height": text_height_text}).set_location((hole_positions[0][0] + 15, hole_positions[0][1] + 15), attachment_point=7)
msp.add_line((hole_positions[0][0], hole_positions[0][1]), (hole_positions[0][0] + 10, hole_positions[0][1] + 10), dxfattribs={"layer": "DIMENSION"}) # Leader line

# Outer corner radius
msp.add_mtext(f"R{outer_corner_radius}", dxfattribs={"layer": "ANNOTATION", "char_height": text_height_text}).set_location((outer_corner_radius + 15, outer_corner_radius + 15), attachment_point=7)
msp.add_line((outer_corner_radius, 0), (outer_corner_radius + 10, 10), dxfattribs={"layer": "DIMENSION"}) # Leader line

# Inner corner radius (central cutout)
msp.add_mtext(f"R{inner_cutout_corner_radius}", dxfattribs={"layer": "ANNOTATION", "char_height": text_height_text}).set_location((cutout_bl[0] + inner_cutout_corner_radius + 15, cutout_bl[1] + inner_cutout_corner_radius + 15), attachment_point=7)
msp.add_line((cutout_bl[0] + inner_cutout_corner_radius, cutout_bl[1]), (cutout_bl[0] + inner_cutout_corner_radius + 10, cutout_bl[1] + 10), dxfattribs={"layer": "DIMENSION"}) # Leader line

# Save the DXF document
doc.saveas(out)
print(f"Saved {out}")