import os
import ezdxf
from ezdxf.math import Vec3
from utils.min_x_y import min_max_coordinates,get_rotated_bbox
from ezdxf.addons import importer

#複製leather
def copy_all_entities_to_dxf(source_path,output_path, offset=(0, 0)):
    source_doc = ezdxf.readfile(source_path)
    source_msp = source_doc.modelspace()

    if os.path.exists(output_path):
        new_doc = ezdxf.readfile(output_path)
        print(f"🔄 讀取已存在的 {output_path} 以進行追加")
    else:
        new_doc = ezdxf.new()
        print(f"🆕 建立新的 {output_path}")

    new_msp = new_doc.modelspace()
    existing_blocks = set(block.name for block in new_doc.blocks)
    supported_types = {"INSERT", "POINT", "LWPOLYLINE","POLYLINE"}

    for entity in source_msp:
        entity_type = entity.dxftype()
        if entity_type not in supported_types:
            continue

        if entity_type == "INSERT":
            block_name = entity.dxf.name
            if block_name not in existing_blocks and block_name in source_doc.blocks:
                source_block = source_doc.blocks[block_name]
                new_block = new_doc.blocks.new(name=block_name)
                for e in source_block:
                    new_block.add_entity(e.copy())
                existing_blocks.add(block_name)

            insert_copy = entity.copy()
            old_point = insert_copy.dxf.insert
            insert_copy.dxf.insert = (
                old_point[0] + offset[0],
                old_point[1] + offset[1],
                old_point[2]
            )
            new_msp.add_entity(insert_copy)

        elif entity_type == "POINT":
            point_copy = entity.copy()
            old_point = point_copy.dxf.location
            point_copy.dxf.location = (
                old_point[0] + offset[0],
                old_point[1] + offset[1],
                old_point[2]
            )
            new_msp.add_entity(point_copy)

        elif entity_type == "LWPOLYLINE":
            lw_copy = entity.copy()
            points = [
                (x + offset[0], y + offset[1], *rest)
                for (x, y, *rest) in lw_copy.get_points()
            ]
            lw_copy.clear()
            lw_copy.append_points(points)
            new_msp.add_entity(lw_copy)

        elif entity_type == "POLYLINE":
            pl_copy = entity.copy()
            for v in pl_copy.vertices:
                x, y, z = v.dxf.location
                v.dxf.location = (
                    x + offset[0],
                    y + offset[1],
                    z
                )
            new_msp.add_entity(pl_copy)
    new_doc.saveas(output_path)
    print("leather匯入完成")
def get_leather_polylines(doc):

    plines = []
    msp = doc.modelspace()

    for e in msp:

        # =====================================
        # 1. ModelSpace 直接存在的 Polyline
        # =====================================
        if e.dxftype() in ("LWPOLYLINE", "POLYLINE"):

            plines.append(e.copy())

        # =====================================
        # 2. INSERT / Block
        # =====================================
        elif e.dxftype() == "INSERT":

            for sub in e.virtual_entities():

                if sub.dxftype() in (
                    "LWPOLYLINE",
                    "POLYLINE"
                ):

                    plines.append(sub.copy())

    # =====================================
    # 顯示分析結果
    # =====================================
    print("\n==============================")
    print("Leather DXF 分析")
    print("==============================")

    print("總 Polyline 數量：", len(plines))

    layer_count = {}

    for p in plines:

        layer = p.dxf.layer

        if layer not in layer_count:
            layer_count[layer] = 0

        layer_count[layer] += 1

    print("\nLayer 統計：")

    for layer, count in layer_count.items():

        print(
            f"  Layer {layer} : "
            f"{count} 個"
        )

    print("==============================\n")

    return plines


# ==========================================
# Leather DXF Cache
# ==========================================

leather_doc_cache = {}
leather_pline_cache = {}


# ==========================================
# 讀取所有 Leather DXF
# ==========================================

def preload_leather(leather_paths):

    for lp in leather_paths:

        print(f"讀取 leather：{lp}")

        # -------------------------------
        # 讀取 DXF
        # -------------------------------
        doc = ezdxf.readfile(lp)

        leather_doc_cache[lp] = doc

        # -------------------------------
        # 取得所有 Polyline
        # -------------------------------
        plines = get_leather_polylines(doc)

        leather_pline_cache[lp] = plines

        print(
            f"完成：{lp} "
            f"→ {len(plines)} 個 Polyline"
        )

    print("\n✔ 所有 leather 已完成快取功能")
def get_polyline_points(pline):

    if pline.dxftype() == "LWPOLYLINE":

        return [
            (x, y)
            for x, y, *_ in pline.get_points()
        ]

    elif pline.dxftype() == "POLYLINE":

        return [
            (
                v.dxf.location.x,
                v.dxf.location.y
            )
            for v in pline.vertices
        ]

    else:
        return []
