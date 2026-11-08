"""Runs the whole pipeline. Examples:
    python run_all.py --episodes 42        (test on one episode)
    python run_all.py --limit 3            (first 3 episodes)
    python run_all.py                      (all episodes; safe to re-run, finished episodes are cached)
    python run_all.py --fresh              (ignore the cache and redo everything)
"""
import argparse
import json
import time
import traceback
from collections import Counter
from pathlib import Path

import llm
from parse import parse_episode
from prompt_utils import prepare
from find import find_candidates, repair_candidate
from validate import validate_candidate
from judge import judge_candidate
from rank import final_score, rank_all, to_markdown

EPISODES_DIR = Path("episodes")
OUT = Path("outputs")
CACHE = OUT / "cache"


def process_episode(ep):
    """Find -> validate (repair length once) -> judge. Returns a dict of valid and rejected picks."""
    cands, raw = find_candidates(ep)
    valid, rejected, repaired = [], [], 0
    for cand in cands:
        ok, reason, res = validate_candidate(ep, cand)
        if not ok and reason.startswith(("too_long", "too_short")):
            fixed = repair_candidate(ep, cand, reason)
            if fixed:
                repaired += 1
                ok, reason, res = validate_candidate(ep, fixed)
        if not ok:
            rejected.append({"episode": ep["episode"], "candidate": cand, "reason": reason})
            continue
        scores = judge_candidate(ep, res)
        if scores is None:
            rejected.append({"episode": ep["episode"], "candidate": cand, "reason": "judge_failed"})
            continue
        res["scores"], res["final"] = scores, final_score(scores)
        valid.append(res)
    return {"episode": ep["episode"], "raw_find": raw, "valid": valid, "rejected": rejected, "repaired": repaired}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--episodes", type=int, nargs="*", help="only these episode numbers")
    ap.add_argument("--limit", type=int, help="only the first N episode files")
    ap.add_argument("--fresh", action="store_true", help="ignore cached results")
    ap.add_argument("--top", type=int, default=10, help="how many promos in ranking.md")
    args = ap.parse_args()

    OUT.mkdir(exist_ok=True)
    CACHE.mkdir(exist_ok=True)
    files = sorted(EPISODES_DIR.glob("*.txt"))
    if args.limit:
        files = files[:args.limit]

    start, results, errors = time.time(), [], []
    for f in files:
        ep = prepare(parse_episode(f))
        if args.episodes and ep["episode"] not in args.episodes:
            continue
        cache_file = CACHE / f'ep_{ep["episode"]:03d}.json'
        if cache_file.exists() and not args.fresh:
            print(f'Episode {ep["episode"]}: loaded from cache')
            results.append(json.loads(cache_file.read_text(encoding="utf-8")))
            continue
        print(f'Episode {ep["episode"]}: working ...', flush=True)
        try:
            r = process_episode(ep)
            cache_file.write_text(json.dumps(r, indent=1), encoding="utf-8")
            results.append(r)
            print(f'  {len(r["valid"])} valid, {len(r["rejected"])} rejected')
        except Exception as e:  # keep going; re-run later to retry this episode
            errors.append(f'Episode {ep["episode"]}: {e}')
            print("  ERROR:", e)
            traceback.print_exc()

    all_valid = [c for r in results for c in r["valid"]]
    all_rejected = [x for r in results for x in r["rejected"]]
    ranked = rank_all(all_valid)

    (OUT / "all_candidates.json").write_text(json.dumps(ranked, indent=1), encoding="utf-8")
    (OUT / "rejected.json").write_text(json.dumps(all_rejected, indent=1), encoding="utf-8")
    (OUT / "ranking.md").write_text(to_markdown(ranked, args.top), encoding="utf-8")

    reasons = Counter(x["reason"].split(":")[0] for x in all_rejected)
    log = [f"Provider: {llm.PROVIDER}", f"Model: {llm.MODEL_NAME}",
           f"Episodes in this output: {len(results)}",
           f"AI calls in this run: {llm.STATS['calls']} (cached episodes cost 0)",
           f"Tokens in this run: {llm.STATS['input_tokens']} in, {llm.STATS['output_tokens']} out",
           f"Time this run: {time.time() - start:.0f} s",
           f"Valid promos: {len(all_valid)} (after removing duplicates: {len(ranked)})",
           f"Rejected: {len(all_rejected)}", f"Rejection reasons: {dict(reasons)}",
           f"Fixed by one length repair: {sum(r['repaired'] for r in results)}",
           f"Errors: {errors or 'none'}"]
    (OUT / "run_log.txt").write_text("\n".join(log) + "\n", encoding="utf-8")
    print("\n" + "\n".join(log))
    print("\nSaved to outputs/: ranking.md, all_candidates.json, rejected.json, run_log.txt")


if __name__ == "__main__":
    main()
