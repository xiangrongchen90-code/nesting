import ezdxf
from ezdxf.entities import Spline
from math import hypot

def spline_to_polyline(input_dxf, output_dxf, segment_length=0.1, close=1):
    doc = ezdxf.readfile(input_dxf)
    msp = doc.modelspace()

    splines = [e for e in msp if isinstance(e, Spline)]
    print(f"找到 {len(splines)} 條 SPLINE")

    for spline in splines:
        tool = spline.construction_tool()

        # 1️⃣ 用控制點近似 spline 長度
        ctrl_pts = list(spline.control_points)
        approx_len = 0.0
        for i in range(len(ctrl_pts) - 1):
            x0, y0 = ctrl_pts[i][:2]
            x1, y1 = ctrl_pts[i + 1][:2]
            approx_len += hypot(x1 - x0, y1 - y0)

        # 2️⃣ 算段數（一定是 int）
        segments = max(int(approx_len / segment_length), 20)

        # ✅ 關鍵修正：傳 segments，不是 segment_length
        points = list(tool.approximate(segments))

        if len(points) < 3:
            print("⚠️ spline 點數不足，略過")
            continue

        # 3️⃣ 自動閉合
        x0, y0, *_ = points[0]
        x1, y1, *_ = points[-1]
        if hypot(x1 - x0, y1 - y0) < close:
            points.append(points[0])

        # 4️⃣ 建立 LWPOLYLINE
        msp.add_lwpolyline(
            [(x, y) for x, y, *_ in points],
            close=True
        )

        # 5️⃣ 刪除原 spline
        msp.delete_entity(spline)

    doc.saveas(output_dxf)
    print(f"✅ 已輸出：{output_dxf}")
