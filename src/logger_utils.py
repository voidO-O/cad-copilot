import json
import os
import datetime
from pathlib import Path

# 使用简单的颜色代码，增加终端可读性
class Color:
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    DARKCYAN = '\033[36m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

class InteractionLogger:
    def __init__(self, log_dir_name="logs"):
        # 获取当前文件 (logger_utils.py) 的绝对路径
        current_file = Path(__file__).resolve()
        # 假设 src 和 logs 在同级目录，那么根目录就是 src 的上一级
        self.project_root = current_file.parent.parent 
        
        self.log_dir = self.project_root / log_dir_name
        self.log_dir.mkdir(exist_ok=True)
        
        self.log_file = self.log_dir / "interaction_history.jsonl"
        # 仅在初始化时打印一次路径，减少干扰
        print(f"{Color.DARKCYAN}[Logger] 日志路径: {self.log_file}{Color.END}")

    def log(self, user_input, scene_context, status, steps, result_msg=""):
        """
        记录交互到文件。
        注意：此处已彻底移除终端打印逻辑，所有打印由 controller.py 统一负责。
        """
        timestamp = datetime.datetime.now().isoformat()
        
        # 构造结构化数据
        record = {
            "timestamp": timestamp,
            "data": {
                "user_input": user_input,
                "scene_context": scene_context, # 这里的 context 建议在 session_context 里过滤掉 volume 
                "parsed_steps": steps,
                "execution_status": status,
                "result_message": result_msg,
                "feedback": None
            }
        }

        # 写入文件 (JSONL)
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
                f.flush()
                os.fsync(f.fileno())
        except Exception as e:
            # 只有文件写入失败这种严重错误才打印
            print(f"{Color.RED}[Logger Error] 写入失败: {e}{Color.END}")
        
        return timestamp

    def update_feedback_last_record(self, is_good):
        """
        找到最后一条日志记录并更新其反馈状态
        """
        if not self.log_file.exists():
            return
        
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            if not lines:
                return
            
            # 解析最后一行
            last_entry = json.loads(lines[-1])
            
            # 在 data 字典中添加或更新 feedback
            if 'data' not in last_entry:
                last_entry['data'] = {}
            last_entry['data']['feedback'] = "GOOD" if is_good else "BAD"
            
            # 写回最后一行
            lines[-1] = json.dumps(last_entry, ensure_ascii=False) + '\n'
            
            with open(self.log_file, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            
            # 这是一个非常有用的交互反馈，可以保留
            feedback_icon = f"{Color.GREEN}👍{Color.END}" if is_good else f"{Color.RED}👎{Color.END}"
            print(f"✅ 反馈已记录: {feedback_icon}")
            
        except Exception as e:
            print(f"{Color.RED}❌ 更新反馈失败: {e}{Color.END}")