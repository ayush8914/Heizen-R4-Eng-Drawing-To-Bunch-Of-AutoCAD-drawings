import ezdxf
import sys
import math

def create_part_dxf():
    out = sys.argv[1]
    doc = ezdxf.new("R2010", setup=True)
    doc.units = ezdxf.units.MM
    msp = doc.modelspace()

    # Define layers
    doc.layers.add("GEOMETRY", color=7)  # White/Black
    doc.layers.add("DIMENSION", color=3) # Green
    doc.layers.add("ANNOTATION", color=1) # Red

    # Part metadata
    part_id = "horizontal_brace_gusset_737"
    thickness = 12 # Estimated, typical for gussets
    material = "PL" # Plate
    
    # Traceability: Dimensions from drawing (estimated based on M24 bolt pattern and typical edge distances)
    # Assumed identical to horizontal_brace_gusset_735 as no specific differing dimensions provided.
    # Origin (0,0) is at the inner corner where vertical leg and horizontal brace meet.
    # Left edge connects to vertical leg, bottom edge connects to horizontal brace.
    plate_width = 155   # Overall width of the gusset (EST: 40 + 75 + 40 = 155mm)
    plate_height = 230  # Overall height of the gusset (EST: 40 + 75 + 75 + 40 = 230mm)

    hole_dia = 26       # For M24 bolt (24mm bolt + 2mm clearance)
    
    # Hole positions parameters
    h_edge_dist_bottom = 40 # Edge distance from bottom edge to horizontal holes
    h_edge_dist_left = 40   # Edge distance from left edge to first horizontal hole
    h_pitch = 75            # Pitch between horizontal holes

    v_edge_dist_left = 40   # Edge distance from left edge to vertical holes
    v_edge_dist_bottom = 40 # Edge distance from bottom edge to first vertical hole (shared with h_edge_dist_bottom)
    v_pitch = 75            # Pitch between vertical holes

    # --- GEOMETRY ---
    
    # Main profile (Right-angled triangular shape)
    # Vertices: (0,0) bottom-left, (plate_width, 0) bottom-right, (0, plate_height) top-left
    # The diagonal cut connects (plate_width, 0) and (0, plate_height)
    points = [
        (0, 0),
        (plate_width, 0),
        (0, plate_height)
    ]
    msp.add_lwpolyline(points, close=True, dxfattribs={"layer": "GEOMETRY"})

    # All unique hole centers (M24 holes: 26mm diameter)
    hole_centers = [
        (h_edge_dist_left, h_edge_dist_bottom),                                 # (40,40) Shared by horizontal & vertical
        (h_edge_dist_left + h_pitch, h_edge_dist_bottom),                       # (115,40) Horizontal connection
        (v_edge_dist_left, v_edge_dist_bottom + v_pitch),                       # (40,115) Vertical connection
        (v_edge_dist_left, v_edge_dist_bottom + 2 * v_pitch)                    # (40,190) Vertical connection
    ]
    
    for center in hole_centers:
        msp.add_circle(center, hole_dia/2, dxfattribs={"layer": "GEOMETRY"})

    # --- ANNOTATIONS & DIMENSIONS ---
    char_h = 5.58 # Standard text height for readability at 1:1

    # Part Title and Metadata
    mt = msp.add_mtext(f"PART: {part_id.replace('_', ' ').upper()}", dxfattribs={"layer": "ANNOTATION", "char_height": char_h})
    mt.set_location((plate_width/2, plate_height + 20), attachment_point=1) # Top center

    mt = msp.add_mtext(f"MATERIAL: {material}", dxfattribs={"layer": "ANNOTATION", "char_height": char_h})
    mt.set_location((plate_width/2, plate_height + 12), attachment_point=1)

    mt = msp.add_mtext(f"THICKNESS: {thickness} mm", dxfattribs={"layer": "ANNOTATION", "char_height": char_h})
    mt.set_location((plate_width/2, plate_height + 4), attachment_point=1)

    # Overall Dimensions
    # Horizontal overall dimension (width)
    msp.add_line((0, -10), (0, -20), dxfattribs={"layer": "DIMENSION"}) # Extension line
    msp.add_line((plate_width, -10), (plate_width, -20), dxfattribs={"layer": "DIMENSION"}) # Extension line
    msp.add_line((0, -15), (plate_width, -15), dxfattribs={"layer": "DIMENSION"}) # Dimension line
    msp.add_line((0, -15), (5, -12), dxfattribs={"layer": "DIMENSION"}); msp.add_line((0, -15), (5, -18), dxfattribs={"layer": "DIMENSION"}) # Arrowhead
    msp.add_line((plate_width, -15), (plate_width-5, -12), dxfattribs={"layer": "DIMENSION"}); msp.add_line((plate_width, -15), (plate_width-5, -18), dxfattribs={"layer": "DIMENSION"}) # Arrowhead
    mt = msp.add_mtext(f"{plate_width}", dxfattribs={"layer": "DIMENSION", "char_height": char_h})
    mt.set_location((plate_width/2, -15), attachment_point=5) # Middle center

    # Vertical overall dimension (height)
    msp.add_line((-10, 0), (-20, 0), dxfattribs={"layer": "DIMENSION"}) # Extension line
    msp.add_line((-10, plate_height), (-20, plate_height), dxfattribs={"layer": "DIMENSION"}) # Extension line
    msp.add_line((-15, 0), (-15, plate_height), dxfattribs={"layer": "DIMENSION"}) # Dimension line
    msp.add_line((-15, 0), (-12, 5), dxfattribs={"layer": "DIMENSION"}); msp.add_line((-15, 0), (-18, 5), dxfattribs={"layer": "DIMENSION"}) # Arrowhead
    msp.add_line((-15, plate_height), (-12, plate_height-5), dxfattribs={"layer": "DIMENSION"}); msp.add_line((-15, plate_height), (-18, plate_height-5), dxfattribs={"layer": "DIMENSION"}) # Arrowhead
    mt = msp.add_mtext(f"{plate_height}", dxfattribs={"layer": "DIMENSION", "char_height": char_h})
    mt.set_location((-15, plate_height/2), attachment_point=5) # Middle center

    # Hole dimensions (Horizontal from left edge)
    dim_y_offset_h1 = -30
    dim_y_offset_h2 = -45

    # Extension lines for 0, h_edge_dist_left, h_edge_dist_left + h_pitch
    msp.add_line((0, dim_y_offset_h1-5), (0, dim_y_offset_h1+5), dxfattribs={"layer": "DIMENSION"})
    msp.add_line((h_edge_dist_left, dim_y_offset_h1-5), (h_edge_dist_left, dim_y_offset_h1+5), dxfattribs={"layer": "DIMENSION"})
    msp.add_line((h_edge_dist_left + h_pitch, dim_y_offset_h1-5), (h_edge_dist_left + h_pitch, dim_y_offset_h1+5), dxfattribs={"layer": "DIMENSION"})

    # 1st pitch (0 to first horizontal hole: 40)
    msp.add_line((0, dim_y_offset_h1), (h_edge_dist_left, dim_y_offset_h1), dxfattribs={"layer": "DIMENSION"})
    msp.add_line((0, dim_y_offset_h1), (5, dim_y_offset_h1-3), dxfattribs={"layer": "DIMENSION"}); msp.add_line((0, dim_y_offset_h1), (5, dim_y_offset_h1+3), dxfattribs={"layer": "DIMENSION"})
    msp.add_line((h_edge_dist_left, dim_y_offset_h1), (h_edge_dist_left-5, dim_y_offset_h1-3), dxfattribs={"layer": "DIMENSION"}); msp.add_line((h_edge_dist_left, dim_y_offset_h1), (h_edge_dist_left-5, dim_y_offset_h1+3), dxfattribs={"layer": "DIMENSION"})
    mt = msp.add_mtext(f"{h_edge_dist_left}", dxfattribs={"layer": "DIMENSION", "char_height": char_h})
    mt.set_location((h_edge_dist_left/2, dim_y_offset_h1), attachment_point=5)

    # 2nd pitch (first horizontal hole to second horizontal hole: 75)
    msp.add_line((h_edge_dist_left, dim_y_offset_h2), (h_edge_dist_left + h_pitch, dim_y_offset_h2), dxfattribs={"layer": "DIMENSION"})
    msp.add_line((h_edge_dist_left, dim_y_offset_h2), (h_edge_dist_left+5, dim_y_offset_h2-3), dxfattribs={"layer": "DIMENSION"}); msp.add_line((h_edge_dist_left, dim_y_offset_h2), (h_edge_dist_left+5, dim_y_offset_h2+3), dxfattribs={"layer": "DIMENSION"})
    msp.add_line((h_edge_dist_left + h_pitch, dim_y_offset_h2), (h_edge_dist_left + h_pitch-5, dim_y_offset_h2-3), dxfattribs={"layer": "DIMENSION"}); msp.add_line((h_edge_dist_left + h_pitch, dim_y_offset_h2), (h_edge_dist_left + h_pitch-5, dim_y_offset_h2+3), dxfattribs={"layer": "DIMENSION"})
    mt = msp.add_mtext(f"{h_pitch}", dxfattribs={"layer": "DIMENSION", "char_height": char_h})
    mt.set_location((h_edge_dist_left + h_pitch/2, dim_y_offset_h2), attachment_point=5)

    # Hole dimensions (Vertical from bottom edge)
    dim_x_offset_v1 = -30
    dim_x_offset_v2 = -45
    dim_x_offset_v3 = -60

    # Extension lines for 0, v_edge_dist_bottom, v_edge_dist_bottom + v_pitch, v_edge_dist_bottom + 2 * v_pitch
    msp.add_line((dim_x_offset_v1-5, 0), (dim_x_offset_v1+5, 0), dxfattribs={"layer": "DIMENSION"})
    msp.add_line((dim_x_offset_v1-5, v_edge_dist_bottom), (dim_x_offset_v1+5, v_edge_dist_bottom), dxfattribs={"layer": "DIMENSION"}) # First hole (40,40)
    msp.add_line((dim_x_offset_v1-5, v_edge_dist_bottom + v_pitch), (dim_x_offset_v1+5, v_edge_dist_bottom + v_pitch), dxfattribs={"layer": "DIMENSION"}) # Second hole (40,115)
    msp.add_line((dim_x_offset_v1-5, v_edge_dist_bottom + 2 * v_pitch), (dim_x_offset_v1+5, v_edge_dist_bottom + 2 * v_pitch), dxfattribs={"layer": "DIMENSION"}) # Third hole (40,190)

    # 1st pitch (0 to first vertical hole: 40)
    msp.add_line((dim_x_offset_v1, 0), (dim_x_offset_v1, v_edge_dist_bottom), dxfattribs={"layer": "DIMENSION"})
    msp.add_line((dim_x_offset_v1, 0), (dim_x_offset_v1-3, 5), dxfattribs={"layer": "DIMENSION"}); msp.add_line((dim_x_offset_v1, 0), (dim_x_offset_v1+3, 5), dxfattribs={"layer": "DIMENSION"})
    msp.add_line((dim_x_offset_v1, v_edge_dist_bottom), (dim_x_offset_v1-3, v_edge_dist_bottom-5), dxfattribs={"layer": "DIMENSION"}); msp.add_line((dim_x_offset_v1, v_edge_dist_bottom), (dim_x_offset_v1+3, v_edge_dist_bottom-5), dxfattribs={"layer": "DIMENSION"})
    mt = msp.add_mtext(f"{v_edge_dist_bottom}", dxfattribs={"layer": "DIMENSION", "char_height": char_h})
    mt.set_location((dim_x_offset_v1, v_edge_dist_bottom/2), attachment_point=5)

    # 2nd pitch (first vertical hole to second vertical hole: 75)
    msp.add_line((dim_x_offset_v2, v_edge_dist_bottom), (dim_x_offset_v2, v_edge_dist_bottom + v_pitch), dxfattribs={"layer": "DIMENSION"})
    msp.add_line((dim_x_offset_v2, v_edge_dist_bottom), (dim_x_offset_v2-3, v_edge_dist_bottom+5), dxfattribs={"layer": "DIMENSION"}); msp.add_line((dim_x_offset_v2, v_edge_dist_bottom), (dim_x_offset_v2+3, v_edge_dist_bottom+5), dxfattribs={"layer": "DIMENSION"})
    msp.add_line((dim_x_offset_v2, v_edge_dist_bottom + v_pitch), (dim_x_offset_v2-3, v_edge_dist_bottom + v_pitch-5), dxfattribs={"layer": "DIMENSION"}); msp.add_line((dim_x_offset_v2, v_edge_dist_bottom + v_pitch), (dim_x_offset_v2+3, v_edge_dist_bottom + v_pitch-5), dxfattribs={"layer": "DIMENSION"})
    mt = msp.add_mtext(f"{v_pitch}", dxfattribs={"layer": "DIMENSION", "char_height": char_h})
    mt.set_location((dim_x_offset_v2, v_edge_dist_bottom + v_pitch/2), attachment_point=5)

    # 3rd pitch (second vertical hole to third vertical hole: 75)
    msp.add_line((dim_x_offset_v3, v_edge_dist_bottom + v_pitch), (dim_x_offset_v3, v_edge_dist_bottom + 2 * v_pitch), dxfattribs={"layer": "DIMENSION"})
    msp.add_line((dim_x_offset_v3, v_edge_dist_bottom + v_pitch), (dim_x_offset_v3-3, v_edge_dist_bottom + v_pitch+5), dxfattribs={"layer": "DIMENSION"}); msp.add_line((dim_x_offset_v3, v_edge_dist_bottom + v_pitch), (dim_x_offset_v3+3, v_edge_dist_bottom + v_pitch+5), dxfattribs={"layer": "DIMENSION"})
    msp.add_line((dim_x_offset_v3, v_edge_dist_bottom + 2 * v_pitch), (dim_x_offset_v3-3, v_edge_dist_bottom + 2 * v_pitch-5), dxfattribs={"layer": "DIMENSION"}); msp.add_line((dim_x_offset_v3, v_edge_dist_bottom + 2 * v_pitch), (dim_x_offset_v3+3, v_edge_dist_bottom + 2 * v_pitch-5), dxfattribs={"layer": "DIMENSION"})
    mt = msp.add_mtext(f"{v_pitch}", dxfattribs={"layer": "DIMENSION", "char_height": char_h})
    mt.set_location((dim_x_offset_v3, v_edge_dist_bottom + v_pitch + v_pitch/2), attachment_point=5)

    # Hole callouts
    mt = msp.add_mtext(f"2x Ø{hole_dia} (M24) Horiz. Conn.", dxfattribs={"layer": "ANNOTATION", "char_height": char_h})
    mt.set_location((h_edge_dist_left + h_pitch + 30, h_edge_dist_bottom), attachment_point=4) # Middle Left
    mt = msp.add_mtext(f"3x Ø{hole_dia} (M24) Vert. Conn.", dxfattribs={"layer": "ANNOTATION", "char_height": char_h})
    mt.set_location((v_edge_dist_left + 30, v_edge_dist_bottom + 2 * v_pitch), attachment_point=4)

    filename = f'{part_id}.dxf'
    doc.saveas(out)

create_part_dxf()
