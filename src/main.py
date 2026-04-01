import customtkinter as ctk
import tkinter as tk
from session_context import ObjectRegistry
from controller import CADController
from viewer import get_viewer
from logger_utils import InteractionLogger
from llm_real import plan_with_ai
import threading
from datetime import datetime
import os
import time

class CADApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Gemini CAD Copilot v2 - Professional Edition")
        self.geometry("1200x850")
        
        # 1. 初始化核心组件
        self.registry = ObjectRegistry()
        self.viewer = get_viewer()
        self.logger = InteractionLogger()
        self.controller = CADController(self.registry, self.viewer, self.logger)
        
        # 2. 构建界面
        self._setup_ui()

    def _setup_ui(self):
        # --- A. 左侧侧边栏 ---
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.pack(side="left", fill="y", padx=0, pady=0)
        ctk.CTkLabel(self.sidebar, text="CAD 控制", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=20)

        ctk.CTkButton(self.sidebar, text="重置视图", command=lambda: self.viewer.display.FitAll()).pack(pady=10, padx=20)
        ctk.CTkButton(self.sidebar, text="清空全部", fg_color="#A03030", command=self.manual_reset_scene).pack(pady=10, padx=20)
        ctk.CTkButton(self.sidebar, text="导出 STL", command=self.manual_export).pack(pady=10, padx=20)

        # --- B. 右侧容器 ---
        self.right_container = ctk.CTkFrame(self)
        self.right_container.pack(side="right", fill="both", expand=True, padx=5, pady=5)

        # 3D 视图区域
        self.viewer_frame = tk.Frame(self.right_container, bg="gray25") 
        self.viewer_frame.pack(side="top", fill="both", expand=True, padx=5, pady=5)

        # 历史记录显示
        self.history_display = ctk.CTkTextbox(self.right_container, height=180)
        self.history_display.pack(side="top", fill="x", padx=20, pady=5)
        self.history_display.tag_config("user", foreground="#1E90FF")
        self.history_display.tag_config("ai_plan", foreground="#808080")
        self.history_display.tag_config("exec", foreground="#2E8B57")
        self.history_display.tag_config("error", foreground="#DC143C")
        self.history_display.configure(state="disabled")

        # --- C. 底部输入面板 ---
        self.control_panel = ctk.CTkFrame(self.right_container, height=80)
        self.control_panel.pack(side="bottom", fill="x", padx=20, pady=10)

        self.entry = ctk.CTkEntry(self.control_panel, placeholder_text="在此输入指令...", height=40)
        self.entry.pack(side="left", padx=10, expand=True, fill="x")
        self.entry.bind("<Return>", lambda e: self.on_submit())

        self.submit_btn = ctk.CTkButton(self.control_panel, text="发送", command=self.on_submit, width=60, height=40)
        self.submit_btn.pack(side="left", padx=5)

        self.fb_frame = ctk.CTkFrame(self.control_panel, fg_color="transparent")
        self.fb_frame.pack(side="left", padx=10)
        ctk.CTkButton(self.fb_frame, text="👍", width=35, command=lambda: self.submit_feedback(True)).pack(side="left", padx=2)
        ctk.CTkButton(self.fb_frame, text="👎", width=35, command=lambda: self.submit_feedback(False)).pack(side="left", padx=2)

        self.status_label = ctk.CTkLabel(self.control_panel, text="准备就绪", text_color="gray")
        self.status_label.pack(side="right", padx=20)

    def append_history(self, tag, message, tag_name="exec"):
        self.history_display.configure(state="normal")
        ts = datetime.now().strftime("%H:%M:%S")
        self.history_display.insert("end", f"[{ts}] [{tag}] ", tag_name)
        self.history_display.insert("end", f"{message}\n")
        self.history_display.see("end")
        self.history_display.configure(state="disabled")

    def on_submit(self):
        text = self.entry.get().strip()
        if not text: return
        self.entry.delete(0, 'end')
        self.submit_btn.configure(state="disabled")
        threading.Thread(target=self._async_task, args=(text,), daemon=True).start()

    def get_enhanced_context(self):
        if not self.registry.objects:
            return "Current scene is empty."
        items = list(self.registry.objects.items())
        summary = "### Current Scene Entities (Ordered by Creation):\n"
        for i, (name, obj) in enumerate(items):
            pos = obj.params.get('position', [0, 0, 0])
            summary += f"- ID: {name} (Index: obj_{i}): {obj.obj_type}, Position: {pos}\n"
        summary += "\n**Rule**: Use 'LAST_OBJ_1', 'LAST_OBJ_2' or 'PREVIOUS_RESULT' for boolean operations."
        return summary

    def _preprocess_steps(self, steps):
        """
        确定性解析器 2.0：
        1. 建立 'geo_index_map'，记录原始指令中的每个物体在展平序列中的真实位置。
        2. LAST_OBJ_N 仅在【用户显式创建】的物体中回溯，无视自动生成的工具体。
        """
        import copy
        flattened_queue = []
        
        # 物理环境已有的 ID
        base_stack = list(self.registry.objects.keys())
        
        # 1. 展平扫描：提取嵌套字典，并记录哪些步骤是“原始几何体”
        raw_geo_steps_indices = [] # 记录展平后，哪些索引属于原始指令要求的物体
        
        for raw_step in steps:
            tool = raw_step.get('tool', '')
            args = raw_step.get('args', {})
            
            # 嵌套拆解逻辑
            if tool.startswith("boolean_") and isinstance(args.get("shape2"), dict):
                inner = args["shape2"]
                # 提取 inner 的内容
                gen_tool = inner.get("tool", "cylinder")
                gen_args = inner.get("args", inner)
                
                # A. 插入工具体生成步骤
                gen_step = {"tool": gen_tool, "args": gen_args, "is_auto": True}
                flattened_queue.append(gen_step)
                
                # B. 插入布尔步骤，shape2 指向刚生成的工具体
                # 注意：此时不计入 raw_geo_steps_indices，因为它是自动生成的
                new_bool_step = copy.deepcopy(raw_step)
                new_bool_step["args"]["shape2"] = f"AUTO_REF_{len(flattened_queue)-1}"
                flattened_queue.append(new_bool_step)
            else:
                # 原始步骤：如果是创建几何体，记录其在 flattened_queue 中的位置
                if tool in ['sphere', 'box', 'cylinder', 'cone', 'torus']:
                    raw_geo_steps_indices.append(len(flattened_queue))
                flattened_queue.append(copy.deepcopy(raw_step))

        # 2. 第二次扫描：确定性 ID 绑定
        final_processed = []
        logic_stack = list(base_stack) # 物理栈：包含所有 pending_obj
        user_obj_stack = list(base_stack) # 用户栈：仅包含用户显式要求的物体
        result_stack = []

        for i, step in enumerate(flattened_queue):
            tool = step.get('tool', '')
            args = step.get('args', {})

            # 解析参数：重点解决 LAST_OBJ_N
            for key in ['shape1', 'shape2', 'shape']:
                if key in args:
                    val = str(args[key])
                    
                    # 优先处理嵌套生成的引用
                    if val.startswith("AUTO_REF_"):
                        ref_idx = int(val.split("_")[-1])
                        args[key] = flattened_queue[ref_idx].get("predicted_id")
                    
                    # 关键修复：LAST_OBJ_N 在 user_obj_stack 中找
                    elif "LAST_OBJ_" in val:
                        try:
                            offset = int(val.split("_")[-1])
                            if len(user_obj_stack) >= offset:
                                args[key] = user_obj_stack[-offset]
                        except: pass
                    
                    # PREVIOUS_RESULT 在 result_stack 中找
                    elif val in ["PREVIOUS_RESULT", "LAST_RESULT"]:
                        args[key] = result_stack[-1] if result_stack else (logic_stack[-1] if logic_stack else val)

            # 更新 ID 和 栈
            p_id = None
            if tool in ['sphere', 'box', 'cylinder', 'cone', 'torus', 'rect', 'extrude']:
                p_id = f"pending_obj_{len(logic_stack)}"
                logic_stack.append(p_id)
                # 如果不是自动生成的，说明是用户显式要求的，进用户栈
                if not step.get("is_auto"):
                    user_obj_stack.append(p_id)
            elif tool.startswith("boolean_"):
                p_id = f"pending_boolean_{i}"
                result_stack.append(p_id)
            
            if p_id:
                step['predicted_id'] = p_id
            final_processed.append(step)

        return final_processed

    def _async_task(self, text):
        self.after(0, lambda: self.append_history("USER", text, "user"))
        self.after(0, lambda: self.status_label.configure(text="AI 思考中...", text_color="yellow"))

        # 定义一个内部错误处理函数，避免 lambda 变量作用域问题
        def report_error(err_msg):
            self.after(0, lambda: self.append_history("ERROR", err_msg, "error"))
            self.after(0, lambda: self.status_label.configure(text="执行报错", text_color="red"))

        try:
            # 1. 向 AI 获取规划
            context_info = self.get_enhanced_context()
            raw_steps = plan_with_ai(text, context_info)
            if not raw_steps:
                self.after(0, lambda: self.status_label.configure(text="AI 未生成指令", text_color="orange"))
                return

            # 2. 预处理生成带有 pending_xxx 占位符的步骤
            steps = self._preprocess_steps(raw_steps)
            self.after(0, lambda: self.append_history("PLAN", "正在解析执行链路...", "ai_plan"))

            # 🌟 3. 动态映射表
            id_map = {} 
            
            for i, step in enumerate(steps):
                tool = step.get('tool')
                args = step.get('args', {}).copy() # 使用副本防止污染原始 planning
                predicted_id = step.get('predicted_id')

                # A. 映射替换：将参数里的 pending_xxx 换成真实 ID
                for key in ['shape1', 'shape2', 'shape']:
                    if key in args:
                        val = str(args[key])
                        if val in id_map:
                            print(f"DEBUG: 映射替换 {val} -> {id_map[val]}")
                            args[key] = id_map[val]
                
                # B. 执行单步：直接使用 controller 的逻辑
                # 我们调用 controller 现有的单步分发能力（如果你的 controller 有单步接口）
                # 或者直接利用 controller 内部的 registry 进行操作
                # 这里假设你的 controller 有一个 handle_single_step 类似方法，如果没有，我们直接通过 registry 操作
                
                # 兼容性写法：尝试调用 controller 执行单步
                # 如果 execute_json_steps 只接受 list，我们就传只有一项的 list
                result_log = self.controller.execute_json_steps([{"tool": tool, "args": args}], user_input=text)
                
                # C. 捕获真实 ID
                # 我们从注册表中找寻最新增加的那个 key
                current_keys = list(self.registry.objects.keys())
                if current_keys:
                    real_id = current_keys[-1] # 假设最新执行生成的就是最后一个
                    
                    if predicted_id:
                        id_map[predicted_id] = real_id
                    
                    # 针对布尔运算的特殊处理：PREVIOUS_RESULT 映射
                    if tool.startswith("boolean_") or "res_" in real_id:
                        id_map[f"pending_boolean_{i}"] = real_id
                        id_map["PREVIOUS_RESULT"] = real_id

            # 4. 更新 UI
            self.after(0, lambda: self.viewer.update_scene(self.registry))
            self.after(0, lambda: self.status_label.configure(text="复杂指令合成成功！", text_color="green"))

        except Exception as e:
            import traceback
            traceback.print_exc()
            err_str = str(e)
            report_error(err_str)
        
        finally:
            self.after(0, lambda: self.submit_btn.configure(state="normal"))

    def manual_export(self):
        try:
            from tools import export_to_stl
            visible_shapes = [obj.shape for name, obj in self.registry.objects.items() if name in self.registry.visible_names]
            if not visible_shapes: return
            
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            export_dir = os.path.join(base_path, "exports")
            os.makedirs(export_dir, exist_ok=True)
            filename = os.path.join(export_dir, f"export_{datetime.now().strftime('%H%M%S')}.stl")
            
            if export_to_stl(visible_shapes, filename):
                self.append_history("INFO", f"手动导出成功: {filename}", "exec")
        except Exception as e:
            self.append_history("ERROR", f"导出失败: {e}", "error")

    def manual_reset_scene(self):
        try:
            self.registry.clear_all()
            if self.viewer and self.viewer.display:
                self.viewer.display.Context.RemoveAll(True)
                self.viewer.display.View.Update()
            self.append_history("RESET", "场景已清空", "exec")
        except Exception as e:
            print(f"Reset Error: {e}")

    def submit_feedback(self, is_good):
        self.logger.update_feedback_last_record(is_good)
        self.status_label.configure(text="感谢反馈！", text_color="green")

    def run(self):
        self.after(200, lambda: self.viewer.start(self.viewer_frame.winfo_id(), self.viewer_frame))
        self.mainloop()

if __name__ == "__main__":
    app = CADApp()
    app.run()