import re

def parse_command(text):
    text = text.lower()

    if "cylinder" in text:
        radius = 10
        height = 20

        r = re.search(r"radius (\d+)", text)
        h = re.search(r"height (\d+)", text)

        if r:
            radius = int(r.group(1))
        if h:
            height = int(h.group(1))

        return {
            "type": "cylinder",
            "radius": radius,
            "height": height
        }

    return None