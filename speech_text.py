"""Deterministic, offline speech preparation; source offsets never change."""
from __future__ import annotations
import re
from collections import Counter

TITLES = {"Mr.": "Mister", "Mrs.": "Missus", "Ms.": "Ms", "Dr.": "Doctor", "Prof.": "Professor",
          "Sr.": "Senior", "Jr.": "Junior", "Fig.": "Figure", "Figs.": "Figures", "No.": "Number"}
SYMBOLS = {"→": "leads to", "←": "comes from", "↔": "is related to", "⇒": "implies", "⇐": "is implied by",
           "↑": "increases", "↓": "decreases", "−": "minus", "±": "plus or minus", "×": "times",
           "÷": "divided by", "=": "equals", "≤": "less than or equal to", "≥": "greater than or equal to",
           "≠": "not equal to", "∑": "sum", "√": "square root", "%": "percent"}


def spoken_text(text, profile="Natural", replacements=None, markdown=False):
    if profile != "Literal":
        text = re.sub(r"(?m)^\s*[-_=─━—–*•·.]{3,}\s*$", " ", text)
        if markdown:
            text = re.sub(r"(?m)^\s{0,3}#{1,6}\s+", "", text)
            text = re.sub(r"!\[([^]]*)\]\([^)]*\)", r"\1", text)
            text = re.sub(r"\[([^]]+)\]\([^)]*\)", r"\1", text)
            text = re.sub(r"(?m)^\s*(?:[-*+]\s+|\d+[.)]\s+)", "", text)
            text = re.sub(r"[*_`~]{1,3}", "", text)
        for abbreviation, expansion in TITLES.items():
            text = re.sub(r"\b" + re.escape(abbreviation) + r"(?=\s|$)", expansion, text, flags=re.I)
        text = re.sub(r"\be\.g\.", "for example", text, flags=re.I)
        text = re.sub(r"\bi\.e\.", "that is", text, flags=re.I)
        text = re.sub(r"\betc\.", "etcetera", text, flags=re.I)
        # Initialisms remain one speech unit, with spaces to avoid a fabricated word.
        text = re.sub(r"\b(?:[A-Z]\.){2,}", lambda m: " ".join(m.group().replace(".", "")), text)
    for symbol, wording in SYMBOLS.items():
        if symbol in "→←↔⇒⇐↑↓" and profile == "Natural":
            text = text.replace(symbol, ", ")
        else:
            text = text.replace(symbol, f" {wording} ")
    if profile == "Literal":
        for symbol, wording in {"_": "underscore", "#": "hash", "|": "vertical bar", "*": "asterisk"}.items():
            text = text.replace(symbol, f" {wording} ")
    if replacements:
        for source, replacement in sorted(replacements.items(), key=lambda item: -len(item[0])):
            if source:
                text = re.sub(r"(?<!\w)" + re.escape(source) + r"(?!\w)", lambda _: replacement, text, flags=re.I)
    return re.sub(r"\s+", " ", text).strip(" ,")


def margin_ranges(document):
    """Conservative repeated first/last lines, only for PDF source pages."""
    if not document.path or document.path.suffix.lower() != ".pdf":
        return []
    candidates, counts = [], Counter()
    offset = 0
    for page in document.pages:
        lines = list(re.finditer(r"[^\n]+", page.text))
        seen = set()
        for line in lines[:1] + lines[-1:]:
            label = line.group().strip()
            if len(label) > 80 or not label or (len(lines)<3 and not label.isdigit()):
                continue
            if not label.isdigit() and re.search(r"[.!?]$",label):
                continue
            key = re.sub(r"\d+", "#", label.casefold())
            candidates.append((offset + line.start(), offset + line.end(), key, label.isdigit()))
            seen.add(key)
        counts.update(seen)
        offset += len(page.text) + 2
    minimum = max(3, int(len(document.pages) * 0.02))
    return [(a, b) for a, b, key, number in candidates if number or counts[key] >= minimum]


def prepare_parts(text, raw_parts, profile="Natural", replacements=None, markdown=False, omitted=()):
    from reader_core import Sentence
    prepared = []
    for part in raw_parts:
        source = part.text
        # Replace omitted source ranges by spaces without altering source coordinates.
        for a, b in omitted:
            left, right = max(a, part.start), min(b, part.end)
            if left < right:
                source = source[:left-part.start] + " " * (right-left) + source[right-part.start:]
        spoken = spoken_text(source, profile, replacements, markdown)
        if spoken and re.search(r"\w", spoken):
            pause = .55 if profile=="Study" and re.match(r"\s*#{1,6}\s",part.text) else .2 if profile=="Study" else 0
            prepared.append(Sentence(part.start, part.end, part.text, spoken, pause))
    return prepared
