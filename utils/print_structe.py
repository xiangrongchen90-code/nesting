import ezdxf


def print_leather_structure(msp):
    print("=== Leather Structure (LWPOLYLINE in MSP) ===")

    for i, e in enumerate(msp.query("LWPOLYLINE")):
        print(f"\nPolyline #{i}")
        print(f"  Type: {e.dxftype()}")
        print(f"  Color: {e.dxf.color}")
        print(f"  Closed: {e.closed}")

        pts = list(e.get_points())
        print(f"  Points count: {len(pts)}")

        for x, y, *_ in pts:      # ⭐ 只取 x,y
            print(f"    ({x}, {y})")



def print_part_structure(doc, block_name):
    if block_name not in doc.blocks:
        print(f"❌ Block '{block_name}' 不存在！")
        return

    block = doc.blocks[block_name]

    print(f"\n=== Part Structure (Block: {block_name}) ===")

    for i, e in enumerate(block):
        if e.dxftype() != "LWPOLYLINE":
            print(f"  Entity #{i}: {e.dxftype()} (略過)")
            continue

        print(f"\n  Polyline #{i}")
        print(f"    Type: {e.dxftype()}")
        print(f"    Color: {e.dxf.color}")
        print(f"    Closed: {e.closed}")

        pts = list(e.get_points())
        print(f"    Points count: {len(pts)}")

        # 只輸出 xy，不顯示 bulge、start_width、end_width
        for (x, y, *_) in pts:
            print(f"      ({float(x)}, {float(y)})")

# temp_path="C:/python/Nike_Nesting_MINZ_DXF-2/leather/leather00_newcolor.dxf"
#
# doc1 = ezdxf.readfile(temp_path)
# msp1 = doc1.modelspace()
# print_leather_structure(msp1)

temp_path="C:/python/Nike_Nesting_MINZ_DXF-2/parts/parts00.dxf"
doc2 = ezdxf.readfile(temp_path)
msp2 = doc2.modelspace()
print_part_structure(doc2, "FOXING_IN-9")
