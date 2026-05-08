import ezdxf
import sys
import math

def draw_arrowhead(msp, p1, p2, size, layer="DIMENSION"):
    angle = math.atan2(p2[1] - p1[1], p2[0] - p1[0])
    a1 = angle + math.radians(150)
    a2 = angle - math.radians(150)
    msp.add_line(p1, (p1[0] + size * math.cos(a1), p1[1] + size * math.sin(a1)), dxfattribs={"layer": layer})
    msp.add_line(p1, (p1[0] + size * math.cos(a2), p1[1] + size * math.sin(a2)), dxfattribs={"layer": layer})

def create_dxf():
    doc = ezdxf.new('R2010', setup=True)
    doc.units = ezdxf.units.MM
    msp = doc.modelspace()

    # Define layers
    doc.layers.add("GEOMETRY", color=1) # Red
    doc.layers.add("DIMENSION", color=3) # Green
    doc.layers.add("ANNOTATION", color=2) # Yellow

    # Part parameters (Derived from 'L 250x28 - 721' and 900mm segment on main elevation)
    part_id = "721"
    description = "tower_leg_splice_plate_lower"
    length = 900  # From 900mm dimension on main elevation
    width = 250   # From 'L 250x28' and 'Schnitt A-A' view
    thickness = 28 # From 'L 250x28'
    material = "S355JR" # Assumed standard structural steel
    qty = 4       # Assumed for 4 tower legs
    hole_diameter = 30 # For M27 bolts (27mm + 3mm clearance)

    # GEOMETRY layer
    # Plate outline, bottom-left at (0,0)
    points = [(0,0), (width,0), (width,length), (0,length)]
    msp.add_lwpolyline(points, close=True, dxfattribs={"layer": "GEOMETRY"})

    # Hole pattern (4 columns, 6 rows)
    # Horizontal spacing based on typical gauge/edge distances for 250mm plate with 4 bolt lines
    x_coords = [50, 100, 150, 200] # (Edge 50, Gauge 50, Gauge 50, Edge 50)
    # Vertical spacing based on 6 bolts in 900mm length, assuming 75mm top/bottom edge distance
    y_coords = [75 + i * 150 for i in range(6)] # (900 - 2*75) / 5 spacings = 150mm pitch

    for x in x_coords:
        for y in y_coords:
            msp.add_circle((x, y), hole_diameter / 2, dxfattribs={"layer": "GEOMETRY"})

    # ANNOTATION layer
    # Part information
    msp.add_mtext(f"PART NO: {part_id}", dxfattribs={"layer": "ANNOTATION", "char_height": 5.0}).set_location((width + 50, length - 20), attachment_point=1)
    msp.add_mtext(f"DESCRIPTION: {description}", dxfattribs={"layer": "ANNOTATION", "char_height": 5.0}).set_location((width + 50, length - 40), attachment_point=1)
    msp.add_mtext(f"PLATE: {width}x{length}x{thickness} mm", dxfattribs={"layer": "ANNOTATION", "char_height": 5.0}).set_location((width + 50, length - 60), attachment_point=1)
    msp.add_mtext(f"MATERIAL: {material}", dxfattribs={"layer": "ANNOTATION", "char_height": 5.0}).set_location((width + 50, length - 80), attachment_point=1)
    msp.add_mtext(f"QTY: {qty}", dxfattribs={"layer": "ANNOTATION", "char_height": 5.0}).set_location((width + 50, length - 100), attachment_point=1)
    msp.add_mtext(f"HOLES: 4x6 = 24x Ø{hole_diameter} mm", dxfattribs={"layer": "ANNOTATION", "char_height": 5.0}).set_location((width + 50, length - 120), attachment_point=1)

    # DIMENSION layer (manual dimensions for clarity)
    dim_text_height = 3.5
    arrow_size = 5

    # Overall width dimension
    msp.add_line((0, -20), (0, -10), dxfattribs={"layer": "DIMENSION"})
    msp.add_line((width, -20), (width, -10), dxfattribs={"layer": "DIMENSION"})
    msp.add_line((0, -15), (width, -15), dxfattribs={"layer": "DIMENSION"})
    draw_arrowhead(msp, (0, -15), (width, -15), arrow_size)
    draw_arrowhead(msp, (width, -15), (0, -15), arrow_size)
    msp.add_mtext(f"{width}", dxfattribs={"layer": "ANNOTATION", "char_height": dim_text_height}).set_location((width/2, -10), attachment_point=5)

    # Overall length dimension
    msp.add_line((-20, 0), (-10, 0), dxfattribs={"layer": "DIMENSION"})
    msp.add_line((-20, length), (-10, length), dxfattribs={"layer": "DIMENSION"})
    msp.add_line((-15, 0), (-15, length), dxfattribs={"layer": "DIMENSION"})
    draw_arrowhead(msp, (-15, 0), (-15, length), arrow_size)
    draw_arrowhead(msp, (-15, length), (-15, 0), arrow_size)
    msp.add_mtext(f"{length}", dxfattribs={"layer": "ANNOTATION", "char_height": dim_text_height}).set_location((-10, length/2), attachment_point=5)

    # Horizontal hole dimensioning (first column offset and pitch)
    msp.add_line((0, y_coords[0]-10), (0, y_coords[0]+10), dxfattribs={"layer": "DIMENSION"})
    msp.add_line((x_coords[0], y_coords[0]-10), (x_coords[0], y_coords[0]+10), dxfattribs={"layer": "DIMENSION"})
    msp.add_line((0, y_coords[0]), (x_coords[0], y_coords[0]), dxfattribs={"layer": "DIMENSION"})
    draw_arrowhead(msp, (0, y_coords[0]), (x_coords[0], y_coords[0]), arrow_size)
    draw_arrowhead(msp, (x_coords[0], y_coords[0]), (0, y_coords[0]), arrow_size)
    msp.add_mtext(f"{x_coords[0]}", dxfattribs={"layer": "ANNOTATION", "char_height": dim_text_height}).set_location((x_coords[0]/2, y_coords[0]+5), attachment_point=5)

    msp.add_line((x_coords[0], y_coords[0]-10), (x_coords[0], y_coords[0]+10), dxfattribs={"layer": "DIMENSION"})
    msp.add_line((x_coords[1], y_coords[0]-10), (x_coords[1], y_coords[0]+10), dxfattribs={"layer": "DIMENSION"})
    msp.add_line((x_coords[0], y_coords[0]), (x_coords[1], y_coords[0]), dxfattribs={"layer": "DIMENSION"})
    draw_arrowhead(msp, (x_coords[0], y_coords[0]), (x_coords[1], y_coords[0]), arrow_size)
    draw_arrowhead(msp, (x_coords[1], y_coords[0]), (x_coords[0], y_coords[0]), arrow_size)
    msp.add_mtext(f"{x_coords[1]-x_coords[0]}", dxfattribs={"layer": "ANNOTATION", "char_height": dim_text_height}).set_location((x_coords[0]+(x_coords[1]-x_coords[0])/2, y_coords[0]+5), attachment_point=5)

    # Vertical hole dimensioning (first row offset and pitch)
    msp.add_line((x_coords[0]-10, 0), (x_coords[0]+10, 0), dxfattribs={"layer": "DIMENSION"})
    msp.add_line((x_coords[0]-10, y_coords[0]), (x_coords[0]+10, y_coords[0]), dxfattribs={"layer": "DIMENSION"})
    msp.add_line((x_coords[0], 0), (x_coords[0], y_coords[0]), dxfattribs={"layer": "DIMENSION"})
    draw_arrowhead(msp, (x_coords[0], 0), (x_coords[0], y_coords[0]), arrow_size)
    draw_arrowhead(msp, (x_coords[0], y_coords[0]), (x_coords[0], 0), arrow_size)
    msp.add_mtext(f"{y_coords[0]}", dxfattribs={"layer": "ANNOTATION", "char_height": dim_text_height}).set_location((x_coords[0]+5, y_coords[0]/2), attachment_point=5)

    msp.add_line((x_coords[0]-10, y_coords[0]), (x_coords[0]+10, y_coords[0]), dxfattribs={"layer": "DIMENSION"})
    msp.add_line((x_coords[0]-10, y_coords[1]), (x_coords[0]+10, y_coords[1]), dxfattribs={"layer": "DIMENSION"})
    msp.add_line((x_coords[0], y_coords[0]), (x_coords[0], y_coords[1]), dxfattribs={"layer": "DIMENSION"})
    draw_arrowhead(msp, (x_coords[0], y_coords[0]), (x_coords[0], y_coords[1]), arrow_size)
    draw_arrowhead(msp, (x_coords[0], y_coords[1]), (x_coords[0], y_coords[0]), arrow_size)
    msp.add_mtext(f"{y_coords[1]-y_coords[0]}", dxfattribs={"layer": "ANNOTATION", "char_height": dim_text_height}).set_location((x_coords[0]+5, y_coords[0]+(y_coords[1]-y_coords[0])/2), attachment_point=5)

    filename = sys.argv[1] if len(sys.argv) > 1 else f"{description}_{part_id}.dxf"
    doc.saveas(filename)
    print(f'Saved {filename}')

if __name__ == '__main__':
    create_dxf()
