# session_context.py
import time
import uuid
from OCC.Core.GProp import GProp_GProps
from OCC.Core.BRepGProp import brepgprop

class CADObject:
    def __init__(self, name, shape,obj_type,params, parents=None):
        self.name = name
        self.shape = shape
        self.obj_type = obj_type
        self.params = params  # 包含 color, radius, position 等
        self.parents = parents or []
        self.timestamp = time.time()
        self.color = params.get('color', 'gray')
        self.volume = self._calculate_volume()

    def _calculate_volume(self):
        try:
            props = GProp_GProps()
        # 修改这里：使用静态方法
            brepgprop.VolumeProperties(self.shape, props) 
            return props.Mass()
        except:
            return 0.0

    def to_dict(self):
        return {
            "name": self.name,
            "type": self.obj_type,
            "volume": round(self.volume, 2),
            "color": self.color,
            "params": self.params
        }

class ObjectRegistry:
    def __init__(self):
        self.objects = {}
        self.visible_names = set()
        self.history = [] # 记录操作顺序

    def add_object(self, obj):
        self.objects[obj.name] = obj
        self.history.append(obj.name)
        self.visible_names.add(obj.name)

    def clear_all(self):
        self.objects.clear()
        self.visible_names.clear()
    
    def get_context_summary(self):
        if not self.objects: return "Scene is empty."
        lines = ["Current Scene Objects:"]
        # 按 history 顺序遍历，确保 AI 看到的顺序一致
        for name in self.history:
            if name not in self.objects: continue
            obj = self.objects[name]
            v = "visible" if name in self.visible_names else "hidden"
        
            p = obj.params
            pos = p.get('position', [0,0,0])
            h = p.get('height', 0)
            r = p.get('radius', 0)
            color = str(obj.color).upper() 
        
            # 重新构造信息行，加入 Color 字段
            lines.append(f"- {name} ({obj.obj_type}): Color={color}, Pos={pos}, Height={h}, Radius={r} [{v}]")
    
        return "\n".join(lines)