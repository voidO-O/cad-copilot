from tools import TOOLS
from viewer import show_shapes
from llm_real import parse_with_ai
from spatial import apply_spatial_relation
import uuid

# 在 main.py 的 import 区域下方添加
class SessionContext:
    def __init__(self):
        # 记录 AI 生成的所有历史步骤 (JSON 格式)
        self.history_steps = []  
        # 记录场景中所有的模型对象 {名称: OCC对象}
        self.shape_pool = {}     
        # 记录最后一次操作的对象名字，方便处理“把它缩小”这种指令
        self.last_target = None  

    def update_context(self, new_steps):
        """每当 AI 返回新步骤时，调用此函数更新记录"""
        self.history_steps.extend(new_steps)
        if new_steps:
            # 假设最后一步是用户关注的重点
            self.last_target = new_steps[-1].get("name")

    def get_scene_description(self):
        """将当前场景有哪些物体告诉 AI"""
        if not self.shape_pool:
            return "当前场景是空的。"
        names = ", ".join(self.shape_pool.keys())
        return f"当前场景中有以下对象: {names}。上一次操作的对象是: {self.last_target}。"
    

def main():
    # 1. 初始化记忆
    ctx = SessionContext()
    print("=== CAD Copilot 多轮对话模式已启动 ===")
    print("您可以输入指令，例如：'创建一个球'，然后输入 '把它向右移动'")

    while True:
        # 2. 获取输入
        text = input("\n请输入指令 (输入 'exit' 退出): ")
        if text.lower() == 'exit':
            break

        # 3. 获取当前场景的描述，发给 AI
        context_info = ctx.get_scene_description()
        result = parse_with_ai(text, context_info)

        if not result:
            print("❌ AI解析失败")
            continue

        # 4. 执行 AI 返回的步骤
        # 注意：这里我们不再重置 shape_pool，而是使用 ctx.shape_pool
        for step in result:
            tool_name = step.get("tool")
            args = step.get("args", {})
            name = step.get("name") or f"obj_{uuid.uuid4().hex[:4]}"

            # 处理创建逻辑
            if tool_name in TOOLS:
                try:
                    # 如果是布尔运算，需要从 pool 里找之前的对象
                    if tool_name in ["cut", "fuse", "common", "union"]:
                        s1 = ctx.shape_pool.get(args.get("shape1"))
                        s2 = ctx.shape_pool.get(args.get("shape2"))
                        if s1 and s2:
                            new_shape = TOOLS[tool_name](s1, s2)
                        else:
                            print(f"❌ 找不到对象: {args}")
                            continue
                    else:
                        # 普通创建逻辑
                        new_shape = TOOLS[tool_name](**args)
                    
                    # 存入记忆中的对象池
                    ctx.shape_pool[name] = new_shape
                    print(f"✅ 执行成功: {name} ({tool_name})")
                except Exception as e:
                    print(f"❌ 建模出错: {e}")

        # 5. 更新记忆历史
        ctx.update_context(result)

        # 6. 刷新 3D 显示 (显示池子里所有的物体)
        print("正在渲染场景...")
        show_shapes(list(ctx.shape_pool.values()))

if __name__ == "__main__":
    main()