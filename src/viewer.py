# viewer.py
from OCC.Display.OCCViewer import Viewer3d
from OCC.Core.Quantity import Quantity_Color, Quantity_NOC_GRAY25, Quantity_NOC_GRAY
from OCC.Core.AIS import AIS_Shaded

class CADViewer:
    def __init__(self):
        self.display = None
        self._initialized = False
        self._last_x = 0
        self._last_y = 0
        # 存储名称到 AIS 对象的映射
        self.ais_objects = {} 

    def start(self, window_handle=None, parent_widget=None):
        if not self._initialized and window_handle:
            self.display = Viewer3d()
            try:
                self.display.Create(window_id=window_handle)
            except:
                self.display.Create(window_handle)

            self.display.SetSize(940, 580)
            
            if hasattr(self.display, "View"):
                # 设置背景颜色
                self.display.View.SetBackgroundColor(Quantity_Color(Quantity_NOC_GRAY25))
                if hasattr(self.display, "Context"):
                    self.display.Context.SetDisplayMode(1, True) 
                
                # 显示坐标系
                for m in ["DisplayTrihedron", "DisplayTriedron"]:
                    if hasattr(self.display, m):
                        getattr(self.display, m)()
                        break
            
            # --- 交互适配逻辑保持不变 ---
            if parent_widget and self.display:
                def save_pos(e):
                    self._last_x, self._last_y = e.x, e.y

                def rotate(e):
                    self.display.Rotation(e.x, e.y)
                    self.display.Repaint()

                def pan(e):
                    self.display.Pan(e.x - self._last_x, self._last_y - e.y)
                    self._last_x, self._last_y = e.x, e.y
                    self.display.Repaint()

                def zoom(e):
                    try:
                        zoom_factor = 10 
                        if e.delta > 0:
                            self.display.Zoom(e.x, e.y, e.x + zoom_factor, e.y + zoom_factor)
                        else:
                            self.display.Zoom(e.x, e.y, e.x - zoom_factor, e.y - zoom_factor)
                    except:
                        if hasattr(self.display, "View"):
                            scale = 1.1 if e.delta > 0 else 0.9
                            current_scale = self.display.View.Scale()
                            self.display.View.SetScale(current_scale * scale)
                    self.display.Repaint()

                parent_widget.bind("<Button-1>", save_pos)
                parent_widget.bind("<B1-Motion>", rotate)
                parent_widget.bind("<Button-3>", save_pos)
                parent_widget.bind("<B3-Motion>", pan)
                parent_widget.bind("<MouseWheel>", zoom)

            if hasattr(self.display, "InitContext"):
                self.display.InitContext()
            
            self.display.Repaint()
            self._initialized = True

    def update_scene(self, object_registry):
        """
        根据 ObjectRegistry 刷新场景
        """
        if not self.display: return
        
        # 1. 清理现有显示
        self.display.Context.EraseAll(True)
        self.ais_objects.clear()

        # 2. 遍历可见对象
        for name in object_registry.visible_names:
            if name in object_registry.objects:
                obj = object_registry.objects[name]
                # 显示形状
                ais_shape = self.display.DisplayShape(obj.shape, update=False)[0]
                self.ais_objects[name] = ais_shape
                
                # 3.直接应用已经在 Controller 中转换好的颜色对象
                self.set_shape_color(name, obj.color)
        
        self.display.FitAll()
        self.display.Repaint()

    def set_shape_color(self, name, color_value):
        """
        设置特定物体的颜色。
        color_value: 既可以是 Quantity_NOC 枚举，也可以是字符串。
        """
        if not self.display or name not in self.ais_objects:
            return

        ais_shape = self.ais_objects[name]
        
        # 检查类型。如果是字符串（手动调用时可能用到），转为枚举；
        # 如果已经是枚举（Controller 传来的），直接使用。
        if isinstance(color_value, str):
            # 为了防止 tools 循环导入，这里做一个简单的本地映射或默认处理
            from tools import COLORS
            color_enum = COLORS.get(color_value.lower(), Quantity_NOC_GRAY)
        else:
            # 此时 color_value 已经是 Quantity_NOC_RED 等对象了
            color_enum = color_value

        context = self.display.Context
        # SetColor 需要的是 Quantity_Color 对象包裹的枚举
        context.SetColor(ais_shape, Quantity_Color(color_enum), False)
        context.SetDisplayMode(ais_shape, 1, False)
        self.display.Repaint()

    def erase_shape(self, name):
        """隐藏特定物体"""
        if name in self.ais_objects:
            self.display.Context.Erase(self.ais_objects[name], True)
            del self.ais_objects[name]

_viewer = CADViewer()
def get_viewer():
    return _viewer