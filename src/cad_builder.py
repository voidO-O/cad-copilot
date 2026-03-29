from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeCylinder
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeSphere
from OCC.Core.gp import gp_Trsf, gp_Vec
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_Transform
from OCC.Core.BRepAlgoAPI import (
    BRepAlgoAPI_Cut,
    BRepAlgoAPI_Fuse,
    BRepAlgoAPI_Common
)


def create_cylinder(radius, height, position=[0,0,0]):
    shape = BRepPrimAPI_MakeCylinder(radius, height).Shape()

    from OCC.Core.gp import gp_Trsf, gp_Vec
    from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_Transform

    trsf = gp_Trsf()
    trsf.SetTranslation(gp_Vec(*position))

    return BRepBuilderAPI_Transform(shape, trsf).Shape()


def create_sphere(radius, position=[0,0,0]):
    shape = BRepPrimAPI_MakeSphere(radius).Shape()

    from OCC.Core.gp import gp_Trsf, gp_Vec
    from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_Transform

    trsf = gp_Trsf()
    trsf.SetTranslation(gp_Vec(*position))

    return BRepBuilderAPI_Transform(shape, trsf).Shape()


def translate(shape, x=0, y=0, z=0):
    """
    平移一个 shape
    """
    trsf = gp_Trsf()
    trsf.SetTranslation(gp_Vec(x, y, z))

    transformed_shape = BRepBuilderAPI_Transform(shape, trsf, True).Shape()
    return transformed_shape

def boolean_cut(shape1, shape2):
    return BRepAlgoAPI_Cut(shape1, shape2).Shape()

def boolean_fuse(shape1, shape2):
    return BRepAlgoAPI_Fuse(shape1, shape2).Shape()

def boolean_common(shape1, shape2):
    result = BRepAlgoAPI_Common(shape1, shape2).Shape()

    if result.IsNull():
        print("❌ 布尔结果为空（没有交集）")

    return result