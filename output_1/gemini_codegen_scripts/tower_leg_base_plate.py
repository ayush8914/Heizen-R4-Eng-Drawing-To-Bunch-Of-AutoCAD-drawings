import sys
import ezdxf
import math

def add_linear_dimension(msp, p1, p2, offset, text, layer="DIMENSION", text_layer="ANNOTATION", char_height=5):
    # Extension lines
    msp.add_line((p1[0], p1[1]), (p1[0], p1[1] + offset), dxfattribs={'layer': layer})
    msp.add_line((p2[0], p2[1]), (p2[0], p2[1] + offset), dxfattribs={'layer': layer})

    # Dimension line
    msp.add_line((p1[0], p1[1] + offset), (p2[0], p2[1] + offset), dxfattribs={'layer': layer})

    # Arrowheads (simple triangles)
    arrow_size = 2.5 # Adjust as needed for visual scale
    
    # Left arrow
    arrow_p1_left = (p1[0], p1[1] + offset)
    arrow_p2_left = (p1[0] + arrow_size, p1[1] + offset - arrow_size)
    arrow_p3_left = (p1[0] + arrow_size, p1[1] + offset + arrow_size)
    msp.add_lwpolyline([arrow_p1_left, arrow_p2_left, arrow_p3_left, arrow_p1_left], close=True, dxfattribs={'layer': layer})
    
    # Right arrow
    arrow_p1_right = (p2[0], p2[1] + offset)
    arrow_p2_right = (p2[0] - arrow_size, p2[1] + offset - arrow_size)
    arrow_p3_right = (p2[0] - arrow_size, p2[1] + offset + arrow_size)
    msp.add_lwpolyline([arrow_p1_right, arrow_p2_right, arrow_p3_right, arrow_p1_right], close=True, dxfattribs={'layer': layer})

    # Dimension text
    text_mid_x = (p1[0] + p2[0]) / 2
    text_y = p1[1] + offset + char_height / 2 + 1 # small offset to clear line
    mt = msp.add_mtext(text, dxfattribs={'layer': text_layer, 'char_height': char_height})
    mt.set_location((text_mid_x, text_y), attachment_point=5) # Middle center

def add_vertical_dimension(msp, p1, p2, offset, text, layer="DIMENSION", text_layer="ANNOTATION", char_height=5):
    # Extension lines
    msp.add_line((p1[0], p1[1]), (p1[0] + offset, p1[1]), dxfattribs={'layer': layer})
    msp.add_line((p2[0], p2[1]), (p2[0] + offset, p2[1]), dxfattribs={'layer': layer})

    # Dimension line
    msp.add_line((p1[0] + offset, p1[1]), (p2[0] + offset, p2[1]), dxfattribs={'layer': layer})

    # Arrowheads (simple triangles)
    arrow_size = 2.5 # Adjust as needed for visual scale

    # Bottom arrow
    arrow_p1_bottom = (p1[0] + offset, p1[1])
    arrow_p2_bottom = (p1[0] + offset - arrow_size, p1[1] + arrow_size)
    arrow_p3_bottom = (p1[0] + offset + arrow_size, p1[1] + arrow_size)
    msp.add_lwpolyline([arrow_p1_bottom, arrow_p2_bottom, arrow_p3_bottom, arrow_p1_bottom], close=True, dxfattribs={'layer': layer})

    # Top arrow
    arrow_p1_top = (p2[0] + offset, p2[1])
    arrow_p2_top = (p2[0] + offset - arrow_size, p2[1] - arrow_size)
    arrow_p3_top = (p2[0] + offset + arrow_size, p2[1] - arrow_size)
    msp.add_lwpolyline([arrow_p1_top, arrow_p2_top, arrow_p3_top, arrow_p1_top], close=True, dxfattribs={'layer': layer})

    # Dimension text
    text_mid_y = (p1[1] + p2[1]) / 2
    text_x = p1[0] + offset + char_height / 2 + 1 # small offset to clear line
    mt = msp.add_mtext(text, dxfattribs={'layer': text_layer, 'char_height': char_height})
    mt.set_location((text_x, text_mid_y), attachment_point=5) # Middle center

