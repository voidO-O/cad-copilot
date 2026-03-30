from openai import OpenAI
import json
import re
import uuid

client = OpenAI(
    api_key="sk-qEQIeuwp652b984v43CbF438E01a403087119d4946Ce0aB8",
    base_url="https://aihubmix.com/v1"
)

def plan_with_ai(user_input, context_info=""):
    """
    第一阶段：逻辑规划。
    重点：强化对布尔运算语义（交集、并集、差集）的识别，防止 AI 试图通过移动位置来“模拟”交集。
    """
    system_prompt = """You are a high-precision CAD Logic Planner.
STRATEGIC RULES:
1. SEMANTIC MAPPING:
   - "Intersection", "Common", "Overlap", "Keep only where they meet" -> ALWAYS use 'boolean common'.
   - "Subtract", "Remove", "Cut out", "Minus" -> ALWAYS use 'boolean cut'.
   - "Combine", "Add", "Join", "Merge" -> ALWAYS use 'boolean fuse'.
   
2. ATOMIC STEPS: Break into: [Creation] -> [Adjustment/Translation] -> [Boolean Operation] -> [Visibility Adjust].

3. SPATIAL CALCULATIONS:
   - If Placing B on top of A: B.Z = A.Z + (A.Height or A.Radius).
   - Translation is RELATIVE (offset).

4. DO NOT use 'translate' to represent a boolean result. Boolean results in a NEW object.

5. If the user asks to "Show A and B", but A or B do not exist in the [CONTEXT], 
  tell the user they need to be created first, OR only create them if the user explicitly asked for creation.
  
6. DO NOT hallucinate default positions [0,0,0] for objects that were previously moved.

[SPATIAL ALIGNMENT RULES]:
- Sphere (球体): Position [x,y,z] is the CENTER. Radius R means Top_Z = z+R, Bottom_Z = z-R.
- Cylinder (圆柱): Position [x,y,z] is the CENTER OF THE BOTTOM BASE. Height H means Top_Z = z+H.
- TO PLACE B ON TOP OF A:
    1. If A is Sphere: B_base_Z = A_center_Z + A.radius.
    2. If A is Cylinder: B_base_Z = A_base_Z + A.height.
- EXAMPLE: If s1 is a sphere (r=3) at [0,0,0], placing c1 on top of it means c1's position is [0,0,3].

[COMMAND SCOPE]:
- If user says "Delete [name]", ONLY use the 'remove' tool for that specific name.
- ONLY use 'delete' tool when user says "delete all", "clear everything" or "reset database".

[STRICT OPERATIONAL HIERARCHY]:
1. VISIBILITY FIRST: If the user wants to 'show', 'hide', or 'only show' an object that already exists in the context, you MUST ONLY use the 'visibility' tool. 
2. NO REDUNDANT CREATION: Do not use 'sphere', 'cylinder', or boolean tools to satisfy a visibility request.
3. SHOW_ONLY LOGIC: 'show_only' means showing the target and hiding EVERYTHING else.
- If the user asks to 'show', 'move', or 'operate' on an object (e.g., 's1') that IS NOT in the [SCENE CONTEXT], you MUST NOT create it.
- Instead, your plan should simply state: "Object [name] does not exist. Please create it first." 
- DO NOT generate 'sphere' or 'cylinder' tools unless the user explicitly said "create", "make", or "generate".

[MEMORY MANAGEMENT RULES]:
1. 'reset' only HIDES objects. They still exist in the [CONTEXT].
2. If the user says "Show the ball" after a reset, ONLY use {"tool": "visibility", "args": {"shape": "s1", "action": "show"}}.
3. NEVER re-create an object (e.g., using 'sphere') if it already exists in the [CONTEXT] asset list.
4. ONLY use 'delete' when the user explicitly says "delete everything" or "start a new project".

"""

    user_prompt = f"""[SCENE CONTEXT]
{context_info}

[USER REQUEST]
{user_input}

Output a numbered logical plan:"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0
    )
    return response.choices[0].message.content

# llm_real.py

def parse_with_ai(text, context_info=""):
    # 注意：这里去掉了开头的 f，改用普通字符串，防止 JSON 大括号被 Python 误解析
    system_prompt = """You are a CAD JSON Transpiler. Convert the provided plan into a strict JSON array.

