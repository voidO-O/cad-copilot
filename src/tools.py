import math
from abc import ABC, abstractmethod
from OCC.Core.Quantity import Quantity_NOC_RED, Quantity_NOC_GREEN, Quantity_NOC_BLUE, Quantity_NOC_GRAY
from OCC.Core.BRep import BRep_Builder
from OCC.Core.TopoDS import TopoDS_Compound
from OCC.Core.StlAPI import StlAPI_Writer
import copy
import uuid
import os
from OCC.Core.BRepCheck import BRepCheck_Analyzer # 导入检查工具
from OCC.Core.BRepMesh import BRepMesh_IncrementalMesh
from OCC.Core.StlAPI import StlAPI_Writer

# --- 1. 颜色映射表 ---
COLORS = {
    "red": Quantity_NOC_RED,
    "green": Quantity_NOC_GREEN,
    "blue": Quantity_NOC_BLUE,
    "gray": Quantity_NOC_GRAY
}

# --- 2. 工具基类 ---
class BaseTool(ABC):
    @abstractmethod
    def execute(self, registry, **kwargs):
        pass

# --- 3. 具体形状实现 ---
class SphereTool(BaseTool):
    def execute(self, registry, radius=1, position=[0,0,0], **kwargs): 
        from cad_builder import create_sphere
        return create_sphere(radius, position)

class CylinderTool(BaseTool):
    def execute(self, registry, radius=1, height=5, position=[0,0,0], **kwargs):
        from cad_builder import create_cylinder
        return create_cylinder(radius, height, position)

class ConeTool(BaseTool): 
    def execute(self, registry, radius=1, height=5, position=[0,0,0], **kwargs):
        from cad_builder import create_cone
        return create_cone(radius, height, position)

class TorusTool(BaseTool):
    def execute(self, registry, major_radius=5, minor_radius=1, position=[0,0,0], **kwargs):
        from cad_builder import create_torus
        return create_torus(major_radius, minor_radius, position)
    
class DeleteTool(BaseTool):
    def execute(self, registry, shape, **kwargs):
        if shape in registry.objects:
            del registry.objects[shape]
            if shape in registry.visible_names:
                registry.visible_names.remove(shape)
            if hasattr(registry, 'history') and shape in registry.history:
                registry.history.remove(shape)
            return f"物体 {shape} 已被永久删除"
        return f"错误：找不到物体 {shape}"
    
class TranslateTool(BaseTool):
    def execute(self, registry, shape, x=0, y=0, z=0, **kwargs):
        from cad_builder import translate
        target_obj = registry.objects.get(shape)
        if not target_obj: return f"Error: {shape} not found"

        new_shape = translate(target_obj.shape, x, y, z)
        target_obj.shape = new_shape
        
        current_pos = target_obj.params.get('position', [0, 0, 0])
        target_obj.params['position'] = [
            current_pos[0] + float(x),
            current_pos[1] + float(y),
            current_pos[2] + float(z)
        ]
        
        target_obj.dirty = True 
        return f"SUCCESS: Moved {shape}"
    
class ScaleTool(BaseTool):
    def execute(self, registry, shape, factor, **kwargs):
        if shape not in registry.objects:
            return f"错误：找不到物体 {shape}"
        
        obj = registry.objects[shape]
        f = float(factor)

        if obj.obj_type == "sphere":
            obj.params['radius'] *= f
        elif obj.obj_type in ["cylinder", "cone"]:
            obj.params['radius'] *= f
            obj.params['height'] *= f
        elif obj.obj_type == "torus":
            obj.params['major_radius'] *= f
            obj.params['minor_radius'] *= f
            
        from cad_builder import create_sphere, create_cylinder, create_cone, create_torus
        pos = obj.params.get('position', [0,0,0])
        if obj.obj_type == "sphere":
            obj.shape = create_sphere(obj.params['radius'], pos)
        elif obj.obj_type == "cylinder":
            obj.shape = create_cylinder(obj.params['radius'], obj.params['height'], pos)
        elif obj.obj_type == "cone":
            obj.shape = create_cone(obj.params['radius'], obj.params['height'], pos)
        elif obj.obj_type == "torus":
            obj.shape = create_torus(obj.params['major_radius'], obj.params['minor_radius'], pos)
            
        obj.dirty = True 
        return f"物体 {shape} 已物理缩放 {f} 倍"

