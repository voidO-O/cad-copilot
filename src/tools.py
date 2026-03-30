from cad_builder import create_cylinder, create_sphere, translate, boolean_cut, boolean_fuse, boolean_common
from OCC.Core.StlAPI import StlAPI_Writer
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_Transform
from OCC.Core.TopoDS import TopoDS_Compound
from OCC.Core.BRep import BRep_Builder

TOOLS = {
    "cylinder": create_cylinder,
    "sphere": create_sphere,
    "translate": translate,
    "cut": boolean_cut,
    "union": boolean_fuse,
    "fuse": boolean_fuse,
    "common": boolean_common,
}

def export_to_stl(shapes, filename):
    """
    将一组形状合并并导出为 STL 文件
    """
    try:
        builder = BRep_Builder()
        compound = TopoDS_Compound()
        builder.MakeCompound(compound)
        
        for shape in shapes:
            builder.Add(compound, shape)
            
        writer = StlAPI_Writer()
        writer.Write(compound, filename)
        return True
    except Exception as e:
        print(f"导出失败: {e}")
        return False