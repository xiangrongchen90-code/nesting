import ezdxf
from ezdxf.entities import LWPolyline
import numpy as np
import math
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import time
from utils.min_x_y import min_max_coordinates
from utils.arr_rotate import part_arr_rotate
from utils.add_parts_leather import get_leather_polylines,parts_pline_cache,leather_pline_cache,get_sorted_polylines,get_polyline_points

from utils.bounding_rectangle import leather_width_height
from scipy.ndimage import binary_dilation

#將part影像化，part的範圍填0，背景是1
# def part_digitization(path=None, min_x=0, min_y=0, max_x=0, max_y=0):
#
#     size = 0.8
#
#     # 取出該 part 的所有 polyline
#     plines = parts_pline_cache[path]
#
#     # --------------------------------------------------
#     # 建立陣列
#     # --------------------------------------------------
#     col = math.floor((max_x - min_x) / size) + 1
#     row = math.ceil((max_y - min_y) / size) + 1
#
#     print(f"col:{col}，row:{row}")
#
#     arr = np.ones((row, col))
#
#     # --------------------------------------------------
#     # 每一條 POLYLINE 分開處理
#     # --------------------------------------------------
#     for pline in plines:
#
#         point = []
#
#         # 取得這一條 POLYLINE 的所有點
#         if pline.dxftype() == "LWPOLYLINE":
#
#             for x, y, *_ in pline.get_points():
#                 point.append((
#                     x - min_x,
#                     y - min_y
#                 ))
#
#         elif pline.dxftype() == "POLYLINE":
#
#             for v in pline.vertices:
#                 point.append((
#                     v.dxf.location.x - min_x,
#                     v.dxf.location.y - min_y
#                 ))
#
#         # 沒有點就跳過
#         if len(point) < 3:
#             continue
#
#         # --------------------------------------------------
#         # 對這一條 POLYLINE 做掃描線填充
#         # --------------------------------------------------
#         for y in range(row):
#
#             x_cross = []
#
#             y_real = y * size
#
#             for k in range(len(point)):
#
#                 x1, y1 = point[k]
#                 x2, y2 = point[(k + 1) % len(point)]
#
#                 # 水平線跳過
#                 if y1 == y2:
#                     continue
#
#                 # 判斷掃描線是否穿過這條邊
#                 if (y1 >= y_real) != (y2 >= y_real):
#
#                     x_cross1 = (
#                         x1
#                         + (y_real - y1)
#                         * (x2 - x1)
#                         / (y2 - y1)
#                     )
#
#                     x_cross.append(x_cross1)
#
#             x_cross.sort()
#
#             # --------------------------------------------------
#             # 兩兩配對
#             # --------------------------------------------------
#             for i in range(0, len(x_cross), 2):
#
#                 if i + 1 >= len(x_cross):
#                     continue
#
#                 x_start = x_cross[i]
#                 x_end = x_cross[i + 1]
#
#                 x1_idx = math.floor(x_start / size)
#                 x2_idx = math.ceil(x_end / size)
#
#                 # 防止超出陣列
#                 x1_idx = max(0, x1_idx)
#                 x2_idx = min(col, x2_idx)
#
#                 if x2_idx > x1_idx:
#                     arr[y, x1_idx:x2_idx] = 0
#
#     # --------------------------------------------------
#     # 上下翻轉
#     # --------------------------------------------------
#     arr = np.flipud(arr)
#
#     # --------------------------------------------------
#     # 計算面積
#     # --------------------------------------------------
#     part_area = np.sum(arr == 0)
#
#     return arr, part_area
def part_digitization(path=None,min_x=0,min_y=0,max_x=0,max_y=0):

    #star_time=time.time()
    #設定1格長寬
    size = 0.8
    # 取出該part的所有polyline
    plines = parts_pline_cache[path]
    # 找出part的所有點
    point = []
    for i in plines:
        if i.dxftype() == "LWPOLYLINE":
            for x, y, *_ in i.get_points():
                point.append((x, y))

        elif i.dxftype() == "POLYLINE":
            for v in i.vertices:
                point.append((
                    v.dxf.location.x,
                    v.dxf.location.y
                ))
    # print(point)

    # 讓座標從0,0開始
    point = [(x-min_x,y-min_y) for (x,y) in point]

    # 設一個跟part一樣大的陣列名為arr，一格大小 = size*size(0.8*0.8)
    col = math.floor((max_x-min_x)/size)+1
    row = math.ceil((max_y-min_y)/size)+1
    print(f"col:{col}，row:{row}")
    arr = np.ones((row, col))  # [y, x] 結構，裡面全填1
    #print(arr.shape)

    # 填充parts進去(part的部分填0)
    for y in range(row):
        # 儲存掃描線和邊界的交點
        x_cross = []
        # 目前掃描線在arr中的真實位置
        y_real = y * size
        for k in range(len(point)):
            # 點1
            x1, y1 = point[k]
            # 點1的下個點
            x2, y2 = point[(k + 1) % len(point)]
            #水平線不處理
            if y1 == y2:
                continue
            # 是否一個點在掃描線上，一個點在下
            if (y1 >= y_real) != (y2 >= y_real):
                # 求那兩點連成的線與掃描線的交點
                x_cross1 = x1 + (y_real - y1) * (x2 - x1) / (y2 - y1)
                x_cross.append(x_cross1)
        x_cross.sort()
        # 兩兩成對處理
        for i in range(0, len(x_cross), 2):
            if i + 1 < len(x_cross):  # 避免超出範圍
                x_start = x_cross[i]
                x_end = x_cross[i + 1]
                # 把座標轉成索引
                x1_idx = math.floor(x_start / size)
                #x2_idx = math.floor(x_end / size)
                x2_idx = math.ceil(x_end / size)
                # 將這段之間的格子填 0
                arr[y, x1_idx:x2_idx] = 0
    # 上下翻轉
    arr = np.flipud(arr)
    # 多加一圈避免碰撞
    # mask = (arr == 0)
    # mask = binary_dilation(mask)
    # arr = np.where(mask, 0, 1)
    # 算面積
    part_area = np.sum(arr== 0)

    return arr,part_area


