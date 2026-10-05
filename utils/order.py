from .parts_digitization import part_digitization
from .arr_rotate import part_arr_rotate
from .add_parts_leather import copy_part_in_leather
from .is_part_inside_leather import part_fully_inside_leather,part_in_forbidden_zone,part_fully_inside_leather_star
from .remove_parts import remove_part
import os
import ezdxf
from .bounding_rectangle import part_width_height,leather_width_height
from .min_x_y import min_max_coordinates,all_parts_min_max
from .add_parts_leather import copy_all_entities_to_dxf,copy_part_in_leather,build_part_blocks,build_test_block,preload_parts
import time
import numpy as np
import matplotlib.pyplot as plt

#將part的dxf形式加到dxf形式的leather中
def order_part(doc,msp,population,parts_name,color,x_y_coordinate):
# 開始排
    # 第一個part1
    for j in range(len(population[0]//2)):
        decide = 1
        #排第一個part
        while decide != 0:
            # 排part
            copy_part_in_leather(doc, msp,
                                 offset = (x_y_coordinate[j][0]*0.8, x_y_coordinate[j][1]*0.6),
                                 new_block_name = parts_name[population[0][j]],
                                 color=color[population[0][j]], rotate_angle=population[0][j+len(population[0]//2)])
#算時間的
def timer(tag):
    print(f"{tag} 用時: {time.perf_counter():.6f}")

#將part_arr排入leather_arr
def order_arr(leather, part, x_order, y_order,always_value,part_value=1):

    always_value = int(always_value)
    ph, pw = part.shape
    lh, lw = leather.shape

    # 準備寫入leather
    # 計算實際可寫入範圍（避免溢位）
    h = min(ph, lh - y_order)
    w = min(pw, lw - x_order)
    # 建立一個和leather大小型態都相同的arr，且裡面的值全為0
    mask = np.zeros_like(leather, dtype=leather.dtype)
    # part == 0 才填入，此時part的範圍填入值part_value，2代表剛填入的樣片，1代表以前的
    mask[y_order:y_order+h, x_order:x_order+w] = (part[:h, :w] == 0).astype(leather.dtype)*part_value

    # 計算 fitness
    step = 1
    #上
    y0 = max(0, y_order - always_value)
    y1 = y_order
    x0 = x_order
    x1 = x_order + always_value
    fitness1 = np.sum(leather[y0:y1:step, x0:x1:step] == 0)
    #左
    y0 = y_order
    y1 = y_order + always_value
    x0 = x_order
    x1 = max(0,x_order - always_value)
    #x0 = max(0, x_order - always_value)
    #x1 = x_order
    fitness2 = np.sum(leather[y0:y1:step, x0:x1:step] == 0)
    #左上
    y0 = y_order
    y1 = max(0, y_order + always_value)
    #y0 = max(0, y_order - always_value)  # 上方的邊界
    #y1 = y_order
    x0 = max(0,x_order - always_value)
    x1 = x_order
    fitness3 = np.sum(leather[y0:y1:step, x0:x1:step] == 0)

    fitness = fitness1 + fitness2 + fitness3

    #為了讓有換列的必輸沒換列的(將板材的右邊界盡量利用的方法)
    # if x_order < always_value:
    #     fitness += (always_value * always_value)
    print("leather dtype:", leather.dtype)
    print("mask dtype:", mask.dtype)
    # 轉成int
    leather = leather.astype(np.uint8)
    mask = mask.astype(np.uint8)
    # 寫入leather
    leather |= mask
    #顯示
    # plt.imshow(leather, cmap='gray', vmin=0, vmax=1)
    # plt.title("leather")
    # plt.show()
    return leather, fitness






# ga_number = 1
# v = 1
# pop_len = 1
#
# temp_path = "C:/python/Nike_Nesting_MINZ_DXF-2/output/temp.dxf"
# leather_path = "C:/python/Nike_Nesting_MINZ_DXF-2/leather/leather00_newcolor.dxf"
# # PARTS 檔案路徑
# parts_path = [
#     "C:/python/Nike_Nesting_MINZ_DXF-2/parts/parts00.dxf",
#     "C:/python/Nike_Nesting_MINZ_DXF-2/parts/parts01.dxf",
#     "C:/python/Nike_Nesting_MINZ_DXF-2/parts/parts02.dxf",
#     "C:/python/Nike_Nesting_MINZ_DXF-2/parts/parts03.dxf"
# ]
# parts_name = ["FOXING_IN-9","FOXING_OUT-9","QTR_IN-9","QTR_OUT-9"]
# color = [1, 3, 5, 6]
# # STEP 1：刪掉舊的 temp.dxf
# if os.path.exists(temp_path):
#     os.remove(temp_path)
#
# # STEP 2：用你的函式把 leather 複製到 temp.dxf（不改函式）
# copy_all_entities_to_dxf(leather_path, temp_path)
# # 讀part檔案
# preload_parts(parts_path, parts_name)
# # STEP 3：讀取 temp.dxf → doc 裡面會有 leather
# doc = ezdxf.readfile(temp_path)
# msp = doc.modelspace()
# # 建立所有part的blocks
# build_part_blocks(doc, parts_path, parts_name,color)
# build_test_block(doc, parts_path)
# # GA 的 population
# population = [[0,1,2,3,0,90,180,360]]
#
# # STEP 4：用 doc 取得 leather 的四邊界
# leather_min_x, leather_max_x, leather_min_y, leather_max_y = leather_width_height(doc, msp)
#
#
#
# # 計算 parts 的 bounding box 相關數值
# all_parts_min_x, all_parts_min_y, all_parts_max_x, all_parts_max_y, parts_max_y_point = \
#     all_parts_min_max(parts_path, parts_name)
#
# # STEP 5：算最大高度（for 換列）
# max_height = 0
# for i in range(len(parts_path)):
#     part_length, part_height, part_min_x, part_max_y = part_width_height(parts_path[i], parts_name[i])
#     max_height = max(max_height, part_height)
#
# # PART 顏色
# color = [1, 3, 5, 6]
#
# # STEP 6：開始排樣
# order_part(
#     ga_number, v, pop_len, doc, msp, population,
#     leather_min_x, leather_max_y, parts_path,
#     temp_path, parts_name,
#     all_parts_min_x, all_parts_min_y, all_parts_max_x, all_parts_max_y,
#     parts_max_y_point, leather_max_x, max_height, color
# )
#
# # STEP 7：最後輸出 DXF
# doc.saveas(temp_path)
