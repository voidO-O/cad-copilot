import json
import re
import uuid
import os
from openai import OpenAI

# 终端颜色定义
class Color:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    END = '\033[0m'

# 初始化客户端
client = OpenAI(
    api_key="sk-qEQIeuwp652b984v43CbF438E01a403087119d4946Ce0aB8",
    base_url="https://aihubmix.com/v1"
)

def plan_with_ai(user_input, context_info=""):
    """
    核心规划函数：将用户意图转化为标准的 CAD 操作 JSON。
    """
    system_prompt = """You are a CAD Engine Controller (Agent). Convert unstructured instructions into a standard JSON array.

[CORE AGENTIC RULES]:
1. TOOL CALLING: Use ONLY defined tools.
2. DETERMINISTIC OUTPUT: Return ONLY a valid JSON array. No explanations.
3. MATH RULE: ALWAYS output final calculated numbers. DO NOT output formulas like "8+15".
4. RESET RULE: If "reset" is called, ALL previous IDs (obj_xxx, res_xxx) are invalidated. NEVER reference them after a reset.
5. DEPENDENCY CHECK: Never reference an ID that was not created in the current or previous successful steps.
6. NO BOX TOOL: Note that 'box' is NOT available. If asked to subtract from a box, explain you cannot create boxes or skip the operation.
7. TARGET SELECTION: When asked to move "the second" or "last" object, look at [SCENE CONTEXT] and use the ID of the most recently created valid shape.

[ID REFERENCING PROTOCOL]:
- If you are creating a new object and immediately using it in the SAME JSON, use placeholders like "NEW_1", "NEW_2".
- If you are referencing EXISTING objects, look at [SCENE CONTEXT] and use the exact ID (e.g., obj_abcd).
- "The latest one" or "the sphere just created" always refers to the object you just defined in the current or previous step.


[TARGET SELECTION]
If the user specifies a color (e.g., 'blue cylinder'), check the [SCENE CONTEXT] for the most recent ID with both that tool type and color attribute.


[ALLOWED TOOLS & SCHEMAS]:
- "sphere": {"radius": float, "position": [x,y,z], "color": str}
- "cylinder": {"radius": float, "height": float, "position": [x,y,z], "color": str}
- "cone": {"radius": float, "height": float, "position": [x,y,z], "color": str}
- "torus": {"major_radius": float, "minor_radius": float, "position": [x,y,z], "color": str}
- "translate": {"shape": "ID", "x": float, "y": float, "z": float}
- "scale": {"shape": "ID", "factor": float}
- "boolean_cut/boolean_fuse/boolean_common": {"shape1": "ID", "shape2": "ID"}
- "delete": {"shape": "ID"}
- "reset": {}
- "export_stl": {"filename": "string"}

[ANCHOR POINT & SPATIAL RULES]:
- Sphere/Torus: Position = CENTER. (Top = Z+R, Bottom = Z-R)
- Cylinder/Cone: Position = BOTTOM BASE CENTER. (Top = Z+Height, Bottom = Z)
- Placement Formula:
- To place B on top of A: B.Z_base = A.Z_top + Gap.
- If B is a Sphere on top of A: B.Z_center = A.Z_top + Gap + B.Radius.

🌟 IMPORTANT RULE FOR MULTI-STEP OPERATIONS 🌟
When performing multiple boolean operations, you MUST use the result of the previous operation.
Example: If you want to fuse A, B, and C.
1. {"tool": "boolean_fuse", "args": {"shape1": "A", "shape2": "B"}} -> This will automatically generate a new ID in the registry, e.g., 'res_fuse_1234'.
2. The NEXT step to add C MUST use 'res_fuse_1234' (or whatever ID the system generates) as 'shape1' and 'C' as 'shape2'.
DO NOT invent names like 'NEW_4' or 'IntermediateResult'. If you are unsure of the result ID, just refer to "the result of step [N]".    

CRITICAL: Never nest shape definitions inside boolean arguments. Always create the shape first, then reference its ID.

CRITICAL RULE:
When using boolean tools (fuse, cut, common), if you are unsure of the object's ID, you MUST use the string "LAST_OBJ_1", "LAST_OBJ_2" to refer to the most recently created objects, or "PREVIOUS_RESULT" for the result of the last boolean operation.

Example:

sphere -> creates obj_A

cylinder -> creates obj_B

boolean_fuse -> use {"shape1": "LAST_OBJ_1", "shape2": "LAST_OBJ_2"}

[ENGINNER RULE]

增量原则：进行布尔减法（cut）时，shape1 必须是 PREVIOUS_RESULT（即已经处理过的半成品），除非这是第一步操作。严禁将 PREVIOUS_RESULT 与它的原始组件（LAST_OBJ）进行 fuse，这会导致孔洞被重新填满。

拓扑顺序：在建模复杂零件（如带孔的轴承座）时，逻辑应为：

第一步：创建所有基础零件（底座、轴套等）。

第二步：将所有基础零件 fuse 成一个整体。

第三步：在这个整体上，连续使用 cut 减去所有的孔（贯穿孔、盲孔、螺栓孔）。

精准寻址：如果你需要对第 N 个生成的物体操作，请数清楚。例如 LAST_OBJ_1 永远是上一行创建的对象。


[COLOR RULE]:
- Default color is 'gray'. Do NOT inherit color from existing objects unless asked.
"""

    user_prompt = f"[SCENE CONTEXT]\n{context_info}\n\n[USER REQUEST]\n{user_input}\n\nOutput JSON Array:"

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0
        )
        
        content = response.choices[0].message.content.strip()
        print(f"{Color.YELLOW}DEBUG AI 原文: {content}{Color.END}")

        # 数学计算预处理
        def eval_math(m):
            try: return str(eval(m.group(0), {"__builtins__": None}, {}))
            except: return m.group(0)
        
        processed_content = re.sub(r'(\d+(\.\d+)?\s*[\+\-\*\/]\s*\d+(\.\d+)?)', eval_math, content)
        
        match = re.search(r'\[.*\]', processed_content, re.DOTALL)
        if not match: return []
            
        steps = json.loads(match.group())

        valid_tools = [
            "sphere", "cylinder", "cone", "torus",
            "scale","translate", "boolean_cut", "boolean_fuse", "boolean_common",
            "reset", "delete", "export_stl"
        ]
        
        final_steps = []
        is_reset_active = False
        
        # --- 🌟 核心修复：占位符映射逻辑 🌟 ---
        temp_id_map = {} # 存储 NEW_1 -> obj_xxxx 的映射
        creation_idx = 0 # 记录当前批次创建了多少个物体

        for s in steps:
            if not isinstance(s, dict): continue
            
            # 平铺嵌套结构
            if "tool" not in s and len(s) == 1:
                p_tool = list(s.keys())[0]
                if isinstance(s[p_tool], dict):
                    s = {"tool": p_tool, "args": s[p_tool]}

            tool = str(s.get("tool", "")).lower()
            # 语义转换
            if "common" in tool: tool = "boolean_common"
            elif "cut" in tool: tool = "boolean_cut"
            elif "fuse" in tool or "union" in tool: tool = "boolean_fuse"
            
            s["tool"] = tool

            if tool == "reset":
                is_reset_active = True
                temp_id_map.clear()

            if tool in valid_tools:
                # 规范化参数
                if "args" not in s:
                    s["args"] = {k: v for k, v in s.items() if k not in ["tool", "name", "args"]}
                
                # 1. 如果是创建类工具，分配真实 UUID 并注册到映射表
                if tool in ["sphere", "cylinder", "cone", "torus"]:
                    creation_idx += 1
                    real_id = f"obj_{uuid.uuid4().hex[:4]}"
                    s["name"] = real_id
                    
                    # 注册 AI 可能使用的占位符
                    temp_id_map[f"new_{creation_idx}"] = real_id
                    # 容错：有些 AI 可能会吐出 "sphere_1" 或直接用 "obj_1"
                    temp_id_map[f"{tool}_{creation_idx}"] = real_id
                    temp_id_map[f"{tool}{creation_idx}"] = real_id
                    # 显式捕捉 AI 在 JSON 中定义的临时 name
                    if "name" in s["args"]:
                        temp_id_map[str(s["args"]["name"]).lower()] = real_id

                # 2. 核心：在执行之前，将 args 里的占位符替换为真实 ID
                for arg_key in ["shape", "shape1", "shape2"]:
                    if arg_key in s["args"]:
                        ref_id = str(s["args"][arg_key]).lower()
                        
                        # 处理 "latest" 关键字
                        if ref_id in ["latest", "last", "the_latest"]:
                            # 寻找最后一个创建的物体 ID
                            last_id = None
                            for prev in reversed(final_steps):
                                if "name" in prev:
                                    last_id = prev["name"]
                                    break
                            if last_id: s["args"][arg_key] = last_id
                        
                        # 处理 NEW_X 占位符映射
                        elif ref_id in temp_id_map:
                            s["args"][arg_key] = temp_id_map[ref_id]

                # 导出清洗
                # --- 🌟 优化 4: 导出路径深度加固 (存放至与 src 同级的 exports 文件夹) 🌟 ---
                if tool == "export_stl":
                    # 1. 提取原始文件名 (多级检索)
                    # 尝试从 args 中取，如果取不到再从 s 根目录取，最后给默认值
                    raw_fname = s.get("args", {}).get("filename") or s.get("filename") or "model_export.stl"
                    
                    # 2. 清洗文件名 (去掉路径幻觉，确保后缀)
                    pure_name = os.path.basename(str(raw_fname))
                    if not pure_name.lower().endswith(".stl"):
                        pure_name = f"{pure_name}.stl"

                    # 3. 计算绝对路径 (强制定位到 src 同级的 exports)
                    # os.path.abspath(__file__) 确保了路径起始点是脚本位置
                    script_path = os.path.abspath(__file__)
                    src_dir = os.path.dirname(script_path)
                    base_dir = os.path.dirname(src_dir)
                    export_dir = os.path.join(base_dir, "exports")

                    # 4. 自动创建文件夹
                    if not os.path.exists(export_dir):
                        try:
                            os.makedirs(export_dir, exist_ok=True)
                            print(f"{Color.GREEN}已自动创建导出目录: {export_dir}{Color.END}")
                        except Exception as e:
                            print(f"{Color.RED}创建目录失败: {e}，将使用当前目录{Color.END}")
                            export_dir = src_dir # 备选方案

                    # 5. 组合最终绝对路径
                    full_path = os.path.normpath(os.path.join(export_dir, pure_name))
                    
                    # 🌟 关键点：全字段覆盖，防止执行器读取旧的或错误的字段 🌟
                    if "args" not in s:
                        s["args"] = {}
                    
                    s["args"]["filename"] = full_path  # 更新 args 里的路径
                    s["filename"] = full_path         # 同时也更新根目录下的路径
                    
                    # 打印调试信息，确认路径是否正确
                    print(f"{Color.YELLOW}DEBUG: 预设导出路径 -> {full_path}{Color.END}")

                final_steps.append(s)
                
        return final_steps

    except Exception as e:
        print(f"\n{Color.RED}❌ AI 规划解析失败: {e}{Color.END}")
        return []

def repair_with_ai(failed_step, error_msg, context_info):
    """
    错误自我修正：当执行报错时，请求 AI 根据错误原因重新规划
    """
    prompt = f"""CAD Error!
[Context]: {context_info}
[Failed Step]: {json.dumps(failed_step)}
[Error Message]: {error_msg}
Provide a corrected JSON array to fix this. Ensure IDs exist in context."""
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        match = re.search(r'\[.*\]', response.choices[0].message.content, re.DOTALL)
        return json.loads(match.group()) if match else None
    except:
        return None