[ALLOWED TOOLS & SCHEMAS]:
1. "sphere": {"tool": "sphere", "name": "s1", "args": {"radius": float, "position": [x,y,z]}}
2. "cylinder": {"tool": "cylinder", "name": "c1", "args": {"radius": float, "height": float, "position": [x,y,z]}}
3. "translate": {"tool": "translate", "args": {"shape": "name", "x": f, "y": f, "z": f}}
4. "common": {"tool": "common", "args": {"shape1": "n1", "shape2": "n2"}}
5. "cut": {"tool": "cut", "args": {"shape1": "n1", "shape2": "n2"}}
6. "fuse": {"tool": "fuse", "args": {"shape1": "n1", "shape2": "n2"}}
7. "visibility": {"tool": "visibility", "args": {"shape": "name", "action": "show"|"hide"|"show_only"}}
8. "reset": Clear the entire scene and all history. No arguments needed.
9. "export": Save current visible shapes to a file. Args: { "filename": "string" }
10. "delete": {"tool": "delete"} -> Completely wipe all objects and metadata from memory.

[CRITICAL LOGIC RULES]:
1. BOOLEAN RESULTS: When 'common', 'cut', or 'fuse' is performed, the original shapes are GONE. 
2. RESET: If user says "clear all", "reset", use the 'reset' tool.
3. EXPORT: If user says "save" or "export", use the 'export' tool.

[CONTEXT]:
 + str(context_info) # 手动拼接，避开 f-string 陷阱

    # ... 后面的请求逻辑保持不变
{context_info}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Plan to Transpile: {text}"}
            ],
            temperature=0
        )

        content = response.choices[0].message.content.strip()
        
        # 稳健提取 JSON
        match = re.search(r'\[\s*\{.*\}\s*\]', content, re.DOTALL)
        if match:
            content = match.group()
        
        steps = json.loads(content)
        
        # 工业级二次校验与格式修补
        corrected_steps = []
        valid_tools = ["sphere", "cylinder", "translate", "common", "cut", "fuse", "visibility", "reset", "delete", "export","remove"]
        
        for s in steps:
            # 兼容性处理：如果 AI 输出了 {"tool": "boolean", "args": {"operation": "common"}}
            if s.get("tool") == "boolean":
                op = s.get("args", {}).get("operation", "").lower()
                if "inter" in op or "comm" in op: s["tool"] = "common"
                elif "union" in op or "fuse" in op: s["tool"] = "fuse"
                elif "cut" in op or "sub" in op: s["tool"] = "cut"

            # 结构标准化
            if "tool" in s and s["tool"] in valid_tools:
                # 确保 Creation 工具必有 name
                if s["tool"] in ["sphere", "cylinder"] and "name" not in s:
                    s["name"] = f"obj_{uuid.uuid4().hex[:4]}"
                corrected_steps.append(s)
            else:
                # 模糊键修复 (例如 AI 直接写了 {"sphere": {...}})
                for t in valid_tools:
                    if t in s:
                        corrected_steps.append({
                            "tool": t,
                            "name": s.get("name", f"obj_{uuid.uuid4().hex[:4]}"),
                            "args": s[t] if isinstance(s[t], dict) else s.get("args", {})
                        })
                        break
        return corrected_steps

    except Exception as e:
        print(f"❌ LLM 解析异常: {e}\nRaw: {content}")
        return None

def repair_with_ai(failed_step, error_msg, context_info):
    """
    第三阶段：自我修复。
    """
    prompt = f"""The CAD system failed to execute a step.
Context: {context_info}
Failed Step: {failed_step}
Error: {error_msg}

Task: Provide a corrected JSON list to fix this error. ONLY return JSON."""
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    content = response.choices[0].message.content.strip()
    match = re.search(r'\[.*\]', content, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except:
            return None
    return None