def create_tower_leg_base_plate_dxf(output_filename):
    doc = ezdxf.new("R2010", setup=True)
    doc.units = ezdxf.units.MM
    msp = doc.modelspace()

    # Define Layers
    doc.layers.add("GEOMETRY", color=7)  # White/Black
    doc.layers.add("DIMENSION", color=3) # Green
    doc.layers.add("ANNOTATION", color=1) # Red

    # --- GEOMETRY ---
    
    base_plate_width = 500
    base_plate_height = 500
    base_plate_thickness = 25 # mm, EST
    hole_diameter = 30 # mm, EST
    hole_radius = hole_diameter / 2
    hole_offset = 75 # mm, EST

    
    # Main plate outline
    points = [(0, 0), (base_plate_width, 0), (base_plate_width, base_plate_height), (0, base_plate_height)]
    msp.add_lwpolyline(points, close=True, dxfattribs={'layer': 'GEOMETRY'})

    # Bolt holes
    hole_positions = [
        (hole_offset, hole_offset),
        (base_plate_width - hole_offset, hole_offset),
        (base_plate_width - hole_offset, base_plate_height - hole_offset),
        (hole_offset, base_plate_height - hole_offset),
    ]
    for hp in hole_positions:
        msp.add_circle(hp, hole_radius, dxfattribs={'layer': 'GEOMETRY'})

    # --- DIMENSIONS ---
    
    # Overall dimensions
    add_linear_dimension(msp, (0, 0), (base_plate_width, 0), -50, f'{base_plate_width}', text_layer='ANNOTATION', char_height=5)
    add_vertical_dimension(msp, (base_plate_width, 0), (base_plate_width, base_plate_height), 50, f'{base_plate_height}', text_layer='ANNOTATION', char_height=5)

    # Hole dimensioning from datum (0,0)
    # X-coordinates for holes
    add_linear_dimension(msp, (0, hole_offset), (hole_offset, hole_offset), -25, f'{hole_offset}', text_layer='ANNOTATION', char_height=5)
    add_linear_dimension(msp, (hole_offset, hole_offset), (base_plate_width - hole_offset, hole_offset), -25, f'{base_plate_width - 2*hole_offset}', text_layer='ANNOTATION', char_height=5)
    add_linear_dimension(msp, (base_plate_width - hole_offset, hole_offset), (base_plate_width, hole_offset), -25, f'{hole_offset}', text_layer='ANNOTATION', char_height=5)

    # Y-coordinates for holes
    add_vertical_dimension(msp, (hole_offset, 0), (hole_offset, hole_offset), 25, f'{hole_offset}', text_layer='ANNOTATION', char_height=5)
    add_vertical_dimension(msp, (hole_offset, hole_offset), (hole_offset, base_plate_height - hole_offset), 25, f'{base_plate_height - 2*hole_offset}', text_layer='ANNOTATION', char_height=5)
    add_vertical_dimension(msp, (hole_offset, base_plate_height - hole_offset), (hole_offset, base_plate_height), 25, f'{hole_offset}', text_layer='ANNOTATION', char_height=5)

    # Hole size annotation
    mt = msp.add_mtext(f'4x Ø{hole_diameter} THRU', dxfattribs={'layer': 'ANNOTATION', 'char_height': 5})
    mt.set_location((base_plate_width/2, base_plate_height/2 + 70), attachment_point=5)

    # --- ANNOTATIONS ---
    
    mt = msp.add_mtext("Part ID: tower_leg_base_plate", dxfattribs={'layer': 'ANNOTATION', 'char_height': 7})
    mt.set_location((base_plate_width/2, base_plate_height + 100), attachment_point=5)

    mt = msp.add_mtext(f"Material: PL{base_plate_thickness} (EST)", dxfattribs={'layer': 'ANNOTATION', 'char_height': 5})
    mt.set_location((base_plate_width/2, base_plate_height + 80), attachment_point=5)

    mt = msp.add_mtext("QTY: 1", dxfattribs={'layer': 'ANNOTATION', 'char_height': 5})
    mt.set_location((base_plate_width/2, base_plate_height + 60), attachment_point=5)

    mt = msp.add_mtext(f"Overall: {base_plate_width}x{base_plate_height}mm", dxfattribs={'layer': 'ANNOTATION', 'char_height': 5})
    mt.set_location((base_plate_width/2, base_plate_height + 40), attachment_point=5)

    doc.saveas(output_filename)
    print(f'Saved {output_filename}')

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script.py <output_filename.dxf>")
        sys.exit(1)
    output_filename = sys.argv[1]
    create_tower_leg_base_plate_dxf(output_filename)
