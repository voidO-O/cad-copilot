# cad_builder.py 完整代码
from OCC.Core.BRepPrimAPI import (
    BRepPrimAPI_MakeCylinder, 
    BRepPrimAPI_MakeSphere, 
    BRepPrimAPI_MakeCone, 
    BRepPrimAPI_MakeTorus
)
from OCC.Core.gp import gp_Trsf, gp_Vec
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_Transform
from OCC.Core.BRepAlgoAPI import (
    BRepAlgoAPI_Cut,
    BRepAlgoAPI_Fuse,
    BRepAlgoAPI_Common
)

def _apply_transform(shape, dx, dy, dz, copy=True):
    """
    内部辅助函数：处理形状的平移变换
    dx, dy, dz: 位移矢量
    copy: 是否返回副本
    """
    trsf = gp_Trsf()
    trsf.SetTranslation(gp_Vec(float(dx), float(dy), float(dz)))
    # 第三个参数 True 表示克隆拓扑，防止对原形状产生副作用
    return BRepBuilderAPI_Transform(shape, trsf, copy).Shape()

def create_cylinder(radius, height, position=[0, 0, 0]):
    """创建圆柱体并放置到指定位置"""
    shape = BRepPrimAPI_MakeCylinder(float(radius), float(height)).Shape()
    return _apply_transform(shape, *position)

def create_sphere(radius, position=[0, 0, 0]):
    """创建球体并放置到指定位置"""
    shape = BRepPrimAPI_MakeSphere(float(radius)).Shape()
    return _apply_transform(shape, *position)

def create_cone(radius, height, position=[0, 0, 0]):
    """创建圆锥体（顶部半径固定为0）"""
    shape = BRepPrimAPI_MakeCone(float(radius), 0.0, float(height)).Shape()
    return _apply_transform(shape, *position)

def create_torus(major_radius, minor_radius, position=[0, 0, 0]):
    """创建圆环"""
    shape = BRepPrimAPI_MakeTorus(float(major_radius), float(minor_radius)).Shape()
    return _apply_transform(shape, *position)

def translate(shape, x=0, y=0, z=0):
    """
    对外接口：相对平移一个已有的形状
    """
    return _apply_transform(shape, x, y, z, copy=True)

# --- 🌟 核心修改：增加统一布尔运算接口 🌟 ---

def boolean_operation(shape1, shape2, op_type="cut"):
    """
    统一布尔运算接口，供 tools.py 调用
    op_type: "cut" (差集), "fuse" (并集), "common" (交集)
    """
    if op_type == "cut":
        algo = BRepAlgoAPI_Cut(shape1, shape2)
    elif op_type == "fuse":
        algo = BRepAlgoAPI_Fuse(shape1, shape2)
    elif op_type == "common":
        algo = BRepAlgoAPI_Common(shape1, shape2)
    else:
        print(f"❌ 未知布尔运算类型: {op_type}")
        return None

    algo.Build()
    
    # 检查算法是否成功执行
    if algo.IsDone():
        result = algo.Shape()
        if result.IsNull():
            print(f"⚠️ 警告: 布尔运算 {op_type} 结果为空 (物体可能未接触)")
        return result
    else:
        print(f"❌ 布尔运算 {op_type} 失败")
        return None

# 以下为保留的原有分立接口，内部统一调用新接口以保证逻辑一致
def boolean_cut(shape1, shape2):
    return boolean_operation(shape1, shape2, "cut")

def boolean_fuse(shape1, shape2):
    return boolean_operation(shape1, shape2, "fuse")

def boolean_common(shape1, shape2):
    return boolean_operation(shape1, shape2, "common")