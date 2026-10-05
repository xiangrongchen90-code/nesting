import numpy as np
import math
from utils.min_x_y import min_max_coordinates
from scipy.ndimage import binary_dilation

#旋轉part的0度陣列
def part_arr_rotate(part, angle_deg):
    #print("原面積", np.sum(part == 0))
    #把角度轉弧度
    angle = math.radians(angle_deg)
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)

    h, w = part.shape

    # 以陣列中心為旋轉中心
    cx = w / 2
    cy = h / 2

    # 四個角旋轉後的新位置(左下、右下、左上、右上)
    corners = [
        (0 - cx, 0 - cy),
        (w - cx, 0 - cy),
        (0 - cx, h - cy),
        (w - cx, h - cy),
    ]
    # 四個角旋轉後的新位置
    rot_corners = []
    for x, y in corners:
        rx =  cos_a*x - sin_a*y
        ry =  sin_a*x + cos_a*y
        rot_corners.append((rx, ry))

    xs = [p[0] for p in rot_corners]
    ys = [p[1] for p in rot_corners]

    #算新的長寬
    new_w = int(max(xs) - min(xs)) + 1
    new_h = int(max(ys) - min(ys)) + 1

    # 建立旋轉後的空陣列（全部背景 1）
    rotated = np.ones((new_h, new_w), dtype = part.dtype)

    # 新中心
    ncx = new_w / 2
    ncy = new_h / 2

    # 映射填值
    for ny in range(new_h):
        for nx in range(new_w):

            # 反向旋轉回去
            x = (nx - ncx)
            y = (ny - ncy)

            ox =  cos_a*x + sin_a*y + cx
            oy = -sin_a*x + cos_a*y + cy

            ox = int(round(ox))
            oy = int(round(oy))

            # 在原圖內 → 填原本的值
            if 0 <= ox < w and 0 <= oy < h:
                rotated[ny, nx] = part[oy, ox]

    # mask = (rotated == 0)
    # mask = binary_dilation(mask)
    # rotated = np.where(mask, 0, 1)
    # rotated = crop_zero_region(rotated)
    rotated= crop_zero_region(rotated)
    #rotated = part_y_move(rotated,max_y)
    # print(f"旋轉{angle_deg}後面積", np.sum(rotated == 0))
    # quit()
    return rotated
    #return rotated,ncx*0.2,ncy*0.2
    #return rotated,math.floor(ncx*0.2),math.floor(ncy*0.2)

#裁出旋轉完成後的最小陣列
def crop_zero_region(arr):

    # 找出所有 0 的座標
    zero_positions = np.where(arr == 0)

    # 若沒有 0，直接回傳 None
    if len(zero_positions[0]) == 0:
        return None

    # 計算 bounding box
    min_row = np.min(zero_positions[0])
    max_row = np.max(zero_positions[0])
    min_col = np.min(zero_positions[1])
    max_col = np.max(zero_positions[1])

    # 裁出這塊區域
    cropped = arr[min_row:max_row+1, min_col:max_col+1]

    return cropped

#因有旋轉過所以要再找一次
def part_y_move(rotated,max_y):
    h, w = rotated.shape
    math.ceil(max_y/0.8)-h
    y_move = math.ceil(max_y/0.8)-h
    if y_move>=0:
        pad = np.ones((y_move, len(rotated[0])))
        rotated = np.vstack((pad, rotated))
    else:
        pad = np.ones((-y_move, len(rotated[0])))
        rotated = np.vstack((rotated,pad))
    return rotated
