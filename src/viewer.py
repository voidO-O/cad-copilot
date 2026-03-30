# viewer.py
from OCC.Display.OCCViewer import Viewer3d
from OCC.Core.Quantity import Quantity_Color, Quantity_NOC_GRAY25

class CADViewer:
    def __init__(self):
        self.display = None
        self._initialized = False
        self._last_x = 0
        self._last_y = 0

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
                # 默认开启实体显示模式 (Shaded)
                if hasattr(self.display, "Context"):
                    self.display.Context.SetDisplayMode(1, True) 
                
                # 显示坐标系
                for m in ["DisplayTrihedron", "DisplayTriedron"]:
                    if hasattr(self.display, m):
                        getattr(self.display, m)()
                        break
            
            # 🌟【交互适配】：针对 pythonocc 7.9.0 的底层指令
            if parent_widget and self.display:
                def save_pos(e):
                    self._last_x, self._last_y = e.x, e.y

                def rotate(e):
                    # 7.9.0 版本的旋转 API
                    self.display.Rotation(e.x, e.y)
                    self.display.Repaint()

                def pan(e):
                    # 7.9.0 版本的平移 API
                    self.display.Pan(e.x - self._last_x, self._last_y - e.y)
                    self._last_x, self._last_y = e.x, e.y
                    self.display.Repaint()

                # 🌟 针对 7.9.0 报错专门修复的缩放函数
                def zoom(e):
                    # 方案 1: 尝试动态缩放 (DynamicZoom)
                    # 许多 7.x 版本使用 DynamicZoom(x1, y1, x2, y2) 模拟滚轮
                    try:
                        zoom_factor = 10 # 步进值
                        if e.delta > 0:
                            # 放大：从中心向外模拟拉伸
                            self.display.Zoom(e.x, e.y, e.x + zoom_factor, e.y + zoom_factor)
                        else:
                            # 缩小：从中心向内模拟收缩
                            self.display.Zoom(e.x, e.y, e.x - zoom_factor, e.y - zoom_factor)
                    except TypeError:
                        # 方案 2: 如果报错 Zoom() 只有 3 个参数，说明它是 Zoom(x, y) 步进
                        try:
                            # 连续调用 2 次以增强滚轮感
                            for _ in range(2):
                                self.display.Zoom(e.x, e.y)
                        except:
                            # 方案 3: 终极保底，直接操作底层的视角缩放系数
                            if hasattr(self.display, "View"):
                                scale = 1.1 if e.delta > 0 else 0.9
                                current_scale = self.display.View.Scale()
                                self.display.View.SetScale(current_scale * scale)
                    
                    self.display.Repaint()

                # 绑定 Tkinter 事件
                parent_widget.bind("<Button-1>", save_pos)
                parent_widget.bind("<B1-Motion>", rotate)
                parent_widget.bind("<Button-3>", save_pos)
                parent_widget.bind("<B3-Motion>", pan)
                parent_widget.bind("<MouseWheel>", zoom)

            if hasattr(self.display, "InitContext"):
                self.display.InitContext()
            
            self.display.Repaint()
            self._initialized = True

    def update_shapes(self, shapes):
        """刷新场景并显示实体模型"""
        if not self.display: return
        
        try:
            # 清理场景
            if hasattr(self.display, "EraseAll"):
                self.display.EraseAll()
            else:
                self.display.Context.EraseAll(True)
        except: pass

        # 渲染每一个形状
        for s in shapes:
            self.display.DisplayShape(s, update=False)
        
        # 🌟 关键：确保 7.9.0 下物体以实体(AIS_Shaded)而非线框模式显示
        if hasattr(self.display, "Context"):
            self.display.Context.SetDisplayMode(1, True)

        self.display.FitAll()
        
        if hasattr(self.display, "View"):
            self.display.View.MustBeResized()
            self.display.View.Update()
        self.display.Repaint()

_viewer = CADViewer()
def get_viewer():
    return _viewer