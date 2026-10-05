import ezdxf
import math

def get_insert_bounding_box(path, insert_name):
    doc = ezdxf.readfile(path)
    msp = doc.modelspace()

    # 找到指定 INSERT
    target_insert = None
    for insert in msp.query("INSERT"):
        if insert.dxf.name == insert_name:
            target_insert = insert
            break

    if target_insert is None:
        print(f"❌ 找不到 INSERT: {insert_name}")
        return None

    block_name = target_insert.dxf.name
    block = doc.blocks[block_name]

    # 取得 scale 與 rotation
    sx, sy, _ = target_insert.dxf.xscale, target_insert.dxf.yscale, target_insert.dxf.zscale
    rotation_deg = target_insert.dxf.rotation
    rotation_rad = math.radians(rotation_deg)

    cos_r = math.cos(rotation_rad)
    sin_r = math.sin(rotation_rad)

    points = []

    # 取得 BLOCK 內所有 LWPOLYLINE 的點
    for entity in block:
        if entity.dxftype() == "LWPOLYLINE":
            for x, y, *_ in entity.get_points():
                # 套 scale
                x *= sx
                y *= sy

                # 套 rotation
                new_x = x * cos_r - y * sin_r
                new_y = x * sin_r + y * cos_r

                points.append((new_x, new_y))

    if not points:
        print(f"⚠️ BLOCK {block_name} 裡沒有多邊形")
        return None

    # 計算邊界 box
    min_x = min(p[0] for p in points)
    max_x = max(p[0] for p in points)
    min_y = min(p[1] for p in points)
    max_y = max(p[1] for p in points)

    width = max_x - min_x
    height = max_y - min_y

    return {
        "insert_name": insert_name,
        "width": width,
        "height": height,
        "min_x": min_x,
        "max_x": max_x,
        "min_y": min_y,
        "max_y": max_y,
    }
#partsName=["FOXING_IN-9","FOXING_OUT-9","QTR_IN-9","QTR_OUT-9"]
result = get_insert_bounding_box("C:/python/Nike_Nesting_MINZ_DXF-2/parts/parts00.dxf", "FOXING_IN-9")
if result:
    print("寬度:", result["width"])
    print("高度:", result["height"])
