"""Step 3: check every AI pick with plain rules (no AI). Turns block IDs into exact timestamps."""

MIN_TOTAL, MAX_TOTAL = 20.0, 60.0   # promo length in seconds
HOOK_WITHIN = 3.0                    # first spoken line / action must start within 3 s
END_TOLERANCE = 2.0                  # clip must not end on a camera-only tail longer than this


def _fail(reason, msg=""):
    return False, f"{reason}: {msg}".strip(": "), None


def validate_candidate(ep, cand):
    """Return (ok, reason, resolved). 'resolved' holds exact start/end times when ok."""
    blocks, index = ep["blocks"], ep["index"]
    segs_in = cand.get("segments")
    if not isinstance(segs_in, list) or not 1 <= len(segs_in) <= 3:
        return _fail("bad_segments", "need a list of 1 to 3 segments")

    segs = []
    for s in segs_in:
        a, b = (s.get("start_block"), s.get("end_block")) if isinstance(s, dict) else (None, None)
        if a not in index or b not in index:
            return _fail("unknown_block_id", f"{a}-{b}")
        i, j = index[a], index[b]
        if i > j:
            return _fail("segment_reversed", f"{a}-{b}")
        chunk = blocks[i:j + 1]
        segs.append({"start_block": a, "end_block": b, "i": i, "j": j,
                     "start": round(min(x["start"] for x in chunk), 2),
                     "end": round(max(x["end"] for x in chunk), 2)})

    for prev, cur in zip(segs, segs[1:]):
        if cur["i"] <= prev["j"]:
            return _fail("segments_out_of_order_or_overlap", f'{prev["end_block"]} then {cur["start_block"]}')

    total = round(sum(s["end"] - s["start"] for s in segs), 2)
    if total > MAX_TOTAL:
        return _fail("too_long", f"total {total}s, must be {MIN_TOTAL:.0f}-{MAX_TOTAL:.0f}s")
    if total < MIN_TOTAL:
        return _fail("too_short", f"total {total}s, must be {MIN_TOTAL:.0f}-{MAX_TOTAL:.0f}s")

    first = [x for x in blocks[segs[0]["i"]:segs[0]["j"] + 1] if x["kind"] != "camera"]
    if not first or min(x["start"] for x in first) - segs[0]["start"] > HOOK_WITHIN:
        return _fail("hook_not_in_first_3s", "no dialogue/action in the first 3 seconds")
    last = [x for x in blocks[segs[-1]["i"]:segs[-1]["j"] + 1] if x["kind"] != "camera"]
    if not last or segs[-1]["end"] - max(x["end"] for x in last) > END_TOLERANCE:
        return _fail("ends_on_camera_only", "clip ends on a camera description")

    for s in segs:
        del s["i"], s["j"]
    resolved = {"episode": ep["episode"], "segments": segs, "duration": total,
                "hook": str(cand.get("hook", "")), "cliffhanger": str(cand.get("cliffhanger", "")),
                "why": str(cand.get("why", ""))}
    return True, "ok", resolved


def overlap_fraction(a, b):
    """How much two promos overlap in time, as a fraction of the shorter one."""
    shared = sum(max(0.0, min(x["end"], y["end"]) - max(x["start"], y["start"]))
                 for x in a["segments"] for y in b["segments"])
    return shared / min(a["duration"], b["duration"])


def dedupe(cands, key):
    """Keep the best-scoring promo when two overlap by more than 50% (same episode)."""
    kept = []
    for c in sorted(cands, key=key, reverse=True):
        if all(c["episode"] != k["episode"] or overlap_fraction(c, k) <= 0.5 for k in kept):
            kept.append(c)
    return kept
