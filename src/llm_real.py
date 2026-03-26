from openai import OpenAI
import json

client = OpenAI(
    api_key="sk-qEQIeuwp652b984v43CbF438E01a403087119d4946Ce0aB8",
    base_url="https://aihubmix.com/v1"
)

def parse_with_ai(text):
    prompt = f"""
    You are a CAD assistant.

    Extract parameters from user input:
    "{text}"

    Return ONLY JSON like:
    {{
        "type": "cylinder",
        "radius": 10,
        "height": 20
    }}
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    content = response.choices[0].message.content

    try:
        return json.loads(content)
    except:
        print("AI返回内容:", content)
        return None