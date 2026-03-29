from OCC.Display.SimpleGui import init_display

# 我们不再使用全局变量保持状态，因为旧窗口关掉后状态就失效了
def show_shapes(shapes):
    # 1. 每次调用都重新初始化一个新的窗口环境
    # 这样虽然效率低一点点，但能保证每次关闭后再次输入都能弹窗
    display, start_display, add_menu, add_function_to_menu = init_display()

    # 2. 清除新窗口里的默认内容（如果有的话）
    display.EraseAll()

    # 3. 循环显示你 shape_pool 里的所有物体
    for shape in shapes:
        display.DisplayShape(shape, update=False)

    # 4. 自动调整视角
    display.FitAll()
    
    # 5. 启动显示循环（这会阻塞程序，直到你关掉窗口）
    print("窗口已弹出，请查看 3D 模型。关闭窗口后即可输入下一条指令。")
    start_display()