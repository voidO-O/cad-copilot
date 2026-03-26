from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeCylinder

def main():
    # 创建一个圆柱
    cylinder = BRepPrimAPI_MakeCylinder(10, 20).Shape()
    
    print("✅ Cylinder created successfully!")

if __name__ == "__main__":
    main()