import re, json, sys

TIME = r"\((\d+):(\d+\.\d+)\)"
BLOCK = re.compile(
    r"\*\*(?P<who>[^*]+?):\*\*\s*\n"
    r"Start: " + TIME + r" \| End: " + TIME + r"\s*\n"
    r"(?P<text>.*?)(?=\n\*\*|\nSCENE |\n--- SCRIPT END|\Z)", re.S)

def secs(m, s):
    return int(m) * 60 + float(s)

def parse_episode(path):
    raw = open(path, encoding="utf-8").read()
    num = re.search(r"EPISODE NUMBER:\s*Episode (\d+)", raw)
    logline = re.search(r"EPISODE LOGLINE:\s*(.*)", raw)
    notes = re.search(r"CONTINUITY NOTES:\s*(.*)", raw)
    blocks = []
    for m in BLOCK.finditer(raw):
        who = m.group("who").strip()
        kind = "camera" if who == "CAMERA" else "action" if who == "ACTION" else "dialogue"
        g = m.groups()
        blocks.append({
            "kind": kind, "who": who,
            "start": secs(g[1], g[2]), "end": secs(g[3], g[4]),
            "text": m.group("text").strip(),
        })
    return {
        "episode": int(num.group(1)) if num else None,
        "logline": logline.group(1).strip() if logline else "",
        "continuity": notes.group(1).strip() if notes else "",
        "blocks": blocks,
    }

if __name__ == "__main__":
    ep = parse_episode(sys.argv[1])
    print(ep["episode"], len(ep["blocks"]), "blocks; last end =", ep["blocks"][-1]["end"])
    print(json.dumps(ep["blocks"][:3], indent=1))
