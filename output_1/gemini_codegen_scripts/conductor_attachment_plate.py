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

# --- Conductor Attachment Plate (ESTIMATED) ---
base_length = 200
base_width = 150
tab_length = 80
tab_width = 80 # Width of the tab section
thickness = 12 # PL12
mounting_hole_diameter = 22
mounting_hole_radius = mounting_hole_diameter / 2
conductor_hole_diameter = 30
conductor_hole_radius = conductor_hole_diameter / 2
secondary_hole_diameter = 18
secondary_hole_radius = secondary_hole_diameter / 2


# Outline points for a rectangular base with a central tab
points = [
    (0, 0),
    (base_length, 0),
    (base_length, (base_width - tab_width) / 2),
    (base_length + tab_length, (base_width - tab_width) / 2),
    (base_length + tab_length, (base_width + tab_width) / 2),
    (base_length, (base_width + tab_width) / 2),
    (base_length, base_width),
    (0, base_width)
]
msp.add_lwpolyline(points, close=True, dxfattribs={"layer": "GEOMETRY"})

# Mounting holes to cross-arm (4 holes on the base plate)
mount_holes = [
    (30, 30),
    (30, base_width - 30),
    (base_length - 30, 30),
    (base_length - 30, base_width - 30)
]
for h_x, h_y in mount_holes:
    msp.add_circle((h_x, h_y), mounting_hole_radius, dxfattribs={"layer": "GEOMETRY"})

# Conductor attachment hole (main large hole on the tab)
conductor_hole_pos = (base_length + tab_length / 2, base_width / 2)
msp.add_circle(conductor_hole_pos, conductor_hole_radius, dxfattribs={"layer": "GEOMETRY"})

# Secondary holes on the tab (e.g., for safety wire or secondary attachment)
secondary_holes = [
    (conductor_hole_pos[0], conductor_hole_pos[1] - 25),
    (conductor_hole_pos[0], conductor_hole_pos[1] + 25)
]
for h_x, h_y in secondary_holes:
    msp.add_circle((h_x, h_y), secondary_hole_radius, dxfattribs={"layer": "GEOMETRY"})


# --- Annotations ---
# Part Title
add_mtext_safe(msp, "~CONDUCTOR ATTACHMENT PLATE", (0, base_width + 50), char_height=7.0, attachment_point=7)
add_mtext_safe(msp, "PL {} - QTY: VARIES (EST.)".format(thickness), (0, base_width + 40), char_height=5.0)

# Overall Dimensions
overall_length = base_length + tab_length
add_horizontal_dimension(msp, (0, 0), (base_length + tab_length, 0), 30, "~{}".format(overall_length), text_height=5.0)
add_vertical_dimension(msp, (0, base_width), (0, 0), 30, "~{}".format(base_width), text_height=5.0)

# Base length and tab length dimensions
add_horizontal_dimension(msp, (0, 0), (base_length, 0), 30 + 30, "~{}".format(base_length), text_height=5.0)
add_horizontal_dimension(msp, (base_length, 0), (base_length + tab_length, 0), 30 + 30, "~{}".format(tab_length), text_height=5.0)

# Tab width dimension
add_vertical_dimension(msp, (base_length + tab_length, (base_width + tab_width) / 2), (base_length + tab_length, (base_width - tab_width) / 2), 30 + 30, "~{}".format(tab_width), text_height=5.0)


# Hole notes
add_mtext_safe(msp, "~4x Ø{} HOLES".format(mounting_hole_diameter), (-50, mount_holes[0][1]), char_height=5.0, attachment_point=4)
add_mtext_safe(msp, "~1x Ø{} HOLE (Conductor)".format(conductor_hole_diameter), (conductor_hole_pos[0] + 50, conductor_hole_pos[1]), char_height=5.0, attachment_point=6) # 6 is MiddleLeft
add_mtext_safe(msp, "~2x Ø{} HOLES (Secondary)".format(secondary_hole_diameter), (conductor_hole_pos[0] + 50, secondary_holes[0][1] - 10), char_height=5.0, attachment_point=6)

# Example hole dimensions for mounting holes
add_horizontal_dimension(msp, (0,0), (mount_holes[0][0],0), -20, "~{}".format(mount_holes[0][0]), text_height=5.0) # below the part
add_vertical_dimension(msp, (0,0), (0,mount_holes[0][1]), -20, "~{}".format(mount_holes[0][1]), text_height=5.0) # left of the part
add_horizontal_dimension(msp, (mount_holes[0][0],0), (mount_holes[2][0],0), -20, "~{}".format(mount_holes[2][0]-mount_holes[0][0]), text_height=5.0)
add_vertical_dimension(msp, (0,mount_holes[0][1]), (0,mount_holes[1][1]), -20, "~{}".format(mount_holes[1][1]-mount_holes[0][1]), text_height=5.0)

doc.saveas(out)
print(f'Saved {out}')