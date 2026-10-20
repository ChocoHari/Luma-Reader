"""Conservative two-column prose order shared by extraction and word alignment."""
import re


def ordered_ocr_regions(text, regions, width):
    """Reorder confident prose columns while retaining every recognised character."""
    if not regions:
        return text, regions, False
    by_source = sorted(regions, key=lambda r: r['start'])
    position = 0
    lines = []
    for region in by_source:
        start, end = region['start'], region['end']
        if start < position or end <= start or end > len(text) or text[position:start].strip():
            return text, regions, False
        lines.append((region, text[start:end]))
        position = end
    if text[position:].strip():
        return text, regions, False
    middle = width / 2
    left = [v for v in lines if v[0]['rect'][2] < middle - width * .015]
    right = [v for v in lines if v[0]['rect'][0] > middle + width * .015]
    def prose(items):
        return [v for v in items if len(re.findall(r'\w+', v[1])) >= 5]
    lp, rp = prose(left), prose(right)
    if len(lp) < 4 or len(rp) < 4:
        return text, regions, False
    if min(max(v[0]['rect'][3] for v in lp), max(v[0]['rect'][3] for v in rp)) <= max(min(v[0]['rect'][1] for v in lp), min(v[0]['rect'][1] for v in rp)):
        return text, regions, False
    left_ids, right_ids = {id(v[0]) for v in left}, {id(v[0]) for v in right}
    spans = sorted((v for v in lines if id(v[0]) not in left_ids | right_ids), key=lambda v: v[0]['rect'][1])
    ordered, remaining = [], left + right
    def emit(items):
        for ids in (left_ids, right_ids):
            ordered.extend(sorted((v for v in items if id(v[0]) in ids), key=lambda v: v[0]['rect'][1]))
    for span in spans:
        before = [v for v in remaining if v[0]['rect'][1] < span[0]['rect'][1]]
        emit(before)
        used = {id(v[0]) for v in before}
        remaining = [v for v in remaining if id(v[0]) not in used]
        ordered.append(span)
    emit(remaining)
    parts, result, offset = [], [], 0
    for region, label in ordered:
        parts.append(label)
        result.append({**region, 'start': offset, 'end': offset + len(label)})
        offset += len(label) + 1
    return '\n'.join(parts), result, True


def native_page_content(page, include_words=True):
    blocks = [b for b in page.get_text('blocks') if b[6] == 0 and b[4].strip()]
    width = page.mediabox.width
    middle = width / 2
    left = [b for b in blocks if b[2] < middle - width * .015]
    right = [b for b in blocks if b[0] > middle + width * .015]
    # Require substantial multiline prose on both sides. Short table cells,
    # isolated marginal labels and ordinary indented paragraphs are insufficient.
    def prose(items):
        return [b for b in items if len(re.findall(r'\w+', b[4])) >= 20
                and len(b[4].strip().splitlines()) >= 3]
    lp, rp = prose(left), prose(right)
    overlap = any(min(a[3], b[3]) - max(a[1], b[1]) > 20 for a in lp for b in rp)
    if not lp or not rp or not overlap:
        return page.get_text(sort=True), page.get_text('words', sort=True) if include_words else [], 'Page order'
    left_ids = {b[5] for b in left}
    right_ids = {b[5] for b in right}
    side_ids = left_ids | right_ids
    spanning = sorted((b for b in blocks if b[5] not in side_ids), key=lambda b: (b[1], b[0]))
    ordered, remaining = [], list(left + right)
    def emit(items):
        ordered.extend(sorted((b for b in items if b[5] in left_ids), key=lambda b: (b[1], b[0])))
        ordered.extend(sorted((b for b in items if b[5] in right_ids), key=lambda b: (b[1], b[0])))
    for span in spanning:
        before = [b for b in remaining if (b[1] + b[3]) / 2 < (span[1] + span[3]) / 2]
        emit(before)
        before_ids = {b[5] for b in before}
        remaining = [b for b in remaining if b[5] not in before_ids]
        ordered.append(span)
    emit(remaining)
    ranks = {b[5]: i for i, b in enumerate(ordered)}
    words = sorted(page.get_text('words'), key=lambda w: (ranks.get(w[5], len(ranks)), w[6], w[7])) if include_words else []
    return '\n\n'.join(b[4].strip() for b in ordered), words, 'Two-column prose'
