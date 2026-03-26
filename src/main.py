from cad_builder import create_cylinder
from viewer import show_shape
from llm_real import parse_with_ai

def main():
    text = input("请输入指令: ")

    result = parse_with_ai(text)

    if result and result["type"] == "cylinder":
        shape = create_cylinder(result["radius"], result["height"])
        print("✅ AI解析成功")
        show_shape(shape)
    else:
        print("❌ AI解析失败")


if __name__ == "__main__":
    main()