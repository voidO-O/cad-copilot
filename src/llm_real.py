from openai import OpenAI
import json

client = OpenAI(
    api_key="sk-qEQIeuwp652b984v43CbF438E01a403087119d4946Ce0aB8",
    base_url="https://aihubmix.com/v1"
)

def parse_with_ai(text, context_info=""):
    prompt = f"""
    You are a CAD assistant. 
    {context_info}  # 这里会传入当前场景有哪些物体

    Task: Convert user input into CAD steps.
    If the user says "it" or "move that", refer to the last created object.

Your task:
Convert the input into CAD steps.

STRICT RULES:
1. You MUST assign a unique name to every created object.
2. Use names like: s1, c1, obj1, etc.
3. Boolean operations MUST reference objects by name.

SCATIAL LOGIC:
- "center" or default: position [0, 0, 0]
- "left": use negative X (e.g., [-50, 0, 0])
- "right": use positive X (e.g., [50, 0, 0])
- "above/top": use positive Z (e.g., [0, 0, 50])
- "far left": use even smaller X (e.g., [-100, 0, 0])

Return ONLY JSON (no explanation):

Example:
[
  {{
    "tool": "sphere",
    "name": "s1",
    "args": {{
      "radius": 10,
      "position": [0, 0, 0]
    }}
  }},
  {{
    "tool": "cylinder",
    "name": "c1",
    "args": {{
      "radius": 5,
      "height": 20,
      "position": [5, 0, 0]
    }}
  }},
  {{
    "tool": "common",
    "name": "result",
    "args": {{
      "shape1": "s1",
      "shape2": "c1"
    }}
  }}
]

User input:
"{text}"
"""


    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    content = response.choices[0].message.content

    # ===== 清洗AI返回 =====
    content = content.strip()

    if content.startswith("```"):
        content = content.replace("```json", "")
        content = content.replace("```", "")
        content = content.strip()

    # ===== 解析JSON =====
    try:
        return json.loads(content)
    except Exception as e:
        print("❌ JSON解析失败")
        print("AI返回内容:", content)
        print("错误信息:", e)
        return None