# def leather_digitization(
#         path=None,
#         min_x=0,
#         min_y=0,
#         max_x=0,
#         max_y=0):
#
#     # --------------------------------------
#     # 每一格 = 0.8 mm
#     # --------------------------------------
#     size = 0.8
#
#     # --------------------------------------
#     # 取得板材所有 Polyline
#     # --------------------------------------
#     plines = leather_pline_cache[path]
#
#     print("\n==============================")
#     print("開始板材影像化")
#     print("DXF：", path)
#     print("Polyline 數量：", len(plines))
#     print("==============================")
#
#     # --------------------------------------
#     # 依面積排序
#     # 最大的 = 外框
#     # 其他的 = 洞 / 瑕疵區域
#     # --------------------------------------
#     all_plines = get_sorted_polylines(plines)
#
#     if not all_plines:
#         raise ValueError(
#             f"板材 {path} 沒有找到任何有效 POLYLINE"
#         )
#
#     outline = all_plines[0][1]
#
#     holes = [
#         pline
#         for _, pline in all_plines[1:]
#     ]
#
#     print("外框：", outline.dxftype())
#     print("洞數量：", len(holes))
#
#     # --------------------------------------
#     # Raster 大小
#     # --------------------------------------
#     col = math.floor(
#         (max_x - min_x) / size
#     ) + 1
#
#     row = math.ceil(
#         (max_y - min_y) / size
#     ) + 1
#
#     print("col =", col)
#     print("row =", row)
#
#     # --------------------------------------
#     # 預設全部不可排樣
#     # 1 = 不可排樣
#     # --------------------------------------
#     arr = np.ones(
#         (row, col),
#         dtype=np.uint8
#     )
#
#     # ======================================
#     # 掃描線填充函式
#     # ======================================
#     def fill_polygon(arr, point_list, value):
#
#         if len(point_list) < 3:
#             return
#
#         # ----------------------------------
#         # 將座標平移到 (0,0)
#         # ----------------------------------
#         pts = [
#             (
#                 x - min_x,
#                 y - min_y
#             )
#             for x, y in point_list
#         ]
#
#         # ----------------------------------
#         # 逐列掃描
#         # ----------------------------------
#         for y_idx in range(row):
#
#             y_real = y_idx * size
#
#             x_cross = []
#
#             # ------------------------------
#             # 找掃描線與邊界交點
#             # ------------------------------
#             for i in range(len(pts)):
#
#                 x1, y1 = pts[i - 1]
#                 x2, y2 = pts[i]
#
#                 # 水平線跳過
#                 if y1 == y2:
#                     continue
#
#                 # 掃描線是否穿過這條邊
#                 if (y1 >= y_real) != (y2 >= y_real):
#
#                     x_int = (
#                         x1
#                         + (y_real - y1)
#                         * (x2 - x1)
#                         / (y2 - y1)
#                     )
#
#                     x_cross.append(x_int)
#
#             # ------------------------------
#             # 排序
#             # ------------------------------
#             x_cross.sort()
#
#             # ------------------------------
#             # 兩兩配對填滿
#             # ------------------------------
#             for i in range(
#                 0,
#                 len(x_cross),
#                 2
#             ):
#
#                 if i + 1 >= len(x_cross):
#                     continue
#
#                 x_start = x_cross[i]
#                 x_end = x_cross[i + 1]
#
#                 # 轉換成陣列 index
#                 x1_idx = max(
#                     0,
#                     math.floor(
#                         x_start / size
#                     )
#                 )
#
#                 x2_idx = min(
#                     col,
#                     math.ceil(
#                         x_end / size
#                     )
#                 )
#
#                 if x2_idx > x1_idx:
#
#                     arr[
#                         y_idx,
#                         x1_idx:x2_idx
#                     ] = value
#
#     # ======================================
#     # 1. 處理外框
#     # ======================================
#
#     outline_pts = get_polyline_points(outline)
#
#     if len(outline_pts) < 3:
#
#         raise ValueError(
#             "板材外框沒有足夠的座標點"
#         )
#
#     print(
#         "外框點數：",
#         len(outline_pts)
#     )
#
#     # 外框 = 0
#     # 代表可排樣
#     fill_polygon(
#         arr,
#         outline_pts,
#         0
#     )
#
#     # ======================================
#     # 2. 處理洞 / 瑕疵區域
#     # ======================================
#
#     for idx, hole in enumerate(holes):
#
#         pts = get_polyline_points(hole)
#
#         if len(pts) < 3:
#             # print(
#             #     f"洞 #{idx + 1} "
#             #     f"點數不足，跳過"
#             # )
#
#             continue
#
#         # print(
#         #     f"洞 #{idx + 1}："
#         #     f"{len(pts)} points"
#         # )
#
#         fill_polygon(
#             arr,
#             pts,
#             1
#         )
#
#     # ======================================
#     # 3. 上下翻轉
#     # ======================================
#
#     arr = np.flipud(arr)
#
#     # ======================================
#     # 4. 計算可排樣面積
#     # ======================================
#
#     leather_area = np.sum(
#         arr == 0
#     )
#
#     print(
#         "可排樣格數：",
#         leather_area
#     )
#
#     print(
#         "板材影像化完成"
#     )
#
#     print("==============================\n")
#
#     return arr, leather_area
#板材的影像化，0是可排樣，1是不可排樣
def leather_digitization(path=None,min_x=0,min_y=0,max_x=0,max_y=0):
    size = 0.8

    plines = leather_pline_cache[path]
    all_plines = get_sorted_polylines(plines)

    # Layer 0 = 板材外框
    layer_0_plines = [
        pl for _, pl in all_plines
        if pl.dxf.layer == "0"
    ]

    # Layer 9 = 內部不可排區域
    holes = [
        pl for _, pl in all_plines
        if pl.dxf.layer == "9"
    ]

    if len(layer_0_plines) != 1:
        raise ValueError(
            f"預期找到 1 個 Layer 0 外框，實際找到 {len(layer_0_plines)} 個"
        )

    outline = layer_0_plines[0]
    # plines = leather_pline_cache[path]
    # all_plines = get_sorted_polylines(plines)
    #
    # outline = all_plines[0][1]          # 最大外框
    # holes = [pl for _, pl in all_plines[1:]]   # 其他全部是洞

    # raster 大小
    col = math.floor((max_x - min_x) / size) + 1
    row = math.ceil((max_y - min_y) / size) + 1
    arr = np.ones((row, col))   # 預設背景 = 1（不可排料）

    #  填外框（填 0）
    def fill_polygon(arr, point_list, value):
        # 把皮料點平移到 (0,0)
        pts = [(x - min_x, y - min_y) for (x, y) in point_list]

        for y_idx in range(row):
            y_real = y_idx * size
            x_cross = []

            for i in range(len(pts)):
                x1, y1 = pts[i - 1]
                x2, y2 = pts[i]

                if y1 == y2:
                    continue
                if (y1 >= y_real) != (y2 >= y_real):
                    x_int = x1 + (y_real - y1) * (x2 - x1) / (y2 - y1)
                    x_cross.append(x_int)

            x_cross.sort()

            for i in range(0, len(x_cross), 2):
                if i + 1 >= len(x_cross):
                    continue

                x1_idx = math.floor(x_cross[i] / size)
                x2_idx = math.ceil(x_cross[i + 1] / size)

                if x2_idx > x1_idx:
                    arr[y_idx, x1_idx:x2_idx] = value

    # 外框：填 0（可排料）
    if outline.dxftype() == "LWPOLYLINE":
        outline_pts = [(x, y) for x, y, *_ in outline.get_points()]
    elif outline.dxftype() == "POLYLINE":
        outline_pts = [(v.dxf.location.x, v.dxf.location.y) for v in outline.vertices]
    else:
        raise TypeError(f"不支援的 outline 型別: {outline.dxftype()}")
    # print("========== Leather Digitization Debug ==========")
    # print("outline type:", outline.dxftype())
    # print("outline 點數:", len(outline_pts))
    # print("outline 前5點:", outline_pts[:5])
    # print("min_x, max_x:", min_x, max_x)
    # print("min_y, max_y:", min_y, max_y)
    # print("row, col:", row, col)
    # print("===============================================")
    fill_polygon(arr, outline_pts, 0)
    #print("填外框後 0 數量:", np.sum(arr == 0))
    # print("進入洞之前 0 數量:", np.sum(arr == 0))
    # print("洞的數量:", len(holes))
    # 洞：填 1（不可排料）
    for hole in holes:
        if hole.dxftype() == "LWPOLYLINE":
            pts = [(x, y) for x, y, *_ in hole.get_points()]
        elif hole.dxftype() == "POLYLINE":
            pts = [(v.dxf.location.x, v.dxf.location.y) for v in hole.vertices]
        else:
            continue  # 不支援的型別直接略過
        # 保護：沒有點就不畫
        if len(pts) < 3:
            continue

        fill_polygon(arr, pts, 1)  # 洞 → 填 1（不可排料）
    # for i, (area, pl) in enumerate(all_plines):
    #     print(
    #         i,
    #         "area =", area,
    #         "layer =", pl.dxf.layer,
    #         "closed =", pl.is_closed,
    #         "vertices =", len(list(pl.vertices))
    #     )
    #print("所有洞填完後 0 數量:", np.sum(arr == 0))
    #顯示
    # plt.imshow(arr, cmap='gray', vmin=0, vmax=1)
    # plt.title("leather")
    # plt.show()
    # mask = (arr == 1)
    # mask = binary_dilation(mask)
    # arr = np.where(mask, 1, 0)
    # arr[0, :] = 1
    # arr[-1, :] = 1
    # arr[:, 0] = 1
    # arr[:, -1] = 1
    leather_area = np.sum(arr == 0)

    return np.flipud(arr),leather_area

