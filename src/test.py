from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeSphere, BRepPrimAPI_MakeCylinder
from OCC.Core.BRepAlgoAPI import BRepAlgoAPI_Common
from OCC.Core.gp import gp_Trsf, gp_Vec
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_Transform

# 1. 创建球
sphere = BRepPrimAPI_MakeSphere(10).Shape()

# 2. 创建圆柱
cylinder = BRepPrimAPI_MakeCylinder(5, 20).Shape()

# 3. 平移圆柱（关键！）
trsf = gp_Trsf()
trsf.SetTranslation(gp_Vec(5, 0, 0))  # 👉 向右移动
cylinder = BRepBuilderAPI_Transform(cylinder, trsf).Shape()

# 4. 做交集
result = BRepAlgoAPI_Common(sphere, cylinder).Shape()

from viewer import show_shapes
show_shapes([result])