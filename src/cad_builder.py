from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeCylinder

def create_cylinder(radius, height):
    """
    创建圆柱体
    """
    shape = BRepPrimAPI_MakeCylinder(radius, height).Shape()
    return shape