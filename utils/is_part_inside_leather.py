from ezdxf.entities import LWPolyline
from shapely.geometry import Polygon, Point,LineString
import math
#新排入的part是否完全在leather裡面
from ezdxf.entities import LWPolyline
from shapely.geometry import Polygon, Point
from ezdxf.math import Vec3


#找min_y與max_y和leather的交點
def slice_polygon_by_y(pts, y_min, y_max):
    new_pts = []
    n = len(pts)

    for i in range(n):
        x1, y1 = pts[i]
        x2, y2 = pts[(i+1) % n]

        # 如果目前點在範圍內，保留
        if y_min <= y1 <= y_max:
            new_pts.append((x1, y1))

        # 處理 y_min 與 y_max 的交點
        for y_cut in (y_min, y_max):
            if (y1 - y_cut) * (y2 - y_cut) < 0:  # 代表有跨過
                # 計算交點
                t = (y_cut - y1) / (y2 - y1)
                x = x1 + t * (x2 - x1)
                new_pts.append((x, y_cut))

    # 切片後的多邊形點數可能 >2，需要排序為環狀
    # 做法：計算 centroid，依角度排序
    if len(new_pts)==0:
        return new_pts

    cx = sum(p[0] for p in new_pts) / len(new_pts)
    cy = sum(p[1] for p in new_pts) / len(new_pts)

    new_pts.sort(key=lambda p: math.atan2(p[1] - cy, p[0] - cx))

    return new_pts
# 新加入的part是否在leather裡面
def part_fully_inside_leather(msp,area_min_y,area_max_y, leather_color_index=None):
    # 找 leather boundary
    leather_polygon = None
    new_pts=[]
    for e in msp:
        if isinstance(e, LWPolyline):
            if leather_color_index is None or e.dxf.color == leather_color_index:
                if e.closed:
                    pts = [(x, y) for x, y, *_ in e.get_points()]
                    new_pts = slice_polygon_by_y(pts, area_min_y, area_max_y)
                    #print("Polygon valid:", leather_polygon.is_valid)
                    #print("Polygon area:", leather_polygon.area)
                    break
    return new_pts
def part_fully_inside_leather_star(msp, part_name, new_pts):
    insert_entity = None
    for ins in msp.query('INSERT'):
        if ins.dxf.name.lower() == part_name.lower():
            insert_entity = ins
            break
    if insert_entity is None:
        #print("❓")
        return False

    leather_polygon = Polygon(new_pts)

    for v in insert_entity.virtual_entities():
        if v.dxftype() == "LWPOLYLINE":
            pts = [(x, y) for x, y, *_ in v.get_points()]
            for px, py in pts:
                if not leather_polygon.contains(Point(px, py)):
                    return False

    return True
#part是否有落到紅色線上或是在紅色線區塊內
def part_in_forbidden_zone(doc, msp, part_name,area_min_y,area_max_y,forbidden_color_index=1):

    insert_entity = None
    for ins in msp.query('INSERT'):
        if ins.dxf.name == part_name:
            insert_entity = ins
            break
    if insert_entity is None:
        return False

    # 取得禁區線
    forbidden_lines = []
    forbidden_polygons = []

    for e in msp.query("LWPOLYLINE"):
        if e.dxf.color == forbidden_color_index:
            pts = [(x, y) for x, y, *_ in e.get_points()]
            result = slice_polygon_by_y(pts, area_min_y, area_max_y)
            if len(result) >= 2:
                forbidden_lines.append(LineString(result))
            if e.closed and len(result) >= 3:
                forbidden_polygons.append(Polygon(result))

    # 取得旋轉後 part 的圖形
    part_lines = []
    part_pts = []

    for v in insert_entity.virtual_entities():
        if v.dxftype() == "LWPOLYLINE":
            pts = [(x, y) for x, y, *_ in v.get_points()]
            part_pts.extend(pts)
            part_lines.append(LineString(pts))

    # 線交叉
    for p in part_lines:
        for f in forbidden_lines:
            if p.intersects(f):
                return True

    # 完全落入禁區
    for poly in forbidden_polygons:
        if all(poly.contains(Point(x, y)) for x, y in part_pts):
            return True

    return False
