"""Step 5: combine scores, drop near-duplicates, rank all promos across all episodes."""
from validate import dedupe
from prompt_utils import mmss

WEIGHTS = {"hook": 0.35, "cliffhanger": 0.35, "standalone": 0.30}  # my choice; easy to change
LOW_STANDALONE_PENALTY = 1.0   # a promo nobody understands should not be posted first
TARGET_LENGTH = 40.0           # tie-break: prefer promos close to this length


def final_score(sc):
    """Weighted score out of 5, minus a penalty if the clip is confusing on its own."""
    s = sum(WEIGHTS[k] * sc[k] for k in WEIGHTS)
    return round(s - (LOW_STANDALONE_PENALTY if sc["standalone"] < 3 else 0), 3)


def rank_all(cands):
    """Dedupe inside each episode, then sort everything. Adds 'rank' to each promo."""
    kept = dedupe(cands, key=lambda c: c["final"])
    kept.sort(key=lambda c: (-c["final"], abs(c["duration"] - TARGET_LENGTH)))
    for n, c in enumerate(kept, start=1):
        c["rank"] = n
    return kept


def why_ranked(c):
    """One line built from the numbers, so the order is easy to defend."""
    sc = c["scores"]
    note = " Penalised: hard to follow without context." if sc["standalone"] < 3 else ""
    return (f'Scores: hook {sc["hook"]}, cliffhanger {sc["cliffhanger"]}, '
            f'clear on its own {sc["standalone"]}; final {c["final"]}; {c["duration"]:.0f}s long.{note}')


def to_markdown(ranked, top_n=10):
    """The ranking file: a short table, then the full detail for each top promo."""
    top = ranked[:top_n]
    out = [f"# Top {len(top)} promos (ranked)\n",
           "| Rank | Episode | Length | Final score |", "|---|---|---|---|"]
    out += [f'| {c["rank"]} | {c["episode"]} | {c["duration"]:.0f}s | {c["final"]} |' for c in top]
    for c in top:
        out.append(f'\n### #{c["rank"]}: Episode {c["episode"]} ({c["duration"]:.0f}s)')
        for s in c["segments"]:
            out.append(f'- Segment: {mmss(s["start"])} to {mmss(s["end"])} ({s["start_block"]} to {s["end_block"]})')
        out += [f'- **Hook:** {c["hook"]}', f'- **Cliffhanger:** {c["cliffhanger"]}',
                f'- **Why it works:** {c["why"]}', f'- **Why ranked here:** {why_ranked(c)}']
    return "\n".join(out) + "\n"
