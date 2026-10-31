"""Prose checks for real-model replies (used by the paid tests; unit-tested offline).

They check the answer format from the system prompt, not the content: numbers come from the evidence.
"""

import re

ORDINARY_WORDS = 100  # the prompt's limit for ordinary answers (target 60-100)
MAX_WORDS = 130  # rankings and comparisons
HEADING = re.compile(r"^\s*(#{1,6}\s|\*\*[^*\n]{1,40}:?\*\*:?\s*$|[-*]?\s*\*\*[^*\n]{1,30}:\*\*)", re.M)
BULLET = re.compile(r"^\s*([-*•]|\d+\.)\s+", re.M)
RAW_FRACTION = re.compile(r"(?<![\w.])0\.\d{3,}(?![\d%])")  # 0.8418, but not 0.6% or 0.25 (a weight)
CLOSING_OFFER = re.compile(r"\b(I can|I could|Would you like|Let me know|If you'd like)\b", re.I)
REPLY_NUMBER = re.compile(r"(?<![\w.-])-?\d[\d,]*(?:\.\d+)?")
EVIDENCE_NUMBER = re.compile(r"-?\d+(?:\.\d+)?")
HEBREW_LETTER = re.compile(r"[א-ת]")
LATIN_LETTER = re.compile(r"[A-Za-z]")


def has_table(text: str) -> bool:
    return any(line.lstrip().startswith("|") for line in text.splitlines())


def format_problems(text: str, max_words: int = MAX_WORDS) -> list[str]:
    """Answer-format policy from the system prompt. Empty list = compliant. No sentence counting."""
    words = len(text.split())
    paragraphs = [p for p in text.strip().split("\n\n") if p.strip()]
    checks = [
        (words == 0, "empty"),
        (words > max_words, f"{words} words > {max_words}"),
        (has_table(text), "table"),
        (bool(HEADING.search(text)), "heading or bold section label"),
        (len(BULLET.findall(text)) >= 2, "bullet list"),
        (bool(RAW_FRACTION.search(text)), f"raw fraction {RAW_FRACTION.findall(text)}"),
        (bool(paragraphs and CLOSING_OFFER.search(paragraphs[-1])), "closing offer of further analysis"),
    ]
    return [msg for failed, msg in checks if failed]


def is_concise(text: str, max_words: int = MAX_WORDS) -> bool:
    return not format_problems(text, max_words)


def hebrew_share(text: str) -> float:
    """Share of Hebrew letters among Hebrew and Latin letters (airport codes stay Latin)."""
    he = len(HEBREW_LETTER.findall(text))
    total = he + len(LATIN_LETTER.findall(text))
    return he / total if total else 0.0


def is_mainly_hebrew(text: str, min_share: float = 0.6) -> bool:
    return hebrew_share(text) >= min_share


def evidence_numbers(obj, out=None) -> list[float]:
    """Every number in tool artifacts, including those inside strings (windows, thresholds, flags)."""
    out = [] if out is None else out
    if isinstance(obj, bool) or obj is None:
        pass
    elif isinstance(obj, (int, float)):
        out.append(float(obj))
    elif isinstance(obj, dict):
        for v in obj.values():
            evidence_numbers(v, out)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            evidence_numbers(v, out)
    elif isinstance(obj, str):
        out.extend(float(x) for x in EVIDENCE_NUMBER.findall(obj.replace(",", "")))
    return out


def _grounded(shown: str, values: list[float]) -> bool:
    x = abs(float(shown.replace(",", "")))  # sign is often worded ("4.98% below 2019")
    decimals = len(shown.split(".")[1]) if "." in shown else 0
    tol = 0.5 * 10**-decimals + 1e-9
    if decimals == 0 and x >= 1000:  # "about 267,000": rounded to its trailing zeros
        zeros = len(shown.replace(",", "")) - len(shown.replace(",", "").rstrip("0"))
        tol = max(tol, 0.5 * 10**zeros)
    # as returned, as a percentage of a share, or in millions ("36.0M")
    return any(abs(abs(c) - x) <= tol for v in values for c in (v, v * 100, v / 1e6))


def ungrounded_numbers(reply: str, artifacts: list) -> list[str]:
    """Numbers in the reply that no artifact supports at the shown precision (e.g. 26.1% for 0.26045)."""
    values = evidence_numbers(artifacts)
    return [s for s in REPLY_NUMBER.findall(reply) if not _grounded(s, values)]