# --- 4. 布尔运算工具 ---
class BooleanTool(BaseTool):
    # 🌟 终极修复：在初始化时就把算子类型焊死
    def __init__(self, default_op="cut"):
        self.default_op = default_op

    def execute(self, registry, shape1, shape2, **kwargs):
        from cad_builder import boolean_operation
        import uuid
        import copy
        
        try:
            from session_context import CADObject
        except ImportError:
            from main import CADObject

        obj1 = registry.objects.get(shape1)
        obj2 = registry.objects.get(shape2)
        
        if not obj1:
            return f"ERROR: Object '{shape1}' not found in the scene. Please check the ID."
        if not obj2:
            return f"ERROR: Object '{shape2}' not found in the scene. Please check the ID."

        # 直接使用初始化时绑定的算子类型
        op_type = self.default_op

        print(f">>> Executing Boolean [{op_type}] between {shape1} and {shape2}")
        result_shape = boolean_operation(obj1.shape, obj2.shape, op_type)

        if result_shape is not None:
            res_name = f"res_{op_type}_{uuid.uuid4().hex[:4]}"
            res_params = copy.deepcopy(obj1.params)
            res_params["is_result"] = True
            res_params["operation"] = op_type
            
            new_obj = CADObject(
                name=res_name,
                params=res_params,
                shape=result_shape,
                obj_type="compound"
            )
            
            registry.objects[res_name] = new_obj
            registry.visible_names.add(res_name)
            
            registry.visible_names.discard(shape1)
            registry.visible_names.discard(shape2)
            
            return f"SUCCESS: Generated {res_name} via {op_type}"
        else:
            return f"ERROR: Boolean {op_type} failed. The objects might not be intersecting."

class ResetTool(BaseTool):
    def execute(self, registry, **kwargs):
        try:
            registry.clear_all()
            return "场景已完全重置，所有物体已清除。"
        except Exception as e:
            return f"重置失败: {str(e)}"

class ExportTool(BaseTool):
    def execute(self, registry, filename="model_export", **kwargs):
        visible_shapes = []
        for name in registry.visible_names:
            if name in registry.objects:
                visible_shapes.append(registry.objects[name].shape)
        
        if not visible_shapes:
            return "ERROR: No visible objects to export."

        # 🌟 修复：直接使用传入的 filename，它已经是 llm_real 计算好的绝对路径
        # 不要再次使用 os.path.abspath，防止二次拼接错误
        final_path = str(filename)
        
        # 补全后缀
        if not final_path.lower().endswith('.stl'):
            final_path += ".stl"

        # 确保目录存在（后端最后一道防线）
        export_dir = os.path.dirname(final_path)
        if export_dir and not os.path.exists(export_dir):
            os.makedirs(export_dir, exist_ok=True)

        success = export_to_stl(visible_shapes, final_path)
        
        if success:
            return f"SUCCESS: Scene exported to {final_path}"
        else:
            # 如果失败了，返回具体的路径供调试
            return f"ERROR: Failed to write to {final_path}"

# --- 5. 工具注册表 ---
TOOL_REGISTRY = {
    "sphere": SphereTool,
    "cylinder": CylinderTool,
    "cone": ConeTool,
    "torus": TorusTool,
    "boolean_cut": lambda: BooleanTool("cut"),    
    "boolean_fuse": lambda: BooleanTool("fuse"),
    "boolean_common": lambda: BooleanTool("common"),
    "delete": DeleteTool,
    "translate": TranslateTool,
    "reset": ResetTool,
    "scale": ScaleTool,
    "export_stl": ExportTool
}

# --- 6. 导出功能 ---
def export_to_stl(shapes, filename):
    try:
        # 1. 路径预处理
        final_path = os.path.abspath(os.path.normpath(filename))
        os.makedirs(os.path.dirname(final_path), exist_ok=True)

        # 2. 准备容器
        builder = BRep_Builder()
        compound = TopoDS_Compound()
        builder.MakeCompound(compound)
        
        has_content = False
        for s in shapes:
            if s and not s.IsNull():
                # 🌟 核心补丁：强制进行网格化 (BRepMesh) 🌟
                # 参数 0.1 是网格精度，值越小越精细，但生成越慢
                # 如果没有这一步，Writer 面对圆滑的球体可能会“一脸懵逼”地导出空文件
                BRepMesh_IncrementalMesh(s, 0.1) 
                builder.Add(compound, s)
                has_content = True

        if not has_content:
            print("❌ 导出失败：没有有效的几何体")
            return False

        # 3. 写入文件
        print(f"DEBUG: 正在网格化并写入 -> {final_path}")
        writer = StlAPI_Writer()
        
        # 针对 StlAPI_Writer 的特殊处理：
        # 有些版本在 Windows 下处理绝对路径时，如果包含中文或空格会失败
        # 我们先尝试直接写
        writer.Write(compound, final_path)
        
        # 4. 验证结果
        # 如果直接写入失败，尝试“曲线救国”：写到当前目录再移动
        if not os.path.exists(final_path) or os.path.getsize(final_path) == 0:
            temp_name = "rescue_export.stl"
            writer.Write(compound, temp_name)
            if os.path.exists(temp_name) and os.path.getsize(temp_name) > 0:
                import shutil
                shutil.move(temp_name, final_path)
                print(f"✅ 通过临时中转成功导出！")
                return True
            else:
                print("❌ 物理写入尝试完全失败，请检查磁盘空间或权限")
                return False
        
        print(f"✅ 导出成功！文件大小: {os.path.getsize(final_path)} 字节")
        return True

    except Exception as e:
        print(f"底层导出异常: {e}")
        return False