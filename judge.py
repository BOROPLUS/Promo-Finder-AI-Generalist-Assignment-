"""Step 4: a second AI call scores each promo. It sees ONLY the clip, like a brand-new viewer."""
import llm
from find import extract_json
from prompt_utils import short

JUDGE_PROMPT = """You are judging a promo clip for a vertical microdrama app. You see ONLY the clip below,
exactly like a viewer who has never seen the show. '--- CUT ---' marks a jump between moments.
Score each from 1 (poor) to 5 (excellent):
- hook: in the first 3 seconds, would a scrolling viewer stop?
- cliffhanger: does it end at an unresolved moment that makes you need the next part?
- standalone: can a stranger follow who is who and what is happening?
Return ONLY JSON: {{"hook": 1-5, "hook_reason": "...", "cliffhanger": 1-5, "cliffhanger_reason": "...", "standalone": 1-5, "standalone_reason": "..."}}

CLIP:
{clip}
"""


def clip_text(ep, resolved):
    """The words and actions of the promo in order, with CUT markers between segments."""
    parts = []
    for s in resolved["segments"]:
        i, j = ep["index"][s["start_block"]], ep["index"][s["end_block"]]
        lines = []
        for b in ep["blocks"][i:j + 1]:
            who = b["who"] if b["kind"] == "dialogue" else f'({b["kind"].upper()})'
            lines.append(f"{who}: {short(b['text'])}")
        parts.append("\n".join(lines))
    return "\n--- CUT ---\n".join(parts)


def judge_candidate(ep, resolved):
    """Return a dict of scores and reasons, or None if the AI reply could not be used."""
    prompt = JUDGE_PROMPT.format(clip=clip_text(ep, resolved))
    for _ in range(2):
        try:
            data = extract_json(llm.call_llm(prompt, temperature=0))
            scores = {k: min(5, max(1, int(data[k]))) for k in ("hook", "cliffhanger", "standalone")}
            for k in ("hook_reason", "cliffhanger_reason", "standalone_reason"):
                scores[k] = str(data.get(k, ""))
            return scores
        except (ValueError, KeyError, TypeError):
            continue
    return None
