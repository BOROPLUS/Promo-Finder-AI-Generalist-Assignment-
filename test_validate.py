"""Checks the validation rules with made-up episodes. No AI and no episode files needed.
Run: python test_validate.py"""
from prompt_utils import prepare
from validate import validate_candidate


def blk(kind, start, end, who=None):
    return {"kind": kind, "who": who or kind.upper(), "start": start, "end": end, "text": "x"}


# 12 blocks: a line every 5 seconds from 0 to 60, plus a camera-only block at the end
ep = prepare({"episode": 1, "blocks": [blk("dialogue", i * 5, i * 5 + 4, "A") for i in range(12)]
              + [blk("camera", 60, 70)]})
cases = [
    ("good promo passes", {"segments": [{"start_block": "B001", "end_block": "B008"}]}, True),
    ("unknown block id is rejected", {"segments": [{"start_block": "B001", "end_block": "B999"}]}, False),
    ("too long (over 60s) is rejected", {"segments": [{"start_block": "B001", "end_block": "B013"}]}, False),
    ("too short (under 20s) is rejected", {"segments": [{"start_block": "B001", "end_block": "B002"}]}, False),
    ("segments out of order are rejected", {"segments": [{"start_block": "B006", "end_block": "B008"},
                                                         {"start_block": "B001", "end_block": "B003"}]}, False),
    ("reversed segment is rejected", {"segments": [{"start_block": "B008", "end_block": "B001"}]}, False),
    ("4 segments is rejected", {"segments": [{"start_block": "B001", "end_block": "B001"}] * 4}, False),
]
# episode with a long camera-only tail, and one that opens on camera only
ep2 = prepare({"episode": 2, "blocks": [blk("dialogue", i * 5, i * 5 + 4, "A") for i in range(5)] + [blk("camera", 25, 45)]})
ep3 = prepare({"episode": 3, "blocks": [blk("camera", 0, 10)] + [blk("dialogue", 10 + i * 5, 14 + i * 5, "A") for i in range(6)]})
cases += [
    ("ends on camera-only is rejected", {"segments": [{"start_block": "B001", "end_block": "B006"}], "_ep": ep2}, False),
    ("no hook in first 3 seconds is rejected", {"segments": [{"start_block": "B001", "end_block": "B007"}], "_ep": ep3}, False),
]
failed = 0
for name, cand, want in cases:
    ok, reason, _ = validate_candidate(cand.pop("_ep", ep), cand)
    status = "PASS" if ok == want else "FAIL"
    failed += status == "FAIL"
    print(f"{status}  {name}  ->  {reason}")
print("\nAll tests passed." if not failed else f"\n{failed} test(s) FAILED.")
