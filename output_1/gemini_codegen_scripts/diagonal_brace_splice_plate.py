import sys
import ezdxf
import math

out = sys.argv[1]

doc = ezdxf.new("R2010", setup=True)
doc.units = ezdxf.units.MM
msp = doc.modelspace()

doc.layers.add("GEOMETRY", color=7)
doc.layers.add("DIMENSION", color=3)
doc.layers.add("ANNOTATION", color=1)

def add_mtext_safe(msp_obj, text_string, insert_point, layer="ANNOTATION", char_height=5.58, attachment_point=1):
    mt = msp_obj.add_mtext(text_string, dxfattribs={"layer": layer, "char_height": char_height})
    mt.set_location(insert_point, attachment_point=attachment_point)

def add_horizontal_dimension(msp_obj, p1, p2, offset_y, text, layer="DIMENSION", arrow_size=3.0, text_height=5.58):
    # Extension lines
    msp_obj.add_line((p1[0], p1[1]), (p1[0], p1[1] - offset_y), dxfattribs={"layer": layer})
    msp_obj.add_line((p2[0], p2[1]), (p2[0], p2[1] - offset_y), dxfattribs={"layer": layer})

    # Dimension line
    msp_obj.add_line((p1[0], p1[1] - offset_y), (p2[0], p2[1] - offset_y), dxfattribs={"layer": layer})

    # Arrowheads (simple triangles)
    msp_obj.add_lwpolyline([
        (p1[0], p1[1] - offset_y),
        (p1[0] + arrow_size, p1[1] - offset_y + arrow_size / 2),
        (p1[0] + arrow_size, p1[1] - offset_y - arrow_size / 2),
        (p1[0], p1[1] - offset_y)
    ], dxfattribs={"layer": layer}, close=True)
    msp_obj.add_lwpolyline([
        (p2[0], p2[1] - offset_y),
        (p2[0] - arrow_size, p2[1] - offset_y + arrow_size / 2),
        (p2[0] - arrow_size, p2[1] - offset_y - arrow_size / 2),
        (p2[0], p2[1] - offset_y)
    ], dxfattribs={"layer": layer}, close=True)

    # Dimension text
    text_mid_point = ((p1[0] + p2[0]) / 2, p1[1] - offset_y - text_height/2 - 2)
    add_mtext_safe(msp_obj, text, text_mid_point, layer=layer, char_height=text_height, attachment_point=5) # 5 is MiddleCenter

def add_vertical_dimension(msp_obj, p1, p2, offset_x, text, layer="DIMENSION", arrow_size=3.0, text_height=5.58):
    # Extension lines
    msp_obj.add_line((p1[0], p1[1]), (p1[0] - offset_x, p1[1]), dxfattribs={"layer": layer})
    msp_obj.add_line((p2[0], p2[1]), (p2[0] - offset_x, p2[1]), dxfattribs={"layer": layer})

    # Dimension line
    msp_obj.add_line((p1[0] - offset_x, p1[1]), (p2[0] - offset_x, p2[1]), dxfattribs={"layer": layer})

    # Arrowheads
    msp_obj.add_lwpolyline([
        (p1[0] - offset_x, p1[1]),
        (p1[0] - offset_x + arrow_size / 2, p1[1] - arrow_size),
        (p1[0] - offset_x - arrow_size / 2, p1[1] - arrow_size),
        (p1[0] - offset_x, p1[1])
    ], dxfattribs={"layer": layer}, close=True)
    msp_obj.add_lwpolyline([
        (p2[0] - offset_x, p2[1]),
        (p2[0] - offset_x + arrow_size / 2, p2[1] + arrow_size),
        (p2[0] - offset_x - arrow_size / 2, p2[1] + arrow_size),
        (p2[0] - offset_x, p2[1])
    ], dxfattribs={"layer": layer}, close=True)

    # Dimension text
    text_mid_point = (p1[0] - offset_x - text_height/2 - 2, (p1[1] + p2[1]) / 2)
    add_mtext_safe(msp_obj, text, text_mid_point, layer=layer, char_height=text_height, attachment_point=5) # 5 is MiddleCenter

