"""Turn growing OCR text into stable, non-overlapping spoken phrases."""
import re
import time
from difflib import SequenceMatcher


def letters(text):
    return ''.join(c for c in text if c.isalnum())


class IncrementalDialogue:
    def __init__(self, tail_wait=.55):
        self.tail_wait=tail_wait
        self.reset()

    def reset(self):
        self.speaker=''; self.previous=''; self.emitted=0
        self.changed=0.0; self.blank_since=None

    def observe(self, reading, now=None):
        now=time.monotonic() if now is None else now
        text=reading.text.strip(); key=letters(text)
        if not key:
            if self.blank_since is None: self.blank_since=now
            if self.previous and now-self.blank_since>=.8:
                self.reset(); return True,[]
            return False,[]
        self.blank_since=None
        if reading.confidence<.65: return False,[]
        previous=self.previous
        same=(key.startswith(previous) or previous.startswith(key))
        # Tolerate a small OCR correction without replaying an already spoken prefix.
        correction=(len(key)>20 and len(key)==len(previous)
                    and SequenceMatcher(None,key,previous).ratio()>.96)
        if self.emitted and key[:self.emitted]==previous[:self.emitted]: same=True
        changed_scene=bool(previous and (reading.speaker!=self.speaker or not (same or correction)))
        if changed_scene:
            self.reset(); previous=''
        common=0
        for a,b in zip(key,previous):
            if a!=b: break
            common+=1
        if key!=previous: self.changed=now
        self.previous=key; self.speaker=reading.speaker
        # Positions let punctuation vary while the spoken content remains deduplicated.
        positions=[i for i,c in enumerate(text) if c.isalnum()]
        start=positions[self.emitted] if self.emitted<len(positions) else len(text)
        chunks=[]
        for mark in re.finditer(r'[。！？!?；;，,：:]',text):
            end=mark.end(); count=len(letters(text[:end]))
            if count<=self.emitted or count>common: continue
            phrase=text[start:end].strip()
            if mark.group() in '，,：:' and count-self.emitted<12: continue
            if phrase:
                chunks.append(phrase); self.emitted=count
                start=end
        # A final line without punctuation is spoken once it stops growing.
        if now-self.changed>=self.tail_wait and len(key)>self.emitted:
            tail=text[start:].strip()
            if tail: chunks.append(tail); self.emitted=len(key)
        return changed_scene,chunks
