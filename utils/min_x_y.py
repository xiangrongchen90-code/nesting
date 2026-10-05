import ezdxf
from ezdxf.entities import LWPolyline



def min_max_coordinates(path,name):
    doc = ezdxf.readfile(path)
    # 找出part的所有點
    point=[]
    part_block = doc.blocks[name]
    for i in part_block:
        if isinstance(i,LWPolyline):
            for x, y, *_ in i.get_points():
                #print(f"x:{x},y:{y}")
                point.append((x,y))
    #讓座標從0,0開始
    min_x = min(i[0] for i in point)
    min_y = min(i[1] for i in point)
    max_x = max(i[0] for i in point)
    max_y = max(i[1] for i in point)
    return min_x,min_y,max_x,max_y

import ezdxf

#計算樣片有經過旋轉的外接矩形
def get_rotated_bbox(insert_entity):

    xs = []
    ys = []

    for v in insert_entity.virtual_entities():

        if hasattr(v, "get_points"):
            pts = v.get_points()
        elif hasattr(v, "points"):
            pts = v.points()
        else:
            continue

        for p in pts:
            x, y = p[0], p[1]
            xs.append(x)
            ys.append(y)

    return min(xs), min(ys), max(xs), max(ys)
#找所有parts中最小的x、y座標
def all_parts_min_max(parts_path,parts_Name):
    all_parts_min_x = float('inf')
    all_parts_min_y = float('inf')
    all_parts_max_x = float('-inf')
    all_parts_max_y = float('-inf')
    #各part的y要移多少(因為要對其左上)
    parts_max_y_point=[]
    for i in range(len(parts_path)):
        temporary_minx,temporary_miny,temporary_maxx,temporary_maxy = min_max_coordinates(parts_path[i], parts_Name[i])
        parts_max_y_point.append(temporary_maxy)
        if temporary_minx < all_parts_min_x:
            all_parts_min_x = temporary_minx
        if temporary_miny < all_parts_min_y:
            all_parts_min_y = temporary_miny
        if all_parts_max_x < temporary_maxx:
            all_parts_max_x = temporary_maxx
        if all_parts_max_y < temporary_maxy:
            all_parts_max_y = temporary_maxy
    return all_parts_min_x,all_parts_min_y,all_parts_max_x,all_parts_max_y,parts_max_y_point