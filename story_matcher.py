"""Prototype for resolving temporary story speaker labels from a script timeline.

The caller supplies a script it is permitted to use. This module never reads game
files or downloads story text. It can later back a chapter-sized public index.
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from difflib import SequenceMatcher


SLOT = re.compile(r"\[charslot(?:\((.*?)\))?\]", re.IGNORECASE)
NAME = re.compile(r"\[name\s*=\s*['\"]([^'\"]+)['\"]\](.*)", re.IGNORECASE)
ATTR = re.compile(r"(\w+)\s*=\s*['\"]([^'\"]*)['\"]")


@dataclass(frozen=True)
class StoryLine:
    shown_speaker: str
    text: str
    sprite: str | None


def sprite_key(value: str) -> str:
    base = value.split("#", 1)[0].lower()
    return re.sub(r"_\d+$", "", base)


def normalize_text(value: str) -> str:
    return re.sub(r"[^\w\u3400-\u9fff]", "", value).lower()


def parse_script(source: str) -> list[StoryLine]:
    slots: dict[str, str] = {}
    focused: str | None = None
    lines: list[StoryLine] = []
    for raw in source.splitlines():
        slot_match = SLOT.search(raw)
        if slot_match:
            args = slot_match.group(1)
            if args is None:
                slots.clear()
                focused = None
            else:
                attributes = dict(ATTR.findall(args))
                slot = attributes.get("slot", "m")
                if attributes.get("name"):
                    slots[slot] = attributes["name"]
                if attributes.get("focus") in slots:
                    focused = attributes["focus"]
                elif attributes.get("name"):
                    focused = slot
        name_match = NAME.search(raw)
        if name_match:
            shown_name = name_match.group(1).strip()
            text = name_match.group(2).strip()
            if text:
                sprite = slots.get(focused) if focused else None
                lines.append(StoryLine(shown_name, text, sprite))
    return lines


class StoryMatcher:
    def __init__(self, lines: list[StoryLine], available_voices: set[str]) -> None:
        self.lines = lines
        self.available_voices = available_voices
        self.position = 0
        votes: dict[str, Counter[str]] = defaultdict(Counter)
        for line in lines:
            if line.sprite and line.shown_speaker in available_voices:
                votes[sprite_key(line.sprite)][line.shown_speaker] += 1
        self.sprite_to_voice: dict[str, str] = {}
        for sprite, names in votes.items():
            name, count = names.most_common(1)[0]
            if count / sum(names.values()) >= 0.85:
                self.sprite_to_voice[sprite] = name

    def locate(self, visible_text: str) -> tuple[StoryLine, str | None, float] | None:
        query = normalize_text(visible_text)
        if len(query) < 4 or not self.lines:
            return None
        nearby = range(max(0, self.position - 5), min(len(self.lines), self.position + 60))
        best = self._best(query, nearby)
        if best is None or best[0] < 0.72:
            best = self._best(query, range(len(self.lines)))
        if best is None or best[0] < 0.72:
            return None
        score, index = best
        self.position = index
        line = self.lines[index]
        if line.shown_speaker in self.available_voices:
            voice = line.shown_speaker
        elif line.sprite:
            voice = self.sprite_to_voice.get(sprite_key(line.sprite))
        else:
            voice = None
        return line, voice, score

    def _best(self, query: str, indexes: range) -> tuple[float, int] | None:
        best: tuple[float, int] | None = None
        for index in indexes:
            candidate = normalize_text(self.lines[index].text)
            if not candidate:
                continue
            score = SequenceMatcher(None, query, candidate).ratio()
            if best is None or score > best[0]:
                best = (score, index)
        return best
