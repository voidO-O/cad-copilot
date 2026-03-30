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
        print(f"DEBUG: 日志绝对路径为 -> {self.log_file}")

    def log(self, user_input, scene_context, plan, steps, status="success", error_msg=""):
        """记录交互并实时打印到终端"""
        timestamp = datetime.datetime.now().isoformat()
        
        # 构造结构化数据
        record = {
            "timestamp": timestamp,
            "data": {
                "user_input": user_input,
                "scene_before": scene_context,
                "ai_plan": plan,
                "parsed_steps": steps,
                "execution_status": status,
                "error_message": error_msg,
                "feedback": None  # 预留反馈字段
            }
        }

        # 1. 写入文件 (JSONL)
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
            f.flush()  # ⭐ 强制将缓冲区内容写入硬盘
            os.fsync(f.fileno()) # ⭐ 确保操作系统层面的写入

        # 2. 漂亮地打印到终端 (终端调试神器)
        self._print_to_terminal(timestamp, user_input, status, error_msg)
        
        return timestamp # 返回时间戳作为这条记录的唯一标识，用于后续更新反馈

    def _print_to_terminal(self, ts, user_input, status, error):
        """格式化终端输出"""
        color = Color.GREEN if status == "success" else Color.RED
        print(f"\n{Color.BOLD}{Color.CYAN}--- Interaction Log [{ts}] ---{Color.END}")
        print(f"{Color.BOLD}User Input:{Color.END} {user_input}")
        print(f"{Color.BOLD}Status:{Color.END} {color}{status.upper()}{Color.END}")
        if error:
            print(f"{Color.BOLD}Error:{Color.END} {Color.YELLOW}{error}{Color.END}")
        print(f"{Color.CYAN}--------------------------------------{Color.END}\n")

    def update_feedback(self, timestamp, is_good):
        """
        根据时间戳找到记录并更新用户反馈 (👍/👎)
        这是 RLHF 数据准备的关键步骤
        """
        temp_file = self.log_file.with_suffix('.tmp')
        found = False
        
        with open(self.log_file, 'r', encoding='utf-8') as f_in, \
             open(temp_file, 'w', encoding='utf-8') as f_out:
            for line in f_in:
                data = json.loads(line)
                if data['timestamp'] == timestamp:
                    data['data']['feedback'] = "GOOD" if is_good else "BAD"
                    found = True
                f_out.write(json.dumps(data, ensure_ascii=False) + "\n")
        
        os.replace(temp_file, self.log_file)
        if found:
            status_text = f"{Color.GREEN}👍 GOOD{Color.END}" if is_good else f"{Color.RED}👎 BAD{Color.END}"
            print(f"✅ 已更新反馈: {status_text} (ID: {timestamp})")