import ezdxf
from ezdxf.entities import LWPolyline
from ezdxf import bbox
from ezdxf.math import Matrix44
import os
import numpy as np

# 如果該DXF檔的板材寬大於高就把它旋轉90度，總之就是要保持高大於寬
def rotate_leather_dxf_if_needed(dxf_path):

    doc = ezdxf.readfile(dxf_path)
    msp = doc.modelspace()

    # 取得目前 DXF 的範圍
    min_x, max_x, min_y, max_y = leather_width_height(doc, msp)

    width = max_x - min_x
    height = max_y - min_y

    print(f"原始板材寬度：{width}")
    print(f"原始板材高度：{height}")

    # 寬度沒有大於高度，不需要旋轉
    if width <= height:
        print("✅ 板材方向正確，不需要旋轉")
        return dxf_path, False

    print("⚠️ 板材寬度大於高度，旋轉 90 度")

    # 逆時針旋轉 90 度
    rotation_matrix = Matrix44.z_rotate(-np.pi / 2)

    for entity in msp:
        try:
            entity.transform(rotation_matrix)
        except Exception as e:
            print(f"⚠️ 無法旋轉 entity：{entity.dxftype()}，原因：{e}")

    # 旋轉後重新取得範圍
    min_x, max_x, min_y, max_y = leather_width_height(doc, msp)

    print(
        f"旋轉後範圍："
        f"min_x={min_x}, max_x={max_x}, "
        f"min_y={min_y}, max_y={max_y}"
    )

    # 將旋轉後的 DXF 平移回正座標
    move_x = -min_x
    move_y = -min_y

    translation_matrix = Matrix44.translate(
        move_x,
        move_y,
        0
    )

    for entity in msp:
        try:
            entity.transform(translation_matrix)
        except Exception as e:
            print(f"⚠️ 無法平移 entity：{entity.dxftype()}，原因：{e}")

    # 另外建立一個旋轉後的檔案
    rotated_path = os.path.splitext(dxf_path)[0] + "_rotated.dxf"

    doc.saveas(rotated_path)

    print(f"✅ 已建立旋轉後板材：{rotated_path}")

    # 再確認一次
    check_doc = ezdxf.readfile(rotated_path)
    check_msp = check_doc.modelspace()

    new_min_x, new_max_x, new_min_y, new_max_y = \
        leather_width_height(check_doc, check_msp)

    new_width = new_max_x - new_min_x
    new_height = new_max_y - new_min_y

    print(f"旋轉後寬度：{new_width}")
    print(f"旋轉後高度：{new_height}")

    return rotated_path, True
# 畫出leather的外接矩形
def leather_width_height(doc, msp):

    minx = float('inf')
    maxx = float('-inf')
    miny = float('inf')
    maxy = float('-inf')
    for entity in msp:
        # LWPOLYLINE
        if entity.dxftype() == "LWPOLYLINE":
            for x, y, *_ in entity.get_points():
                minx = min(minx, x)
                maxx = max(maxx, x)
                miny = min(miny, y)
                maxy = max(maxy, y)

        # POLYLINE
        elif entity.dxftype() == "POLYLINE":
            for v in entity.vertices:
                x, y, _ = v.dxf.location
                minx = min(minx, x)
                maxx = max(maxx, x)
                miny = min(miny, y)
                maxy = max(maxy, y)
    return minx, maxx, miny, maxy

#畫出parts的外接矩形
def part_width_height(path, name):
    doc = ezdxf.readfile(path)
    msp = doc.modelspace()

    ext = bbox.extents(msp)

    minx = ext.extmin.x
    miny = ext.extmin.y
    maxx = ext.extmax.x
    maxy = ext.extmax.y

    print(f"{name}最大寬度:{maxx-minx},最大高度:{maxy-miny}")

    return maxx-minx, maxy-miny, minx, maxy
# def part_width_height(path,name):
#     doc = ezdxf.readfile(path)
#     msp = doc.modelspace()
#     for insert in msp.query(f'INSERT[name=="{name}"]'):
#         block = doc.blocks[name]
#         insert_x, insert_y = insert.dxf.insert.x, insert.dxf.insert.y
#         minx = float('inf')
#         maxx = float('-inf')
#         miny = float('inf')
#         maxy = float('-inf')
#         for entity in block:
#             if isinstance(entity, LWPolyline):
#                 for point in entity.get_points():
#                     x = point[0] + insert_x
#                     y = point[1] + insert_y
#                     minx = min(minx,x)
#                     maxx = max(maxx,x)
#                     miny = min(miny, y)
#                     maxy = max(maxy, y)
#         print(f"{name}最大寬度:{maxx-minx},最大高度:{maxy-miny}")
#         return maxx-minx,maxy-miny,minx,maxy
#畫出parts的minxy、maxxy
def part_minxy_maxxy(path, name):
    doc = ezdxf.readfile(path)

    minx = float('inf')
    maxx = float('-inf')
    miny = float('inf')
    maxy = float('-inf')

    # ===== 舊格式：從 Block 讀 =====
    if name and name in doc.blocks:
        entities = doc.blocks[name]
    # ===== 新格式：直接從 ModelSpace 讀 =====
    else:
        entities = doc.modelspace()

    def update_point(x, y):
        nonlocal minx, maxx, miny, maxy
        minx = min(minx, x)
        maxx = max(maxx, x)
        miny = min(miny, y)
        maxy = max(maxy, y)

    for entity in entities:

        # LWPOLYLINE
        if entity.dxftype() == "LWPOLYLINE":
            for x, y, *_ in entity.get_points():
                update_point(x, y)

        # POLYLINE
        elif entity.dxftype() == "POLYLINE":
            for v in entity.vertices:
                update_point(
                    v.dxf.location.x,
                    v.dxf.location.y
                )

        # 舊資料可能是 INSERT
        elif entity.dxftype() == "INSERT":
            for sub in entity.virtual_entities():

                if sub.dxftype() == "LWPOLYLINE":
                    for x, y, *_ in sub.get_points():
                        update_point(x, y)

                elif sub.dxftype() == "POLYLINE":
                    for v in sub.vertices:
                        update_point(
                            v.dxf.location.x,
                            v.dxf.location.y
                        )

    # 防呆
    if minx == float('inf'):
        raise ValueError(
            f"找不到任何輪廓資料: {path}"
        )

    return minx, miny, maxx, maxy
# def part_minxy_maxxy(path, name):
#     doc = ezdxf.readfile(path)
#     block = doc.blocks[name]
#
#     minx = float('inf')
#     maxx = float('-inf')
#     miny = float('inf')
#     maxy = float('-inf')
#
#     for entity in block:
#         if isinstance(entity, LWPolyline):
#             for x, y, *_ in entity.get_points():
#                 minx = min(minx, x)
#                 maxx = max(maxx, x)
#                 miny = min(miny, y)
#                 maxy = max(maxy, y)
#
#     return minx, miny, maxx, maxy
