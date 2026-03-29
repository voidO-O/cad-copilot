from OCC.Core.gp import gp_Trsf, gp_Vec
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_Transform


def translate_shape(shape, x=0, y=0, z=0):
    trsf = gp_Trsf()
    trsf.SetTranslation(gp_Vec(x, y, z))
    return BRepBuilderAPI_Transform(shape, trsf, True).Shape()


def apply_spatial_relation(shape, relation):
    offset = 20  # ⭐ 第一版先写死

    if relation == "right":
        return translate_shape(shape, x=offset)

    elif relation == "left":
        return translate_shape(shape, x=-offset)

    elif relation == "above":
        return translate_shape(shape, z=offset)

    elif relation == "below":
        return translate_shape(shape, z=-offset)

    return shape