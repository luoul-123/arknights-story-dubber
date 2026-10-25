import re

def compact_ocr(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    # Windows OCR inserts spaces between Chinese glyphs in some game fonts.
    text = re.sub(r"(?<=[\u3400-\u9fff]) (?=[\u3400-\u9fff])", "", text)
    text = re.sub(r"\s+([，。！？、；：])", r"\1", text)
    text = re.sub(r"([，。！？、；：])\s+", r"\1", text)
    text = re.sub(r"([（【])\s+", r"\1", text)
    text = re.sub(r"-{2,}", "——", text)
    return text


def is_interface_text(text: str) -> bool:
    """Ignore fixed story controls wherever OCR finds them on screen."""
    compact = re.sub(r"\s+", "", text)
    return bool(re.fullmatch(r"(?:明日方舟|自动(?:ON|OFF)?|跳过[▶▷卜>》，。!！]?|LOG|设置|自动(?:ON|OFF)?跳过[▶▷卜>》，。!！]?)", compact, re.I))


def join_wrapped_lines(items: list[dict], index: int, excluded: set[int] | None = None) -> str:
    """Join OCR rows belonging to one dialogue block, even across word breaks."""
    excluded = excluded or set()
    first = items[index]
    previous = first
    chosen = [first["text"]]
    used = excluded | {index}
    for _ in range(5):
        nearby = [
            (i, item) for i, item in enumerate(items)
            if i not in used
            and 0 < item["y"] - previous["y"] <= max(55, previous.get("h", 24) * 2.6)
            and abs(item["x"] - first["x"]) <= max(65, first.get("h", 24) * 3)
            and re.search(r"[\u3400-\u9fff]", item["text"])
        ]
        if not nearby:
            break
        next_index, previous = min(nearby, key=lambda pair: (pair[1]["y"], abs(pair[1]["x"] - first["x"])))
        used.add(next_index)
        chosen.append(previous["text"])
    return compact_ocr("".join(chosen))


def parse_dialogue(lines: list[dict]) -> tuple[str, str]:
    items = [
        {"text": compact_ocr(str(line.get("text", ""))), "x": float(line.get("x", 0)), "y": float(line.get("y", 0)), "h": float(line.get("height", 24))}
        for line in lines
    ]
    items = [item for item in items if item["text"] and not is_interface_text(item["text"])]
    if not items:
        return "旁白 / 未识别", ""

    # Search every part of the window for a short speaker label beside dialogue.
    candidates: list[tuple[float, int, int, str]] = []
    for i, label in enumerate(items):
        name = label["text"].strip("一—－- ")
        if not (1 < len(name) <= 10) or not re.search(r"[\u3400-\u9fff]", name) or re.search(r"[，。！？、；：,.!?]", name):
            continue
        for j, dialogue in enumerate(items):
            if i == j or dialogue["x"] < label["x"] + 55 or abs(dialogue["y"] - label["y"]) > 35:
                continue
            joined = join_wrapped_lines(items, j, {i})
            if len(joined) < 2 or (len(joined) < 4 and not re.search(r"[，。！？、；：,.!?]", joined)):
                continue
            score = len(joined) * 2 - abs(dialogue["y"] - label["y"])
            candidates.append((score, i, j, name))

    if candidates:
        _, label_index, dialogue_index, speaker = max(candidates)
        return speaker, join_wrapped_lines(items, dialogue_index, {label_index})

    # Narration may have no label; require Chinese prose to avoid reading UI or code.
    groups = [join_wrapped_lines(items, i) for i in range(len(items))]
    narration = [
        group for group in groups
        if len(re.findall(r"[\u3400-\u9fff]", group)) >= 5
        or (len(re.findall(r"[\u3400-\u9fff]", group)) >= 2 and re.search(r"[。！？!?]", group))
    ]
    if not narration:
        return "旁白 / 未识别", ""
    return "旁白 / 未识别", max(narration, key=len)
