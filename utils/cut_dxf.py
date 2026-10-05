import ezdxf

def cut_dxf_bottom(input_path, output_path, y_cut):
    doc = ezdxf.readfile(input_path)
    msp = doc.modelspace()

    remove_list = []

    for e in msp:
        if e.dxftype() == "LWPOLYLINE":
            pts = [(x, y) for x, y, *_ in e.get_points()]

            # 如果全部點都在 y_cut 以下 → 刪掉
            if all(y < y_cut for _, y in pts):
                remove_list.append(e)

    # 執行刪除
    for e in remove_list:
        msp.delete_entity(e)

    doc.saveas(output_path)
    print("Done! 裁掉下半部並輸出到:", output_path)
cut_dxf_bottom("C:/python/Nike_Nesting_MINZ_DXF-2/output/leather00_add_parts.dxf", "C:/python/Nike_Nesting_MINZ_DXF-2/output/temp_2.dxf", y_cut=2500)
