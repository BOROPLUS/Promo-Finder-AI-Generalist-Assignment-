"""Step 2: ask the AI for candidate promos. It answers with block IDs, never timestamps."""
import json
import re
import llm
from prompt_utils import to_prompt_text, label_of, short

FIND_PROMPT = """You are an editor choosing promo clips for a vertical microdrama app (like ReelShort or DramaBox).
A promo is 20-60 seconds in total, built from 1 to 3 segments of THIS episode, in time order. It must:
(a) open on a hook: in the first 3 seconds something makes a scrolling viewer stop, like a slap, a reveal or a shocking line,
(b) end on a cliffhanger: cut at an unresolved moment so the viewer needs to know what happens next,
(c) make sense to someone who has never seen the show.
Pick 3 different candidates that do not overlap much. Use ONLY the block IDs given. Never write timestamps.
Return ONLY JSON, no extra text, as a list of objects with keys:
segments (list of {{"start_block": "B010", "end_block": "B020"}}), hook (one line), cliffhanger (one line), why (one line).

Episode logline: {logline}
Continuity notes: {continuity}

Script blocks (ID, start-end seconds, speaker or type, text):
{script}
"""

REPAIR_PROMPT = """A promo candidate was rejected: {reason}
Fix it by changing ONLY the segments (use only block IDs from the script below, never timestamps) so the total length is 20-60 seconds,
the clip still opens on a hook and ends on a cliffhanger. Return ONLY the corrected JSON object with the same keys
(segments, hook, cliffhanger, why).

Rejected candidate:
{candidate}

Script blocks:
{script}
"""


def extract_json(text):
    """Pull the first JSON list or object out of an AI reply (handles ```json fences)."""
    text = re.sub(r"```(?:json)?", "", text).strip()
    starts = [p for p in (text.find("["), text.find("{")) if p != -1]
    if not starts:
        raise ValueError("no JSON found")
    start = min(starts)
    end = text.rfind("]" if text[start] == "[" else "}")
    return json.loads(text[start:end + 1])


def find_candidates(ep):
    """Return (list of candidate dicts, raw AI reply). Retries once if the JSON is broken."""
    prompt = FIND_PROMPT.format(logline=ep["logline"], continuity=ep["continuity"],
                                script=to_prompt_text(ep))
    raw = llm.call_llm(prompt)
    for attempt in range(2):
        try:
            data = extract_json(raw)
            if isinstance(data, dict):
                data = [data]
            return [c for c in data if isinstance(c, dict)], raw
        except (ValueError, json.JSONDecodeError):
            if attempt == 1:
                return [], raw
            raw = llm.call_llm(prompt + "\n\nYour last reply was not valid JSON. Return ONLY the JSON list.")
    return [], raw


def repair_candidate(ep, cand, reason):
    """Ask the AI once to fix a rejected candidate using only the blocks near the referenced IDs."""
    # Collect positions of every block ID mentioned in the candidate's segments
    ids = [seg.get(k, "") for seg in cand.get("segments", []) for k in ("start_block", "end_block")]
    positions = [ep["index"][bid] for bid in ids if bid in ep.get("index", {})]
    if positions:
        lo = max(0, min(positions) - 20)
        hi = min(len(ep["blocks"]), max(positions) + 21)
        script = "\n".join(
            f'[{b["id"]}] {b["start"]:.1f}-{b["end"]:.1f} | {label_of(b)}: {short(b["text"])}'
            for b in ep["blocks"][lo:hi])
    else:
        script = to_prompt_text(ep)   # fallback: no recognised IDs found
    prompt = REPAIR_PROMPT.format(reason=reason, candidate=json.dumps(cand), script=script)
    try:
        data = extract_json(llm.call_llm(prompt))
        return data[0] if isinstance(data, list) and data else data
    except (ValueError, json.JSONDecodeError):
        return None


if __name__ == "__main__":  # quick test on one episode: python find.py
    import sys
    from pathlib import Path
    from parse import parse_episode
    from prompt_utils import prepare
    files = sorted(Path("episodes").glob("*042*.txt")) or sorted(Path("episodes").glob("*.txt"))
    ep = prepare(parse_episode(files[0]))
    cands, raw = find_candidates(ep)
    Path("outputs").mkdir(exist_ok=True)
    Path("outputs/raw_find_test.txt").write_text(raw, encoding="utf-8")
    print(json.dumps(cands, indent=2))
