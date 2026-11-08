"""Helpers that turn a parsed episode into text the AI can read, using block IDs."""

MAX_TEXT = 240  # long camera/action text is shortened to save tokens


def prepare(ep):
    """Give every block an ID (B001, B002 ...) and build an id -> position lookup."""
    for i, b in enumerate(ep["blocks"], start=1):
        b["id"] = f"B{i:03d}"
    ep["index"] = {b["id"]: pos for pos, b in enumerate(ep["blocks"])}
    return ep


def label_of(b):
    """Speaker name for dialogue, CAMERA or ACTION for the rest."""
    return b["who"] if b["kind"] == "dialogue" else b["kind"].upper()


def short(text):
    """Shorten very long text with '...'."""
    return text if len(text) <= MAX_TEXT else text[:MAX_TEXT].rstrip() + "..."


def to_prompt_text(ep):
    """One line per block: [B011] 11.2-12.6 | SPEAKER: text"""
    if "index" not in ep:
        prepare(ep)
    return "\n".join(
        f'[{b["id"]}] {b["start"]:.1f}-{b["end"]:.1f} | {label_of(b)}: {short(b["text"])}'
        for b in ep["blocks"])


def mmss(t):
    """Seconds -> mm:ss.s for display."""
    return f"{int(t // 60):02d}:{t % 60:04.1f}"
