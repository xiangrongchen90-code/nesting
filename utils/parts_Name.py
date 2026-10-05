import ezdxf
import os
#求part的名稱
def partsName(path):
    return os.path.splitext(os.path.basename(path))[0]
# def partsName(path):
#     a=ezdxf.readfile(path)
#     b=a.modelspace()
#     for entity in b:
#         if entity.dxftype()=="INSERT":
#             return entity.dxf.name
#     return "None"