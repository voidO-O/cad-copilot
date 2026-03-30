from logger_utils import InteractionLogger
import threading
import customtkinter as ctk
from tools import TOOLS
from llm_real import parse_with_ai, plan_with_ai, repair_with_ai
import uuid
import viewer 
from translator import ToolTranslator
import os
from datetime import datetime
import tkinter as tk

class SessionContext:
    def __init__(self):
        self.history_steps = []
        self.shape_pool = {}      
        self.visible_names = set() 
        self.last_target = None
        self.shape_metadata = {}  

    def add_shape(self, name, shape, params=None, visible=True):
        self.shape_pool[name] = shape
        if params: 
            self.shape_metadata[name] = params
        if visible: 
            self.visible_names.add(name)
        else:
            if name in self.visible_names: self.visible_names.remove(name)

    # 👇 这是之前漏掉的隐藏方法
    def hide_shape(self, name):
        if name in self.visible_names: self.visible_names.remove(name)

    # 👇 这是之前漏掉的获取可见物体方法
    def get_visible_shapes(self):
        return [self.shape_pool[n] for n in self.visible_names if n in self.shape_pool]

    # 👇 这是导致你报错的罪魁祸首，更新上下文记忆的方法
    def update_context(self, new_steps):
        if not new_steps: return
        self.history_steps.extend(new_steps)
        last_step = new_steps[-1]
        self.last_target = last_step.get("name") or last_step.get("args", {}).get("shape")

    # main.py -> SessionContext 类中替换该方法

    def get_scene_description(self):
        if not self.shape_metadata:
            return "场景目前是空的。"
        
        desc = "【后台资产库】(即使画面不显示，这些物体依然存在):\n"
        for name, meta in self.shape_metadata.items():
            v_status = "可见" if name in self.visible_names else "隐藏"
            pos = meta.get("pos", [0,0,0])
            desc += f"- {name}: 类型={meta['type']}, 位置={pos}, 状态={v_status}\n"
        
        desc += "\n⚠️ 操作建议：若物体处于'隐藏'状态，直接使用 visibility 工具将其 'show' 即可，无需重新创建。"
        return desc
    
