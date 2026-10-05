import ezdxf
from ezdxf import bbox
import cv2
import matplotlib.pyplot as plt
from ezdxf.addons.drawing import RenderContext, Frontend
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
import numpy as np

#將dxf轉成png
def change_png(input_path, output_path, dpi=300,dxf_w=0,dxf_h=0):
    #初始設定路徑
    doc = ezdxf.readfile(input_path)
    msp = doc.modelspace()
    # 建立一個圖表 (matplotlib figure)
    fig = plt.figure()
    ax = fig.add_axes([0, 0, 1, 1])  # 塞滿整個畫布
    # 建立繪製上下文 (RenderContext)
    ctx = RenderContext(doc)
    ctx.set_current_layout(msp)
    # 設定背景顏色
    out = MatplotlibBackend(ax)
    out.set_background("#000000")
    # 前端：把 DXF 內容繪製到 matplotlib
    out = MatplotlibBackend(ax)
    Frontend(ctx, out).draw_layout(msp, finalize=True)
    # 輸出成 PNG
    fig.savefig(output_path, dpi=dpi)
    # 計算dxf與png長寬差
    extmin, extmax = bbox.extents(msp)
    img = cv2.imread(output_path)
    png_h, png_w = img.shape[:2]
    #會預留30pixel
    png_h-=60
    png_w-=60
    area_multiple=(dxf_w/png_w)*(dxf_h/png_h)
    return area_multiple
#算leather與parts的面積
def leather_parts_area(png_path,leather_or_parts_value,area_multiple):
    # 讀取圖片
    img = cv2.imread(png_path, cv2.IMREAD_GRAYSCALE)
    # 二值化
    img[(img > 70) | (img==0)] = 255
    img[(img < 255)]=0
    # 二值化結果 (白線 + 背景黑)
    binary = img.copy()
    # 閉運算 (closing)：先膨脹再腐蝕 → 補齊外框
    kernel = np.ones((15, 15), np.uint8)
    closed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
    # 找到所有的輪廓
    contours, hierarchy = cv2.findContours(closed, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
    #算各輪廓面積
    areas = []
    for k in range(len(contours)):
        areas.append(cv2.contourArea(contours[k]))
    #將面積由大小排到大-sort_area裡的是索引值
    sort_area = np.argsort(areas)[::-1]
    # 建立全黑底
    mask = np.zeros_like(img)
    # 將第二大框變白色
    hole_area=0
    cv2.drawContours(mask, contours, sort_area[1], 255, cv2.FILLED)
    #文字部分變白-parts才需要
    if leather_or_parts_value==0:
        cv2.drawContours(mask, contours, sort_area[2], 255, cv2.FILLED)
    #將第二大框裡的都變黑色-leather需要
    if leather_or_parts_value:
        for k in range(len(contours)):
            if hierarchy[0][k][3]==sort_area[1]:
                cv2.drawContours(mask, contours, k, leather_or_parts_value, cv2.FILLED)
                hole_area += areas[k]
    #匯出圖片
    cv2.imwrite(png_path, mask)
    #算像素非黑色的有多少
    white_pixels = cv2.countNonZero(mask)
    print("area:",round(white_pixels*area_multiple))
    return round(white_pixels*area_multiple)
    #print(f"面積:{round(white_pixels*area_multiple)}")
# dxf="C:/python/Nike_Nesting_MINZ_DXF-2/output/temp_3_png.dxf"
# change_png("C:/python/Nike_Nesting_MINZ_DXF-2/output/temp_3_png.dxf", "C:/python/Nike_Nesting_MINZ_DXF-2/output/temp_3_png.png", dpi=300,dxf_w=0,dxf_h=0)
# leather_parts_area("C:/python/Nike_Nesting_MINZ_DXF-2/output/temp_3_png.png",1,1)