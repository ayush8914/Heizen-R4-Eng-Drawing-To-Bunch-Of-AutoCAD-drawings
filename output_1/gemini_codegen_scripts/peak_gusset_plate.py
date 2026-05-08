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

# --- Peak Gusset Plate (ESTIMATED) ---
plate_width = 400
plate_height = 400
thickness = 12 # PL12
hole_diameter = 22
hole_radius = hole_diameter / 2

# Outline points (custom hexagonal-like shape for a robust connection)
points = [
    (0, 100),
    (100, 0),
    (plate_width - 100, 0),
    (plate_width, 100),
    (plate_width, plate_height - 100),
    (plate_width / 2, plate_height),
    (0, plate_height - 100)
]
msp.add_lwpolyline(points, close=True, dxfattribs={"layer": "GEOMETRY"})

# Hole positions (EST)
holes = [
    (50, 50),
    (plate_width - 50, 50),
    (plate_width - 50, plate_height - 150),
    (plate_width / 2, plate_height - 50),
    (50, plate_height - 150),
    (plate_width/2, plate_height/2) # Central hole for a vertical member
]

for h_x, h_y in holes:
    msp.add_circle((h_x, h_y), hole_radius, dxfattribs={"layer": "GEOMETRY"})

# --- Annotations ---
# Part Title
add_mtext_safe(msp, "~PEAK GUSSET PLATE", (0, plate_height + 50), char_height=7.0, attachment_point=7) # 7 is MiddleLeft
add_mtext_safe(msp, "PL {} - QTY: 1 (EST.)".format(thickness), (0, plate_height + 40), char_height=5.0)

# Overall Dimensions
add_horizontal_dimension(msp, (points[0][0], points[0][1]), (points[3][0], points[3][1]), 30, "~{} (W)".format(plate_width), text_height=5.0)
add_vertical_dimension(msp, (points[5][0], points[5][1]), (points[1][0], points[1][1]), 30, "~{} (H)".format(plate_height), text_height=5.0)

# Hole notes
add_mtext_safe(msp, "~6x Ø{} HOLES".format(hole_diameter), (plate_width + 10, 50), char_height=5.0, attachment_point=4) # 4 is MiddleRight

# Hole X dimensions (example for some critical holes)
add_horizontal_dimension(msp, (holes[0][0], holes[0][1]), (holes[1][0], holes[1][1]), 30 + 30, "~{}".format(plate_width - 100), text_height=5.0)
add_horizontal_dimension(msp, (0,0), (holes[0][0], holes[0][1]), 30 + 30 + 20, "~{}".format(holes[0][0]), text_height=5.0)
add_horizontal_dimension(msp, (holes[1][0], holes[1][1]), (plate_width,0), 30 + 30 + 20, "~{}".format(plate_width - holes[1][0]), text_height=5.0)

# Hole Y dimensions
add_vertical_dimension(msp, (holes[4][0], holes[4][1]), (holes[0][0], holes[0][1]), 30 + 30, "~{}".format(holes[4][1] - holes[0][1]), text_height=5.0)
add_vertical_dimension(msp, (points[5][0], points[5][1]), (holes[3][0], holes[3][1]), 30 + 30 + 20, "~{}".format(plate_height - holes[3][1]), text_height=5.0)

doc.saveas(out)
print(f'Saved {out}')