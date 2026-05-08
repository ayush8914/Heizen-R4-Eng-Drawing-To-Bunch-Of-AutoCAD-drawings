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
    part_id = "tower_leg_base_plate_734"
    thickness = 20 # From "BLE 20x290" in prompt (drawing shows 28x290 but prompt is authoritative)
    material = "PL" # Plate
    
    # Traceability: Dimensions from drawing
    plate_width = 290   # From "BLE 20x290"
    plate_height = 290  # Assumed square based on typical base plates and 290mm dimension

    # Holes for M27 anchor bolts (29mm diameter)
    anchor_hole_dia = 29 # For M27 bolt (27mm bolt + 2mm clearance)
    anchor_edge_dist = 45 # Estimated typical edge distance from drawing
    
    # Holes for M24 leg connection (26mm diameter)
    leg_hole_dia = 26   # For M24 bolt (24mm bolt + 2mm clearance)
    leg_edge_dist = 80  # Estimated, inside the leg section area (approx 250x250 from Schnitt A-A)
    leg_pitch = 130     # Estimated (210 - 80 = 130), pitch between inner leg connection holes

    # --- GEOMETRY ---
    
    # Main profile (Rectangular plate)
    msp.add_lwpolyline([(0,0), (plate_width,0), (plate_width,plate_height), (0,plate_height)], close=True, dxfattribs={"layer": "GEOMETRY"})

    # Holes for M27 anchor bolts (4 holes, around corners)
    anchor_holes = [
        (anchor_edge_dist, anchor_edge_dist),
        (plate_width - anchor_edge_dist, anchor_edge_dist),
        (anchor_edge_dist, plate_height - anchor_edge_dist),
        (plate_width - anchor_edge_dist, plate_height - anchor_edge_dist)
    ]
    for h_pos in anchor_holes:
        msp.add_circle(h_pos, anchor_hole_dia/2, dxfattribs={"layer": "GEOMETRY"})

    # Holes for M24 leg connection (4 holes, in a square pattern for the leg section)
    leg_holes = [
        (leg_edge_dist, leg_edge_dist),
        (leg_edge_dist + leg_pitch, leg_edge_dist),
        (leg_edge_dist, leg_edge_dist + leg_pitch),
        (leg_edge_dist + leg_pitch, leg_edge_dist + leg_pitch)
    ]
    for h_pos in leg_holes:
        msp.add_circle(h_pos, leg_hole_dia/2, dxfattribs={"layer": "GEOMETRY"})

    # --- ANNOTATIONS & DIMENSIONS ---
    char_h = 5.58 # Standard text height

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

    # Anchor hole dimensions (Horizontal)
    dim_y_offset_h_anchor1 = -30
    dim_y_offset_h_anchor2 = -45
    
    # Extension lines for horizontal anchor hole dimensions: 0, 45, 245, 290
    msp.add_line((0, dim_y_offset_h_anchor1-5), (0, dim_y_offset_h_anchor1+5), dxfattribs={"layer": "DIMENSION"})
    msp.add_line((anchor_edge_dist, dim_y_offset_h_anchor1-5), (anchor_edge_dist, dim_y_offset_h_anchor1+5), dxfattribs={"layer": "DIMENSION"})
    msp.add_line((plate_width - anchor_edge_dist, dim_y_offset_h_anchor1-5), (plate_width - anchor_edge_dist, dim_y_offset_h_anchor1+5), dxfattribs={"layer": "DIMENSION"})
    msp.add_line((plate_width, dim_y_offset_h_anchor1-5), (plate_width, dim_y_offset_h_anchor1+5), dxfattribs={"layer": "DIMENSION"})

    # Dim 0 to 45 (anchor_edge_dist)
    msp.add_line((0, dim_y_offset_h_anchor1), (anchor_edge_dist, dim_y_offset_h_anchor1), dxfattribs={"layer": "DIMENSION"})
    msp.add_line((0, dim_y_offset_h_anchor1), (5, dim_y_offset_h_anchor1-3), dxfattribs={"layer": "DIMENSION"}); msp.add_line((0, dim_y_offset_h_anchor1), (5, dim_y_offset_h_anchor1+3), dxfattribs={"layer": "DIMENSION"})
    msp.add_line((anchor_edge_dist, dim_y_offset_h_anchor1), (anchor_edge_dist-5, dim_y_offset_h_anchor1-3), dxfattribs={"layer": "DIMENSION"}); msp.add_line((anchor_edge_dist, dim_y_offset_h_anchor1), (anchor_edge_dist-5, dim_y_offset_h_anchor1+3), dxfattribs={"layer": "DIMENSION"})
    mt = msp.add_mtext(f"{anchor_edge_dist}", dxfattribs={"layer": "DIMENSION", "char_height": char_h})
    mt.set_location((anchor_edge_dist/2, dim_y_offset_h_anchor1), attachment_point=5)

    # Dim 45 to 245 (plate_width - 2 * anchor_edge_dist)
    msp.add_line((anchor_edge_dist, dim_y_offset_h_anchor2), (plate_width - anchor_edge_dist, dim_y_offset_h_anchor2), dxfattribs={"layer": "DIMENSION"})
    msp.add_line((anchor_edge_dist, dim_y_offset_h_anchor2), (anchor_edge_dist+5, dim_y_offset_h_anchor2-3), dxfattribs={"layer": "DIMENSION"}); msp.add_line((anchor_edge_dist, dim_y_offset_h_anchor2), (anchor_edge_dist+5, dim_y_offset_h_anchor2+3), dxfattribs={"layer": "DIMENSION"})
    msp.add_line((plate_width - anchor_edge_dist, dim_y_offset_h_anchor2), (plate_width - anchor_edge_dist-5, dim_y_offset_h_anchor2-3), dxfattribs={"layer": "DIMENSION"}); msp.add_line((plate_width - anchor_edge_dist, dim_y_offset_h_anchor2), (plate_width - anchor_edge_dist-5, dim_y_offset_h_anchor2+3), dxfattribs={"layer": "DIMENSION"})
    mt = msp.add_mtext(f"{plate_width - 2 * anchor_edge_dist}", dxfattribs={"layer": "DIMENSION", "char_height": char_h})
    mt.set_location((plate_width/2, dim_y_offset_h_anchor2), attachment_point=5)

    # Dim 245 to 290 (anchor_edge_dist)
    msp.add_line((plate_width - anchor_edge_dist, dim_y_offset_h_anchor1), (plate_width, dim_y_offset_h_anchor1), dxfattribs={"layer": "DIMENSION"})
    msp.add_line((plate_width - anchor_edge_dist, dim_y_offset_h_anchor1), (plate_width - anchor_edge_dist+5, dim_y_offset_h_anchor1-3), dxfattribs={"layer": "DIMENSION"}); msp.add_line((plate_width - anchor_edge_dist, dim_y_offset_h_anchor1), (plate_width - anchor_edge_dist+5, dim_y_offset_h_anchor1+3), dxfattribs={"layer": "DIMENSION"})
    msp.add_line((plate_width, dim_y_offset_h_anchor1), (plate_width-5, dim_y_offset_h_anchor1-3), dxfattribs={"layer": "DIMENSION"}); msp.add_line((plate_width, dim_y_offset_h_anchor1), (plate_width-5, dim_y_offset_h_anchor1+3), dxfattribs={"layer": "DIMENSION"})
    mt = msp.add_mtext(f"{anchor_edge_dist}", dxfattribs={"layer": "DIMENSION", "char_height": char_h})
    mt.set_location((plate_width - anchor_edge_dist/2, dim_y_offset_h_anchor1), attachment_point=5)

    # Leg holes - horizontal dimensioning
    dim_y_offset_h_leg = -60
    # Extension lines for leg_edge_dist, leg_edge_dist + leg_pitch
    msp.add_line((leg_edge_dist, dim_y_offset_h_leg-5), (leg_edge_dist, dim_y_offset_h_leg+5), dxfattribs={"layer": "DIMENSION"})
    msp.add_line((leg_edge_dist + leg_pitch, dim_y_offset_h_leg-5), (leg_edge_dist + leg_pitch, dim_y_offset_h_leg+5), dxfattribs={"layer": "DIMENSION"})
    msp.add_line((leg_edge_dist, dim_y_offset_h_leg), (leg_edge_dist + leg_pitch, dim_y_offset_h_leg), dxfattribs={"layer": "DIMENSION"})
    msp.add_line((leg_edge_dist, dim_y_offset_h_leg), (leg_edge_dist+5, dim_y_offset_h_leg-3), dxfattribs={"layer": "DIMENSION"}); msp.add_line((leg_edge_dist, dim_y_offset_h_leg), (leg_edge_dist+5, dim_y_offset_h_leg+3), dxfattribs={"layer": "DIMENSION"})
    msp.add_line((leg_edge_dist + leg_pitch, dim_y_offset_h_leg), (leg_edge_dist + leg_pitch-5, dim_y_offset_h_leg-3), dxfattribs={"layer": "DIMENSION"}); msp.add_line((leg_edge_dist + leg_pitch, dim_y_offset_h_leg), (leg_edge_dist + leg_pitch-5, dim_y_offset_h_leg+3), dxfattribs={"layer": "DIMENSION"})
    mt = msp.add_mtext(f"{leg_pitch}", dxfattribs={"layer": "DIMENSION", "char_height": char_h})
    mt.set_location((leg_edge_dist + leg_pitch/2, dim_y_offset_h_leg), attachment_point=5)
    
    # Vertical Anchor hole dimensions
    dim_x_offset_v_anchor1 = -30
    dim_x_offset_v_anchor2 = -45

    # Extension lines for vertical anchor hole dimensions: 0, 45, 245, 290
    msp.add_line((dim_x_offset_v_anchor1-5, 0), (dim_x_offset_v_anchor1+5, 0), dxfattribs={"layer": "DIMENSION"})
    msp.add_line((dim_x_offset_v_anchor1-5, anchor_edge_dist), (dim_x_offset_v_anchor1+5, anchor_edge_dist), dxfattribs={"layer": "DIMENSION"})
    msp.add_line((dim_x_offset_v_anchor1-5, plate_height - anchor_edge_dist), (dim_x_offset_v_anchor1+5, plate_height - anchor_edge_dist), dxfattribs={"layer": "DIMENSION"})
    msp.add_line((dim_x_offset_v_anchor1-5, plate_height), (dim_x_offset_v_anchor1+5, plate_height), dxfattribs={"layer": "DIMENSION"})

    # Dim 0 to 45 (anchor_edge_dist)
    msp.add_line((dim_x_offset_v_anchor1, 0), (dim_x_offset_v_anchor1, anchor_edge_dist), dxfattribs={"layer": "DIMENSION"})
    msp.add_line((dim_x_offset_v_anchor1, 0), (dim_x_offset_v_anchor1-3, 5), dxfattribs={"layer": "DIMENSION"}); msp.add_line((dim_x_offset_v_anchor1, 0), (dim_x_offset_v_anchor1+3, 5), dxfattribs={"layer": "DIMENSION"})
    msp.add_line((dim_x_offset_v_anchor1, anchor_edge_dist), (dim_x_offset_v_anchor1-3, anchor_edge_dist-5), dxfattribs={"layer": "DIMENSION"}); msp.add_line((dim_x_offset_v_anchor1, anchor_edge_dist), (dim_x_offset_v_anchor1+3, anchor_edge_dist-5), dxfattribs={"layer": "DIMENSION"})
    mt = msp.add_mtext(f"{anchor_edge_dist}", dxfattribs={"layer": "DIMENSION", "char_height": char_h})
    mt.set_location((dim_x_offset_v_anchor1, anchor_edge_dist/2), attachment_point=5)

    # Dim 45 to 245 (plate_height - 2 * anchor_edge_dist)
    msp.add_line((dim_x_offset_v_anchor2, anchor_edge_dist), (dim_x_offset_v_anchor2, plate_height - anchor_edge_dist), dxfattribs={"layer": "DIMENSION"})
    msp.add_line((dim_x_offset_v_anchor2, anchor_edge_dist), (dim_x_offset_v_anchor2-3, anchor_edge_dist+5), dxfattribs={"layer": "DIMENSION"}); msp.add_line((dim_x_offset_v_anchor2, anchor_edge_dist), (dim_x_offset_v_anchor2+3, anchor_edge_dist+5), dxfattribs={"layer": "DIMENSION"})
    msp.add_line((dim_x_offset_v_anchor2, plate_height - anchor_edge_dist), (dim_x_offset_v_anchor2-3, plate_height - anchor_edge_dist-5), dxfattribs={"layer": "DIMENSION"}); msp.add_line((dim_x_offset_v_anchor2, plate_height - anchor_edge_dist), (dim_x_offset_v_anchor2+3, plate_height - anchor_edge_dist-5), dxfattribs={"layer": "DIMENSION"})
    mt = msp.add_mtext(f"{plate_height - 2 * anchor_edge_dist}", dxfattribs={"layer": "DIMENSION", "char_height": char_h})
    mt.set_location((dim_x_offset_v_anchor2, plate_height/2), attachment_point=5)

    # Dim 245 to 290 (anchor_edge_dist)
    msp.add_line((dim_x_offset_v_anchor1, plate_height - anchor_edge_dist), (dim_x_offset_v_anchor1, plate_height), dxfattribs={"layer": "DIMENSION"})
    msp.add_line((dim_x_offset_v_anchor1, plate_height - anchor_edge_dist), (dim_x_offset_v_anchor1-3, plate_height - anchor_edge_dist+5), dxfattribs={"layer": "DIMENSION"}); msp.add_line((dim_x_offset_v_anchor1, plate_height - anchor_edge_dist), (dim_x_offset_v_anchor1+3, plate_height - anchor_edge_dist+5), dxfattribs={"layer": "DIMENSION"})
    msp.add_line((dim_x_offset_v_anchor1, plate_height), (dim_x_offset_v_anchor1-3, plate_height-5), dxfattribs={"layer": "DIMENSION"}); msp.add_line((dim_x_offset_v_anchor1, plate_height), (dim_x_offset_v_anchor1+3, plate_height-5), dxfattribs={"layer": "DIMENSION"})
    mt = msp.add_mtext(f"{anchor_edge_dist}", dxfattribs={"layer": "DIMENSION", "char_height": char_h})
    mt.set_location((dim_x_offset_v_anchor1, plate_height - anchor_edge_dist/2), attachment_point=5)

    # Leg holes - vertical dimensioning
    dim_x_offset_v_leg = -60
    # Extension lines for leg_edge_dist, leg_edge_dist + leg_pitch
    msp.add_line((dim_x_offset_v_leg-5, leg_edge_dist), (dim_x_offset_v_leg+5, leg_edge_dist), dxfattribs={"layer": "DIMENSION"})
    msp.add_line((dim_x_offset_v_leg-5, leg_edge_dist + leg_pitch), (dim_x_offset_v_leg+5, leg_edge_dist + leg_pitch), dxfattribs={"layer": "DIMENSION"})
    msp.add_line((dim_x_offset_v_leg, leg_edge_dist), (dim_x_offset_v_leg, leg_edge_dist + leg_pitch), dxfattribs={"layer": "DIMENSION"})
    msp.add_line((dim_x_offset_v_leg, leg_edge_dist), (dim_x_offset_v_leg-3, leg_edge_dist+5), dxfattribs={"layer": "DIMENSION"}); msp.add_line((dim_x_offset_v_leg, leg_edge_dist), (dim_x_offset_v_leg+3, leg_edge_dist+5), dxfattribs={"layer": "DIMENSION"})
    msp.add_line((dim_x_offset_v_leg, leg_edge_dist + leg_pitch), (dim_x_offset_v_leg-3, leg_edge_dist + leg_pitch-5), dxfattribs={"layer": "DIMENSION"}); msp.add_line((dim_x_offset_v_leg, leg_edge_dist + leg_pitch), (dim_x_offset_v_leg+3, leg_edge_dist + leg_pitch-5), dxfattribs={"layer": "DIMENSION"})
    mt = msp.add_mtext(f"{leg_pitch}", dxfattribs={"layer": "DIMENSION", "char_height": char_h})
    mt.set_location((dim_x_offset_v_leg, leg_edge_dist + leg_pitch/2), attachment_point=5)

    # Hole callouts
    mt = msp.add_mtext(f"4x Ø{anchor_hole_dia} (M27 Anchor) Symm.", dxfattribs={"layer": "ANNOTATION", "char_height": char_h})
    mt.set_location((plate_width/2, dim_y_offset_h_anchor2 - 20), attachment_point=1)

    mt = msp.add_mtext(f"4x Ø{leg_hole_dia} (M24 Leg Conn.) Symm.", dxfattribs={"layer": "ANNOTATION", "char_height": char_h})
    mt.set_location((plate_width/2, dim_y_offset_h_leg - 20), attachment_point=1)

    filename = f'{part_id}.dxf'
    doc.saveas(out)

create_part_dxf()
