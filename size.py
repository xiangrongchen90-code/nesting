import os
import sys
import json
import ezdxf

from utils.bounding_rectangle import (
    leather_width_height,
    part_width_height,
)

if __name__ == "__main__":

    if len(sys.argv) < 3:
        print("參數不足")
        sys.exit()

    file_type = sys.argv[1]
    file_name = sys.argv[2]

    base_dir = os.path.dirname(os.path.abspath(__file__))

    if file_type == "leather":

        dxf_path = os.path.join(
            base_dir,
            "leather",
            file_name + ".dxf"
        )

        doc = ezdxf.readfile(dxf_path)
        msp = doc.modelspace()

        min_x, max_x, min_y, max_y = leather_width_height(doc, msp)

        width = round(max_x - min_x)
        height = round(max_y - min_y)

        result = {
            "width": width,
            "height": height,
            "size": f"{width}*{height}"
        }

        with open(
            os.path.join(base_dir, "size.json"),
            "w",
            encoding="utf-8"
        ) as f:
            json.dump(result, f, ensure_ascii=False, indent=4)

        print(result)
    elif file_type == "part":

        dxf_path = os.path.join(
            base_dir,
            "parts",
            file_name + ".dxf"
        )

        width, height, _, _ = part_width_height(
            dxf_path,
            file_name
        )

        width = round(width)
        height = round(height)

        result = {
            "width": width,
            "height": height,
            "size": f"{width}*{height}"
        }

        with open(
                os.path.join(base_dir, "size.json"),
                "w",
                encoding="utf-8"
        ) as f:
            json.dump(result, f, ensure_ascii=False, indent=4)

        print(result)