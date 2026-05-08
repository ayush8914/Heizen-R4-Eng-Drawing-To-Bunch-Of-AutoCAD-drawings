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

    # Part parameters (Estimated from main elevation for part 738 and 'BLE 20x90 - 738')
    part_id = "738"
    description = "diagonal_brace_gusset_738"
    base_width = 200 # Estimated visual approximation from main view
    height = 300     # Estimated visual approximation from main view
    thickness = 20   # From 'BLE 20x90 - 738' (20mm thickness)
    material = "S355JR" # Assumed standard structural steel
    qty = 8          # Estimated quantity based on common tower structure
    hole_diameter = 30 # For M27 bolts (27mm + 3mm clearance)

    # GEOMETRY layer
    # Gusset outline as a right-angle triangle, bottom-left at (0,0)
    points_adjusted = [(0,0), (base_width,0), (0,height)]
    msp.add_lwpolyline(points_adjusted, close=True, dxfattribs={"layer": "GEOMETRY"})

    # Hole pattern (2 holes on the hypotenuse)
    # Hypotenuse goes from (base_width, 0) to (0, height)
    hypotenuse_length = math.sqrt(base_width**2 + height**2)
    edge_dist = 50 # Distance from each end of the hypotenuse along the hypotenuse line

    # Vector from (base_width, 0) to (0, height) is (-base_width, height)
    unit_vec_x_adj = -base_width / hypotenuse_length
    unit_vec_y_adj = height / hypotenuse_length

    # First bolt position from (base_width, 0) along the hypotenuse
    bolt1_x_adj = base_width + edge_dist * unit_vec_x_adj
    bolt1_y_adj = 0 + edge_dist * unit_vec_y_adj

    # Second bolt position from (0, height) along the hypotenuse (moving opposite to unit vector)
    bolt2_x_adj = 0 - edge_dist * unit_vec_x_adj
    bolt2_y_adj = height - edge_dist * unit_vec_y_adj

    msp.add_circle((bolt1_x_adj, bolt1_y_adj), hole_diameter / 2, dxfattribs={"layer": "GEOMETRY"})
    msp.add_circle((bolt2_x_adj, bolt2_y_adj), hole_diameter / 2, dxfattribs={"layer": "GEOMETRY"})

    # ANNOTATION layer
    msp.add_mtext(f"PART NO: {part_id}", dxfattribs={"layer": "ANNOTATION", "char_height": 5.0}).set_location((base_width + 50, height - 20), attachment_point=1)
    msp.add_mtext(f"DESCRIPTION: {description}", dxfattribs={"layer": "ANNOTATION", "char_height": 5.0}).set_location((base_width + 50, height - 40), attachment_point=1)
    msp.add_mtext(f"GUSSET: ~{base_width}x~{height}x{thickness} mm (approx)", dxfattribs={"layer": "ANNOTATION", "char_height": 5.0}).set_location((base_width + 50, height - 60), attachment_point=1)
    msp.add_mtext(f"MATERIAL: {material}", dxfattribs={"layer": "ANNOTATION", "char_height": 5.0}).set_location((base_width + 50, height - 80), attachment_point=1)
    msp.add_mtext(f"QTY: {qty} (EST)", dxfattribs={"layer": "ANNOTATION", "char_height": 5.0}).set_location((base_width + 50, height - 100), attachment_point=1)
    msp.add_mtext(f"HOLES: 2x Ø{hole_diameter} mm", dxfattribs={"layer": "ANNOTATION", "char_height": 5.0}).set_location((base_width + 50, height - 120), attachment_point=1)
    msp.add_mtext(f"Note: Dimensions EST from general view as specific detail for 738 not provided.", dxfattribs={"layer": "ANNOTATION", "char_height": 3.0}).set_location((base_width + 50, height - 140), attachment_point=1)

    # DIMENSION layer (manual dimensions for clarity)
    dim_text_height = 3.5
    arrow_size = 5

    # Base width dimension
    msp.add_line((0, -20), (0, -10), dxfattribs={"layer": "DIMENSION"})
    msp.add_line((base_width, -20), (base_width, -10), dxfattribs={"layer": "DIMENSION"})
    msp.add_line((0, -15), (base_width, -15), dxfattribs={"layer": "DIMENSION"})
    draw_arrowhead(msp, (0, -15), (base_width, -15), arrow_size)
    draw_arrowhead(msp, (base_width, -15), (0, -15), arrow_size)
    msp.add_mtext(f"~{base_width}", dxfattribs={"layer": "ANNOTATION", "char_height": dim_text_height}).set_location((base_width/2, -10), attachment_point=5)

    # Height dimension
    msp.add_line((-20, 0), (-10, 0), dxfattribs={"layer": "DIMENSION"})
    msp.add_line((-20, height), (-10, height), dxfattribs={"layer": "DIMENSION"})
    msp.add_line((-15, 0), (-15, height), dxfattribs={"layer": "DIMENSION"})
    draw_arrowhead(msp, (-15, 0), (-15, height), arrow_size)
    draw_arrowhead(msp, (-15, height), (-15, 0), arrow_size)
    msp.add_mtext(f"~{height}", dxfattribs={"layer": "ANNOTATION", "char_height": dim_text_height}).set_location((-10, height/2), attachment_point=5)

    # Bolt 1 horizontal dimension
    msp.add_line((0, bolt1_y_adj - 10), (0, bolt1_y_adj + 10), dxfattribs={"layer": "DIMENSION"})
    msp.add_line((bolt1_x_adj, bolt1_y_adj - 10), (bolt1_x_adj, bolt1_y_adj + 10), dxfattribs={"layer": "DIMENSION"})
    msp.add_line((0, bolt1_y_adj), (bolt1_x_adj, bolt1_y_adj), dxfattribs={"layer": "DIMENSION"})
    draw_arrowhead(msp, (0, bolt1_y_adj), (bolt1_x_adj, bolt1_y_adj), arrow_size)
    draw_arrowhead(msp, (bolt1_x_adj, bolt1_y_adj), (0, bolt1_y_adj), arrow_size)
    msp.add_mtext(f"~{bolt1_x_adj:.0f}", dxfattribs={"layer": "ANNOTATION", "char_height": dim_text_height}).set_location((bolt1_x_adj/2, bolt1_y_adj+5), attachment_point=5)

    # Bolt 1 vertical dimension
    msp.add_line((bolt1_x_adj - 10, 0), (bolt1_x_adj + 10, 0), dxfattribs={"layer": "DIMENSION"})
    msp.add_line((bolt1_x_adj - 10, bolt1_y_adj), (bolt1_x_adj + 10, bolt1_y_adj), dxfattribs={"layer": "DIMENSION"})
    msp.add_line((bolt1_x_adj, 0), (bolt1_x_adj, bolt1_y_adj), dxfattribs={"layer": "DIMENSION"})
    draw_arrowhead(msp, (bolt1_x_adj, 0), (bolt1_x_adj, bolt1_y_adj), arrow_size)
    draw_arrowhead(msp, (bolt1_x_adj, bolt1_y_adj), (bolt1_x_adj, 0), arrow_size)
    msp.add_mtext(f"~{bolt1_y_adj:.0f}", dxfattribs={"layer": "ANNOTATION", "char_height": dim_text_height}).set_location((bolt1_x_adj+5, bolt1_y_adj/2), attachment_point=5)

    filename = sys.argv[1] if len(sys.argv) > 1 else f"{description}_{part_id}.dxf"
    doc.saveas(filename)
    print(f'Saved {filename}')

if __name__ == '__main__':
    create_dxf()
