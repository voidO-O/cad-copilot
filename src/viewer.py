from OCC.Display.SimpleGui import init_display

def show_shape(shape):
    display, start_display, add_menu, add_function_to_menu = init_display()

    display.DisplayShape(shape, update=True)
    display.FitAll()

    start_display()