# def get_leather_polylines(doc):
#     plines = []
#     msp = doc.modelspace()
#
#     for e in msp:
#         # 直接的 polyline
#         if e.dxftype() in ("LWPOLYLINE", "POLYLINE"):
#             plines.append(e.copy())
#
#         # INSERT → 展開 virtual_entities()
#         elif e.dxftype() == "INSERT":
#             for sub in e.virtual_entities():
#                 if sub.dxftype() in ("LWPOLYLINE", "POLYLINE"):
#                     plines.append(sub.copy())
#
#     return plines
# leather_doc_cache = {}
# leather_pline_cache = {}
# #讀取所有leather的DXF
# def preload_leather(leather_paths):
#     for lp in leather_paths:
#         doc = ezdxf.readfile(lp)
#         leather_doc_cache[lp] = doc
#
#         plines = get_leather_polylines(doc)
#         leather_pline_cache[lp] = plines
#
#     print("所有 leather 已完成快取功能")
def get_part_polylines(doc, part_name):

    plines = []

    # 先抓 ModelSpace
    for e in doc.modelspace():

        if e.dxftype() in ("LWPOLYLINE", "POLYLINE"):
            plines.append(e.copy())

        elif e.dxftype() == "INSERT":
            for sub in e.virtual_entities():

                if sub.dxftype() in ("LWPOLYLINE", "POLYLINE"):
                    plines.append(sub.copy())

    return plines
# def get_part_polylines(doc, part_name):
#
#     plines = []
#     block = doc.blocks[part_name]
#
#     for e in block:
#         if e.dxftype() in ("LWPOLYLINE", "POLYLINE"):
#             plines.append(e.copy())
#         elif e.dxftype() == "INSERT":
#             for sub in e.virtual_entities():
#                 if sub.dxftype() in ("LWPOLYLINE", "POLYLINE"):
#                     plines.append(sub.copy())
#     return plines

#取所有leather的框
def get_sorted_polylines(plines):
    closed_plines = []

    for pl in plines:
        if (
                (pl.dxftype() == "LWPOLYLINE" and pl.closed) or
                (pl.dxftype() == "POLYLINE" and pl.is_closed)
        ):
            if pl.dxftype() == "LWPOLYLINE":
                count = len(pl.get_points())
            elif pl.dxftype() == "POLYLINE":
                count = len(pl.vertices)
            else:
                continue

            closed_plines.append((count, pl))

    closed_plines.sort(key=lambda x: x[0], reverse=True)

    return closed_plines




parts_doc_cache = {}
parts_pline_cache = {}
#讀取所有part的DXF（一次）
def preload_parts(parts_path, parts_Name):

    for p, name in zip(parts_path, parts_Name):
        doc = ezdxf.readfile(p)
        parts_doc_cache[p] = doc

        plines = get_part_polylines(doc, name)
        parts_pline_cache[p] = plines

    print("✔ preload_parts 完成，所有 part 已快取")

#建立block
def build_test_block(doc, parts_path):
    if "test" in doc.blocks:
        print("✔ test block 已存在")
        return

    print("🛠 建立 test block ...")

    test_block = doc.blocks.new("test")

    # 用第一個 part 的 polyline 當測試形狀
    first_path = parts_path[0]
    for pl in parts_pline_cache[first_path]:
        test_block.add_entity(pl.copy())

    print("✔ test block 建立完成")

def build_part_blocks(doc, parts_path, parts_name, color):
    for idx, (p, name) in enumerate(zip(parts_path, parts_name)):

        if name in doc.blocks:
            print(f"✔ block {name} 已存在")
            continue

        print(f"🛠 建立正式 block：{name}")
        block = doc.blocks.new(name)

        for pl in parts_pline_cache[p]:
            new_pl = pl.copy()
            new_pl.dxf.color = color[idx]
            block.add_entity(new_pl)

    print("✔ 所有正式 block 建立完成！")


#將parts移到leather中
def copy_part_in_leather(doc, msp,
                         offset=(0, 0), new_block_name=None,
                         color=1,rotate_angle=0, cx=0, cy=0):

    #blockref 放在中心點（旋轉中心）
    insert = msp.add_blockref(new_block_name, (cx, cy))
    insert.dxf.color = color

    print(f"cx={cx}, cy={cy}")


    # 旋轉（以插入點為中心）
    insert.dxf.rotation = rotate_angle

    # 計算旋轉後外接矩形
    min_x, min_y, max_x, max_y = get_rotated_bbox(insert)


    # 左上角 (min_x, max_y) 對齊 offset
    dx = offset[0] - min_x
    dy = offset[1] - max_y

    #最終移動
    insert.dxf.insert = Vec3(cx + dx, cy + dy, 0)

    #上下翻轉
    # insert.dxf.xscale = 1
    # insert.dxf.yscale = -1

    print(f"匯入完成：{new_block_name}（旋轉：{rotate_angle}°）")



