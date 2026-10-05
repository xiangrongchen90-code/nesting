import ezdxf
from collections import Counter
import os


# =========================
# DXF 檔案路徑
# =========================
dxf_path = r"C:\python\Nike_Nesting_MINZ_DXF-2 (5)(newGABO)\parts\7288_VAMP-8.dxf"


# =========================
# 讀取 DXF
# =========================
doc = ezdxf.readfile(dxf_path)
msp = doc.modelspace()

print("=" * 70)
print("DXF 檔案分析")
print("=" * 70)

print(f"檔案名稱：{os.path.basename(dxf_path)}")
print(f"DXF 版本：{doc.dxfversion}")
print()


# =========================================================
# 1. Entity 類型統計
# =========================================================
entity_counter = Counter()

for entity in msp:
    entity_counter[entity.dxftype()] += 1

print("=" * 70)
print("【1. Entity 類型統計】")
print("=" * 70)

for entity_type, count in entity_counter.items():
    print(f"{entity_type:<20} {count}")


# =========================================================
# 2. Layer 統計
# =========================================================
layer_counter = Counter()

for entity in msp:
    layer_counter[entity.dxf.layer] += 1

print()
print("=" * 70)
print("【2. Layer 統計】")
print("=" * 70)

for layer, count in layer_counter.items():
    print(f"{layer:<30} {count}")


# =========================================================
# 3. INSERT / Block 分析
# =========================================================
print()
print("=" * 70)
print("【3. Block / INSERT 分析】")
print("=" * 70)

insert_count = 0

for entity in msp:
    if entity.dxftype() == "INSERT":
        insert_count += 1

        print(f"\nINSERT #{insert_count}")
        print(f"Block 名稱：{entity.dxf.name}")
        print(f"插入位置：({entity.dxf.insert.x}, "
              f"{entity.dxf.insert.y}, "
              f"{entity.dxf.insert.z})")

        if entity.dxf.hasattr("rotation"):
            print(f"旋轉角度：{entity.dxf.rotation}")

        if entity.dxf.hasattr("xscale"):
            print(f"X Scale：{entity.dxf.xscale}")

        if entity.dxf.hasattr("yscale"):
            print(f"Y Scale：{entity.dxf.yscale}")


# =========================================================
# 4. LWPOLYLINE 分析
# =========================================================
print()
print("=" * 70)
print("【4. LWPOLYLINE 分析】")
print("=" * 70)

polyline_count = 0

for entity in msp:
    if entity.dxftype() == "LWPOLYLINE":

        polyline_count += 1

        points = list(entity.get_points())

        print(f"\nLWPOLYLINE #{polyline_count}")
        print(f"Layer：{entity.dxf.layer}")
        print(f"Vertex 數量：{len(points)}")
        print(f"是否封閉：{entity.closed}")

        if points:
            xs = [p[0] for p in points]
            ys = [p[1] for p in points]

            print(f"X 範圍：{min(xs):.3f} ~ {max(xs):.3f}")
            print(f"Y 範圍：{min(ys):.3f} ~ {max(ys):.3f}")
            print(f"寬度：{max(xs) - min(xs):.3f}")
            print(f"高度：{max(ys) - min(ys):.3f}")


# =========================================================
# 5. LINE / ARC / CIRCLE 統計
# =========================================================
print()
print("=" * 70)
print("【5. 基本幾何圖形分析】")
print("=" * 70)

for entity in msp:

    if entity.dxftype() == "LINE":

        start = entity.dxf.start
        end = entity.dxf.end

        print(
            f"LINE | "
            f"({start.x:.3f}, {start.y:.3f}) -> "
            f"({end.x:.3f}, {end.y:.3f})"
        )

    elif entity.dxftype() == "CIRCLE":

        center = entity.dxf.center
        radius = entity.dxf.radius

        print(
            f"CIRCLE | "
            f"Center=({center.x:.3f}, {center.y:.3f}) | "
            f"Radius={radius:.3f}"
        )

    elif entity.dxftype() == "ARC":

        center = entity.dxf.center

        print(
            f"ARC | "
            f"Center=({center.x:.3f}, {center.y:.3f}) | "
            f"Radius={entity.dxf.radius:.3f} | "
            f"Start={entity.dxf.start_angle:.3f}° | "
            f"End={entity.dxf.end_angle:.3f}°"
        )


# =========================================================
# 6. 整個 DXF 的 Bounding Box
# =========================================================
print()
print("=" * 70)
print("【6. DXF 整體範圍】")
print("=" * 70)

all_x = []
all_y = []

for entity in msp:

    if entity.dxftype() == "LINE":

        all_x.extend([
            entity.dxf.start.x,
            entity.dxf.end.x
        ])

        all_y.extend([
            entity.dxf.start.y,
            entity.dxf.end.y
        ])

    elif entity.dxftype() == "LWPOLYLINE":

        for p in entity.get_points():
            all_x.append(p[0])
            all_y.append(p[1])

    elif entity.dxftype() in ["CIRCLE", "ARC"]:

        center = entity.dxf.center
        radius = entity.dxf.radius

        all_x.extend([
            center.x - radius,
            center.x + radius
        ])

        all_y.extend([
            center.y - radius,
            center.y + radius
        ])

    elif entity.dxftype() == "INSERT":

        insert = entity.dxf.insert

        all_x.append(insert.x)
        all_y.append(insert.y)


if all_x and all_y:

    min_x = min(all_x)
    max_x = max(all_x)
    min_y = min(all_y)
    max_y = max(all_y)

    width = max_x - min_x
    height = max_y - min_y

    print(f"最小 X：{min_x:.3f}")
    print(f"最大 X：{max_x:.3f}")
    print(f"最小 Y：{min_y:.3f}")
    print(f"最大 Y：{max_y:.3f}")
    print(f"整體寬度：{width:.3f}")
    print(f"整體高度：{height:.3f}")


# =========================================================
# 7. Block 定義統計
# =========================================================
print()
print("=" * 70)
print("【7. DXF Block 定義】")
print("=" * 70)

for block in doc.blocks:

    # 跳過一些 DXF 內部 Block
    if block.name.startswith("*"):
        continue

    entity_types = Counter()

    for entity in block:
        entity_types[entity.dxftype()] += 1

    print(f"\nBlock：{block.name}")
    print(f"Entity 數量：{sum(entity_types.values())}")

    for entity_type, count in entity_types.items():
        print(f"  {entity_type:<20} {count}")


print()
print("=" * 70)
print("分析完成")
print("=" * 70)