#算新加入的part要移動多少
def part_and_leather_move(leather, part, order_x, order_y,yn_irregular=0):

    ph, pw = part.shape
    lh, lw = leather.shape
    move_count = 0
    touch_leather_bottom = 0
    leather_full = 0
    leather_change_column = 0
    # 卡住了禁止他往上跑
    ok_up = True

    while True:
        # 卡住了強制右移且不準上移
        if move_count > 80:  # 逃脫機制
            print("⚠️ 偵測到上移邏輯與右移邏輯發生無限迴圈，上移禁止")
            ok_up = False
        move_count += 1
        print(f"該樣片移動第{move_count}次")
        #先往上
        step = 10
        while ok_up:
            leather_top = 0
            # 此時樣片往上會超出皮料，故不宜往上
            if (order_y - (ph//step)) < 0:
                leather_top = 1
                break
            else:
                # 預先將座標往上移動一個零件高度的距離，準備開始逐格檢查
                order_y -= (ph//step)
            if leather_top!=1:
                #print("向上移動")
                sub = leather[order_y:order_y + ph, order_x:order_x + pw]
                # 保險，怕part跟sub大小不一樣
                if sub.shape != part.shape:
                    pad_y = ph - sub.shape[0]
                    pad_x = pw - sub.shape[1]
                    #在右方與下方補1(1-->不可排料)
                    sub = np.pad(sub, ((0, pad_y), (0, pad_x)), mode='constant', constant_values=1)
                overlap = ((sub == 1) & (part == 0)).astype(int)
                one_number_column = np.sum(overlap == 1, axis=0)
                # 如果任一列存在障礙物
                if max(one_number_column)!=0:
                    print("向上移動⬆️")
                    pad_h = max(one_number_column)
                    if pad_h > (ph//step):
                        pad_h = (ph//step)
                    order_y += pad_h
                    #order_y += (pad_h + 2)
                    break
        # 再往右移動
        # 取出子區域（左上對齊）
        sub = leather[order_y:order_y + ph, order_x:order_x + pw]
        # 保險，怕part跟sub大小不一樣
        if sub.shape != part.shape:
            pad_y = ph - sub.shape[0]
            pad_x = pw - sub.shape[1]
            # 在右方與下方補1(1-->不可排料)
            sub = np.pad(sub, ((0, pad_y), (0, pad_x)), mode='constant', constant_values=1)
        # overlap 計算(0-->黑，1-->白)
        overlap = (((sub == 2) | (sub == 1)) & (part == 0)).astype(int)
        # 沒碰撞 → 再往右、往下移動1格作為間距
        if overlap.sum() == 0:
            # 往右、往下移動1格
            order_x += 1
            order_y += 1
            # 重新取得移動後的位置
            sub = leather[order_y:order_y + ph, order_x:order_x + pw]
            # 檢查移動1格後是否發生碰撞
            overlap = (((sub == 2) | (sub == 1)) & (part == 0)).astype(int)
            # 移動1格後仍然沒有碰撞
            if overlap.sum() == 0:
                break
        # 計算往右多少
        one_number_row = np.sum(overlap == 1, axis=1)
        max_row = max(one_number_row) if len(one_number_row) > 0 else 0
        print("向右移動🔜")
        order_x += max(max_row, 1)
        # 如果往右超界
        if order_x + pw > lw:
            # 換行
            #order_y += 20
            order_y += (ph//4)
            #order_y += ph
            order_x = 0
            # 有換行過，上一個樣片有可能出現在現樣片正上方，這樣會無限循環，故將所有值2改成1
            leather[leather == 2] = 1
            # 紀錄有換行過
            # leather_change_column = 1

            # print(f"🐥🐥🐥🐥🐥🐥🐥🐥🐥🐥🐥🐥🐥🐥🐥🐥🐥我是換行")
            #往下也超界代表這張皮料整個都排滿了(ph // 2)
            if order_y + ph > lh:
                touch_leather_bottom = 1
                print("整張皮料已排滿")
                leather_full = 1
                # print(f"😘😘😘😘😘😘😘😘😘😘😘😘😘😘😘😘😘我是結束")
                break

            continue
        if order_x < pw:
            leather_change_column = 1
    return order_x, order_y,touch_leather_bottom,leather_change_column,leather_full