class CADGui(ctk.CTk):
    def _setup_ui(self):
        """完整的界面布局：包含侧边栏和主交互区"""
        
        # --- A. 左侧侧边栏 (Sidebar) ---
        self.sidebar = ctk.CTkFrame(self, width=180, corner_radius=0)
        self.sidebar.pack(side="left", fill="y", padx=10, pady=10)

        ctk.CTkLabel(self.sidebar, text="CAD 控制", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=20)

        # 侧边栏按钮
        self.reset_btn = ctk.CTkButton(self.sidebar, text="重置视图 (Reset)", 
                                       command=lambda: self.handle_manual_command("reset"))
        self.reset_btn.pack(pady=10, padx=15)

        self.delete_btn = ctk.CTkButton(self.sidebar, text="清空全部 (Delete)", 
                                        fg_color="#A03030", hover_color="#8B0000",
                                        command=lambda: self.handle_manual_command("delete"))
        self.delete_btn.pack(pady=10, padx=15)

        self.export_btn = ctk.CTkButton(self.sidebar, text="导出 STL 模型", 
                                        command=self.manual_export)
        self.export_btn.pack(pady=10, padx=15)

        # --- B. 右侧主容器 ---
        self.right_container = ctk.CTkFrame(self)
        self.right_container.pack(side="right", fill="both", expand=True, padx=5, pady=5)

        # 1. 3D 渲染区域 (嵌入目标)
        self.viewer_frame = tk.Frame(self.right_container, bg="gray25") 
        self.viewer_frame.pack(side="top", fill="both", expand=True, padx=5, pady=5)

        # 2. 交互历史记录区
        self.history_display = ctk.CTkTextbox(self.right_container, height=180, corner_radius=10)
        self.history_display.pack(side="top", fill="x", padx=20, pady=5)
        
        self.history_display.tag_config("user", foreground="#1E90FF")
        self.history_display.tag_config("ai_plan", foreground="#808080")
        self.history_display.tag_config("exec", foreground="#2E8B57")
        self.history_display.tag_config("error", foreground="#DC143C")
        self.history_display.configure(state="disabled")

        # 3. 底部控制面板
        self.control_panel = ctk.CTkFrame(self.right_container, height=80)
        self.control_panel.pack(side="bottom", fill="x", padx=20, pady=10)

        # 输入框
        self.entry = ctk.CTkEntry(self.control_panel, placeholder_text="在此输入指令...", height=40)
        self.entry.pack(side="left", padx=(10, 10), expand=True, fill="x")
        self.entry.bind("<Return>", lambda e: self.run_cad())

        # 发送按钮
        self.btn = ctk.CTkButton(self.control_panel, text="发送", command=self.run_cad, width=60, height=40)
        self.btn.pack(side="left", padx=5)

        # 反馈按钮组 (👍/👎)
        self.feedback_frame = ctk.CTkFrame(self.control_panel, fg_color="transparent")
        self.feedback_frame.pack(side="left", padx=10)

        ctk.CTkButton(self.feedback_frame, text="👍", width=35, height=40, fg_color="#2E8B57", 
                      command=lambda: self.submit_feedback(True)).pack(side="left", padx=2)
        ctk.CTkButton(self.feedback_frame, text="👎", width=35, height=40, fg_color="#A03030", 
                      command=lambda: self.submit_feedback(False)).pack(side="left", padx=2)

        self.status_label = ctk.CTkLabel(self.control_panel, text="准备就绪", text_color="gray")
        self.status_label.pack(side="right", padx=20)

    def append_history(self, tag, message, tag_name="sys"):
        self.history_display.configure(state="normal")
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # 针对用户输入添加特殊前缀，使其更显眼
        display_tag = f"👤 {tag}" if tag == "USER" else f"🤖 {tag}"
        
        # 插入带颜色的标签
        self.history_display.insert("end", f"[{timestamp}] {display_tag}: ", tag_name)
        self.history_display.insert("end", f"{message}\n")
        
        self.history_display.see("end")
        self.history_display.configure(state="disabled")

    def __init__(self):
        super().__init__()
        self.title("Gemini CAD Copilot - 智能建模终端")
        self.geometry("1150x850") 
        
        # 1. 核心后端组件初始化
        self.ctx = SessionContext()
        self.translator = ToolTranslator(TOOLS.keys())
        self.logger = InteractionLogger()
        self.last_log_id = None
        
        # 2. 构建界面 (包含侧边栏和主容器)
        self._setup_ui() 

        # 3. 核心嵌入逻辑
        self.update()
        container_id = self.viewer_frame.winfo_id()
        
        self.viewer = viewer.get_viewer()
        self.viewer.start(window_handle=container_id, parent_widget=self.viewer_frame) 
        
        self.after(500, lambda: self.viewer.update_shapes(self.ctx.get_visible_shapes()))
        
        # 0.5秒后强制刷新一次空场景，唤醒 OpenGL
        self.after(500, lambda: self.viewer.update_shapes([]))

    def handle_manual_command(self, cmd_type):
        """绕过 AI 规划，直接执行 UI 触发的系统级指令"""
        step = {"tool": cmd_type, "args": {}}
        print(f"⚡ 快捷操作触发: {cmd_type}")
        self._execute_single_step(step)
        # 执行完手动刷新画面
        self.viewer.update_shapes(self.ctx.get_visible_shapes())


    # 增加手动触发方法
    def manual_reset(self):
        self._execute_single_step({"tool": "reset", "args": {}})
        self.viewer.update_shapes([]) # 清空渲染器
        self.set_status("场景已重置", "gray")

    def manual_export(self):
        self._execute_single_step({"tool": "export", "args": {"filename": "manual_export.stl"}})
        self.set_status("导出成功 (manual_export.stl)", "green")


    def set_status(self, text, color="white"):
        self.after(0, lambda: self.status_label.configure(text=text, text_color=color))

    def run_cad(self):
        text = self.entry.get()
        if not text: return
        self.btn.configure(state="disabled")
        threading.Thread(target=self._async_task, args=(text,), daemon=True).start()

    def submit_feedback(self, is_good):
        if self.last_log_id:
            # 调用 logger_utils 中的更新方法
            self.logger.update_feedback(self.last_log_id, is_good)
            
            # UI 反馈
            status_symbol = "👍" if is_good else "👎"
            self.set_status(f"感谢评价！已记录为 {status_symbol}", "green")
            
            # ⭐ 核心修改：评价后清除 ID，防止对同一条记录重复评价
            self.last_log_id = None 
        else:
            self.set_status("请先执行一个指令再评价", "gray")

    def _async_task(self, text):
        # 1. 显示用户输入 (蓝色)
        self.after(0, lambda: self.append_history("USER", text, "user"))
        
        self.set_status("⏳ AI 正在思考逻辑...", "yellow")
        context_desc = self.ctx.get_scene_description()
        
        try:
            # 2. 规划
            plan = plan_with_ai(text, context_desc)
            self.after(0, lambda: self.append_history("PLAN", plan.split('\n')[0] + "...", "ai_plan"))
            
            # 3. 解析
            steps = parse_with_ai(plan, context_desc)
            
            # 如果 AI 拒绝执行（例如物体不存在），将 AI 的回复直接打印出来
            if not steps:
                # 尝试从 plan 中提取 AI 的解释文本
                reason = plan if "exist" in plan.lower() or "not" in plan.lower() else "指令无法解析"
                self.after(0, lambda: self.append_history("AI", reason, "error"))
                self.set_status("💬 AI 提示: 操作不可行", "orange")
                self.after(0, lambda: self.btn.configure(state="normal"))
                return

            # 4. 执行
            for step in steps:
                self.after(0, lambda s=step: self.append_history("EXEC", f"调用工具: {s['tool']}", "exec"))
                self._execute_single_step(step)

            # 5. 刷新视图
            self.ctx.update_context(steps)
            self.after(0, lambda: self.viewer.update_shapes(self.ctx.get_visible_shapes()))
            self.set_status("✅ 执行成功", "green")

        except Exception as e:
            self.after(0, lambda: self.append_history("FATAL", str(e), "error"))
            self.set_status("❌ 运行出错", "red")
        
        self.after(0, lambda: self.btn.configure(state="normal"))
        self.last_log_id = self.logger.log(text, context_desc, plan, steps, status="success")

    def _execute_single_step(self, step):
        raw_tool = step.get("tool", "").lower()
        
        # 拦截系统指令，确保不被翻译成错误的建模工具
        if raw_tool in ["reset", "delete", "export"]:
            tool = raw_tool
        else:
            tool = self.translator.translate(raw_tool)
        
        args = step.get("args", {})
        name = step.get("name") or f"obj_{uuid.uuid4().hex[:4]}"

        # 功能 1：Reset (仅清空画面)
        if tool == "reset":
            self.ctx.visible_names.clear() 
            self.ctx.last_target = None
            self.after(0, lambda: self.viewer.update_shapes([]))
            print("🧹 视图已清空（物体数据已保留在后台）")
            return
        
        if tool == "remove":
            target = args.get("shape") or name # 优先取参数里的名字
            if target in self.ctx.shape_pool:
                del self.ctx.shape_pool[target]
                if target in self.ctx.visible_names:
                    self.ctx.visible_names.remove(target)
                if target in self.ctx.shape_metadata:
                    del self.ctx.shape_metadata[target]
                print(f"🔥 已移除指定物体: {target}")
            return

        # 功能 2：Delete (彻底清空数据)
        if tool == "delete":
            self.ctx.shape_pool.clear()
            self.ctx.visible_names.clear()
            self.ctx.shape_metadata.clear()
            self.ctx.last_target = None
            self.ctx.history_steps.clear()
            self.after(0, lambda: self.viewer.update_shapes([]))
            print("🗑️ 所有物体已删除，场景彻底重置")
            return

        if tool == "export":
            visible_shapes = self.ctx.get_visible_shapes()
            if not visible_shapes:
                print("⚠️ 导出终止：当前场景没有可见物体")
                return
            
            # 1. 锁定项目根目录 (即 main.py 所在的文件夹)
            src_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(src_dir) # 这才是 cad-copilot 根目录

            export_dir = os.path.join(project_root, "exports")
            
            # 如果文件夹不存在则创建
            if not os.path.exists(export_dir):
                os.makedirs(export_dir)

            # 2. 生成带时间戳的文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            raw_filename = args.get("filename", "model")
            
            # 清洗 AI 提供的名称
            clean_name = "".join([c for c in str(raw_filename) if c.isalnum() or c in ('_', '-')]).strip()
            if clean_name.lower().endswith("stl"): clean_name = clean_name[:-3]
            
            # 最终合成路径：项目目录/exports/名称_时间戳.stl
            filename = f"{clean_name}_{timestamp}.stl"
            full_path = os.path.join(export_dir, filename)
            
            try:
                from tools import export_to_stl
                success = export_to_stl(visible_shapes, full_path)
                if success:
                    print(f"💾 模型已安全导出至项目目录: {full_path}")
            except Exception as e:
                print("❌ 导出失败:", str(e))
            return
        
        # 3. 处理可见性
        if tool == "visibility":
            target = args.get("shape")
            action = args.get("action")
            
            if target not in self.ctx.shape_pool:
                for real_name in self.ctx.shape_pool.keys():
                    if real_name in str(target):
                        target = real_name
                        break

            if action == "show_only":
                self.ctx.visible_names = {target} if target in self.ctx.shape_pool else set()
            elif action in ["show", "visible"]:
                if target in self.ctx.shape_pool:
                    self.ctx.visible_names.add(target)
            elif action in ["hide", "invisible"]:
                self.ctx.hide_shape(target)
            
            print("👁️ 可见性调整:", target, "->", action)
            return

        # 4. 处理几何建模工具
        if tool in TOOLS:
            if tool == "translate":
                target = args.get("shape") or self.ctx.last_target
                if not target or target not in self.ctx.shape_pool: return
                
                self.ctx.visible_names.add(target)
                new_shape = TOOLS["translate"](self.ctx.shape_pool[target], 
                                              x=args.get('x',0), y=args.get('y',0), z=args.get('z',0))
                
                old_meta = self.ctx.shape_metadata.get(target, {"pos": [0,0,0]})
                new_pos = [old_meta['pos'][0] + args.get('x',0), 
                           old_meta['pos'][1] + args.get('y',0), 
                           old_meta['pos'][2] + args.get('z',0)]
                self.ctx.add_shape(target, new_shape, params={**old_meta, "pos": new_pos})

            elif tool in ["sphere", "cylinder", "box"]:
                # 修复点：确保 safe_args 的构建过程不会因为 float 转换报错
                safe_args = {}
                for k, v in args.items():
                    try:
                        # 只有当 v 是字符串且看起来像数字时才转换
                        if isinstance(v, str) and (v.replace('.','',1).replace('-','',1).isdigit()):
                            safe_args[k] = float(v)
                        else:
                            safe_args[k] = v
                    except:
                        safe_args[k] = v

                new_shape = TOOLS[tool](**safe_args)
                self.ctx.add_shape(name, new_shape, params={
                    "type": tool, "args": safe_args, "pos": safe_args.get("position", [0,0,0])
                })

            elif tool in ["cut", "fuse", "common"]:
                s1_name = args.get('shape1')
                s2_name = args.get('shape2')
            
                if s1_name in self.ctx.shape_pool and s2_name in self.ctx.shape_pool:
                    s1 = self.ctx.shape_pool[s1_name]
                    s2 = self.ctx.shape_pool[s2_name]
                    new_shape = TOOLS[tool](s1, s2)
                    
                    self.ctx.visible_names.clear() 
                    res_name = name if "obj_" not in name else f"{tool}_result_{uuid.uuid4().hex[:4]}"
                    
                    self.ctx.add_shape(res_name, new_shape, params={"type": tool, "pos": [0,0,0]})
                    self.ctx.visible_names.add(res_name) 
                    self.ctx.last_target = res_name 
                    print("✅ 布尔运算成功:", res_name)

        # 安全打印 2：彻底弃用末尾的 f-string 打印
        print("执行详情 -> 工具:", tool, " | 参数:", args)

if __name__ == "__main__":
    app = CADGui()
    app.mainloop()