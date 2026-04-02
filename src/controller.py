# controller.py
import uuid
from tools import TOOL_REGISTRY, COLORS
from session_context import CADObject
from datetime import datetime

class Color:
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    END = '\033[0m'

class CADController:
    def __init__(self, registry, viewer, logger):
        self.registry = registry
        self.viewer = viewer
        self.logger = logger

    def execute_json_steps(self, steps, user_input=""):
        self._print_header(user_input)
        print(f"{Color.CYAN}[AI 规划详情]:{Color.END} {steps}")

        if not steps:
            print(f"{Color.YELLOW}⚠ AI 规划结果为空{Color.END}")
            return

        try:
            for i, step in enumerate(steps):
                tool_name = step.get("tool")
                
                # 参数容错处理
                # 优先获取 args 字典，如果为空，则把除了 tool, name, args 以外的所有字段都塞进 args
                args = step.get("args", {}).copy()
                if not args:
                    args = {k: v for k, v in step.items() if k not in ['tool', 'name', 'args']}
                
                name = step.get("name", f"obj_{uuid.uuid4().hex[:4]}")
                
                print(f"[{i+1}/{len(steps)}] 执行: {Color.PURPLE}{tool_name:12}{Color.END}...", end="")

                # 1. 处理非几何工具
                if tool_name == "visibility":
                    self._handle_visibility(args)
                    continue
                
                if tool_name == "reset":
                    self.registry.clear_all()
                    print(f" {Color.GREEN}场景已重置{Color.END}")
                    continue

                # 2. 处理几何工具及删除操作
                if tool_name in TOOL_REGISTRY:
                    tool_instance = TOOL_REGISTRY[tool_name]()
                    
                    # 针对布尔运算的特殊处理
                    if "boolean" in tool_name:
                        args['op_type'] = tool_name.split('_')[-1]

                    # 执行工具逻辑
                    result = tool_instance.execute(self.registry, **args)
                    
                    # 3. 后续处理
                    if isinstance(result, str):
                        # 如果返回的是字符串（如 Translate 或 Delete 的成功消息）
                        print(f" {Color.GREEN}{result}{Color.END}")
                    elif result:
                        # 如果返回的是新形状（如 sphere, cylinder）
                        new_obj = CADObject(name, result, tool_name, args)
                        self.registry.add_object(new_obj)
                        print(f" {Color.GREEN}成功{Color.END} -> {name}")
                    else:
                        print(f" {Color.RED}失败{Color.END}")
                else:
                    print(f" {Color.RED}未知工具: {tool_name}{Color.END}")

            print(f"\n{Color.BOLD}Status:{Color.END} {Color.GREEN}SUCCESS{Color.END}")

        except Exception as e:
            print(f" {Color.RED}报错: {e}{Color.END}")
            raise e
        finally:
            print(f"{Color.CYAN}--------------------------------------{Color.END}\n")
            self.logger.log(
                 user_input=user_input, 
                 scene_context=self.registry.get_context_summary(), 
                 status="success", # 或根据 try/except 结果传入
                 steps=steps
                 )

    def _handle_visibility(self, args):
        target, action = args.get("shape"), args.get("action")
        
        # 增强的可见性逻辑，支持 show_only 和 all
        if action == "show_only":
            self.registry.visible_names.clear()
            if target != "all":
                self.registry.visible_names.add(target)
                
        elif target == "all":
            if action == "hide":
                self.registry.visible_names.clear()
            elif action == "show":
                # 将所有已注册的对象加入可见集合
                self.registry.visible_names.update(self.registry.objects.keys())
                
        else:
            if action == "hide" and target in self.registry.visible_names:
                self.registry.visible_names.remove(target)
            elif action == "show":
                self.registry.visible_names.add(target)
                
        print(f" {Color.GREEN}可见性已更新: {target} -> {action}{Color.END}")

    def _print_header(self, user_input):
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"{Color.CYAN}--- Interaction Log [{timestamp}] ---{Color.END}")
        print(f"{Color.BOLD}User Input:{Color.END} {user_input}")