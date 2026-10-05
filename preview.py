import sys
import os
import ezdxf
import matplotlib.pyplot as plt
from ezdxf.addons.drawing import Frontend, RenderContext
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend

# 給介面預覽圖的
def dxf_to_png(dxf_path, output_path, dpi=600):
    doc = ezdxf.readfile(dxf_path)

    fig = plt.figure(figsize=(12, 8))
    ax = fig.add_axes([0, 0, 1, 1])
    # 白色背景
    ax.set_axis_off()
    ctx = RenderContext(doc)
    Frontend(
        ctx,
        MatplotlibBackend(ax)
    ).draw_layout(doc.modelspace())
    fig.savefig(
        output_path,
        dpi=dpi,
    )
    plt.close(fig)

if __name__ == "__main__":

    if len(sys.argv) < 4:
        print("參數不足")
        sys.exit()

    preview_type = sys.argv[1]
    file_name = sys.argv[2]
    output_dir = sys.argv[3]

    # preview.py 所在資料夾
    python_dir = os.path.dirname(os.path.abspath(__file__))

    # 專案根目錄（Python 的上一層）
    project_dir = os.path.dirname(python_dir)

    if preview_type == "leather":

        dxf_path = os.path.join(
            python_dir,
            "leather",
            file_name + ".dxf"
        )

        output_path = os.path.join(
            output_dir,
            "leather_preview.png"
        )

    elif preview_type == "part":

        dxf_path = os.path.join(
            python_dir,
            "parts",
            file_name + ".dxf"
        )

        output_path = os.path.join(
            output_dir,
            "part_preview.png"
        )

    else:

        print("未知預覽類型")
        sys.exit()

    dxf_to_png(
        dxf_path,
        output_path
    )
    print("DXF:", dxf_path)
    print("PNG:", output_path)
    print("完成")