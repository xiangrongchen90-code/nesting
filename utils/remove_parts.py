
#移除有與leather發生碰撞的part
def remove_part(doc, msp, part_name, output_file):
    # 刪除 INSERT（實體）
    inserts_to_remove = [e for e in msp.query('INSERT') if e.dxf.name == part_name]
    for e in inserts_to_remove:
        msp.delete_entity(e)

    doc.saveas(output_file)
    #print(f"🗑️ 已移除INSERT: {part_name}")