# --- Diagonal Brace Splice Plate (ESTIMATED) ---
plate_length = 300
plate_width = 120
thickness = 10 # PL10
hole_diameter = 18
hole_radius = hole_diameter / 2

# Outline
points = [
    (0, 0),
    (plate_length, 0),
    (plate_length, plate_width),
    (0, plate_width)
]
msp.add_lwpolyline(points, close=True, dxfattribs={"layer": "GEOMETRY"})

# Hole pattern (2x2 grid for each brace end)
# Left side
hole_grid_x1 = [30, 70]
hole_grid_y = [30, 90] # 30mm from top/bottom edges, 120-30-30 = 60mm pitch
# Right side
hole_grid_x2 = [plate_length - 70, plate_length - 30]

for x in hole_grid_x1:
    for y in hole_grid_y:
        msp.add_circle((x, y), hole_radius, dxfattribs={"layer": "GEOMETRY"})
for x in hole_grid_x2:
    for y in hole_grid_y:
        msp.add_circle((x, y), hole_radius, dxfattribs={"layer": "GEOMETRY"})

# --- Annotations ---
# Part Title
add_mtext_safe(msp, "~DIAGONAL BRACE SPLICE PLATE", (0, plate_width + 50), char_height=7.0, attachment_point=7)
add_mtext_safe(msp, "PL {} - QTY: VARIES (EST.)".format(thickness), (0, plate_width + 40), char_height=5.0)

# Overall Dimensions
add_horizontal_dimension(msp, (0, 0), (plate_length, 0), 30, "~{}".format(plate_length), text_height=5.0)
add_vertical_dimension(msp, (0, plate_width), (0, 0), 30, "~{}".format(plate_width), text_height=5.0)

# Hole notes
add_mtext_safe(msp, "~8x Ø{} HOLES".format(hole_diameter), (plate_length + 10, plate_width / 2), char_height=5.0, attachment_point=4)

# Hole X dimensions
add_horizontal_dimension(msp, (0, 0), (hole_grid_x1[0], 0), 30 + 30, "~{}".format(hole_grid_x1[0]), text_height=5.0)
add_horizontal_dimension(msp, (hole_grid_x1[0], 0), (hole_grid_x1[1], 0), 30 + 30, "~{}".format(hole_grid_x1[1] - hole_grid_x1[0]), text_height=5.0)
add_horizontal_dimension(msp, (hole_grid_x1[1], 0), (hole_grid_x2[0], 0), 30 + 30, "~{}".format(hole_grid_x2[0] - hole_grid_x1[1]), text_height=5.0)
add_horizontal_dimension(msp, (hole_grid_x2[0], 0), (hole_grid_x2[1], 0), 30 + 30, "~{}".format(hole_grid_x2[1] - hole_grid_x2[0]), text_height=5.0)
add_horizontal_dimension(msp, (hole_grid_x2[1], 0), (plate_length, 0), 30 + 30, "~{}".format(plate_length - hole_grid_x2[1]), text_height=5.0)

# Hole Y dimensions
add_vertical_dimension(msp, (0, hole_grid_y[1]), (0, hole_grid_y[0]), 30 + 30, "~{}".format(hole_grid_y[1] - hole_grid_y[0]), text_height=5.0)
add_vertical_dimension(msp, (0, plate_width), (0, hole_grid_y[1]), 30 + 30, "~{}".format(plate_width - hole_grid_y[1]), text_height=5.0)
add_vertical_dimension(msp, (0, hole_grid_y[0]), (0, 0), 30 + 30, "~{}".format(hole_grid_y[0]), text_height=5.0)

doc.saveas(out)
print(f'Saved {out}')