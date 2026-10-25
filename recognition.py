"""Screen capture and hybrid OCR, with a bounded text-stability gate."""
from __future__ import annotations
import hashlib
import re
import time
from dataclasses import dataclass
from difflib import SequenceMatcher

import numpy as np
import win32gui
from PIL import Image, ImageGrab
from capture_window import print_window
from dialogue import compact_ocr, is_interface_text, parse_dialogue
from windows_services import WindowsWorker


class CapturePaused(RuntimeError):
    pass


def is_foreground(hwnd):
    foreground = win32gui.GetForegroundWindow()
    return bool(foreground and win32gui.GetAncestor(foreground, 2) == hwnd)


def visible_windows():
    result = []
    def visit(hwnd, _):
        if win32gui.IsWindowVisible(hwnd) and not win32gui.IsIconic(hwnd):
            title = win32gui.GetWindowText(hwnd).strip()
            a, b, c, d = win32gui.GetWindowRect(hwnd)
            if title and c-a >= 400 and d-b >= 250:
                result.append((hwnd, title))
    win32gui.EnumWindows(visit, None)
    return result


@dataclass
class Reading:
    speaker: str
    text: str
    image: Image.Image
    elapsed_ms: int
    confidence: float
    lines: list
    cached: bool = False
    engine: str = 'Windows OCR'


class Recognizer:
    def __init__(self):
        self.native = WindowsWorker()
        self.refiner = None
        self.engine = 'Windows OCR'
        self.warning = ''
        self.cache_key = None
        self.cache_value = None
        self.last_fallback = 0.0

    def warmup(self):
        self.native.ocr(Image.new('RGB', (100, 80), 'black'))
        try:
            from rapidocr import RapidOCR
            self.refiner = RapidOCR(params={
                'Global.log_level': 'error', 'Global.use_cls': False,
                'EngineConfig.onnxruntime.intra_op_num_threads': 4,
            })
            self.refiner(Image.new('RGB', (180, 48), 'white'), use_det=False, use_cls=False)
            self.engine = '双引擎中文识别'
        except Exception as exc:
            self.warning = f'中文复核模型不可用，使用 Windows OCR：{exc}'
        return self.engine

    def capture(self, hwnd):
        if not win32gui.IsWindow(hwnd) or win32gui.IsIconic(hwnd):
            raise CapturePaused('游戏窗口已关闭或最小化')
        if not is_foreground(hwnd):
            raise CapturePaused('等待游戏回到前台，返回后自动继续')
        # Screen capture is both faster and reliable for this game's GPU renderer.
        bounds = win32gui.GetWindowRect(hwnd)
        image = ImageGrab.grab(bbox=bounds, all_screens=True)
        if not is_foreground(hwnd) or bounds != win32gui.GetWindowRect(hwnd):
            raise CapturePaused('窗口正在切换，等待画面稳定')
        return image

    def scan_window(self, hwnd):
        return self.scan(self.capture(hwnd), source=hwnd)

    def scan(self, image, source='image'):
        started = time.perf_counter()
        image = image.convert('RGB')
        # Fingerprint the actual frame: a stationary frame does not need new OCR.
        signature = hashlib.blake2b(image.tobytes(), digest_size=12).digest()
        key = (source, image.size, signature)
        if key == self.cache_key and self.cache_value:
            old = self.cache_value
            return Reading(old.speaker, old.text, image, 0, old.confidence, old.lines, True, old.engine)
        max_side = max(image.size)
        work = image
        if max_side > 2200:
            work = image.resize((round(image.width*2200/max_side), round(image.height*2200/max_side)))
        lines = self.native.ocr(work)
        refined = []
        scores = []
        for row in lines:
            row = dict(row)
            original = compact_ocr(row['text'])
            if is_interface_text(original):
                continue
            if self.refiner and len(re.findall(r'[\u3400-\u9fff]', original)) >= 2:
                x, y, w, h = (row[k] for k in ('x', 'y', 'width', 'height'))
                crop = work.crop((max(0, x-5), max(0, y-5), min(work.width, x+w+5), min(work.height, y+h+5)))
                try:
                    result = self.refiner(crop, use_det=False, use_cls=False)
                    if result.txts:
                        candidate = compact_ocr(result.txts[0])
                        confidence = float(result.scores[0])
                        if original and original[-1] in '。！？!?' and candidate and candidate[-1] not in '。！？!?':
                            candidate += original[-1]
                        # High-confidence visual recognition may correct glyphs, never invent prose.
                        if confidence >= .85 and len(candidate) >= max(1, len(original)*.6):
                            row['text'] = candidate
                            row['confidence'] = confidence
                        scores.append(confidence)
                except Exception:
                    pass
            refined.append(row)
        speaker, text = parse_dialogue(refined)
        # Recover text that Windows detection missed, at most once per second.
        if not text and self.refiner and time.monotonic()-self.last_fallback > 1:
            self.last_fallback = time.monotonic()
            result = self.refiner(work, use_det=True, use_cls=False)
            fallback = []
            if result.txts:
                for box, value, score in zip(result.boxes, result.txts, result.scores):
                    lo, hi = np.min(box, axis=0), np.max(box, axis=0)
                    fallback.append(dict(text=value, x=float(lo[0]), y=float(lo[1]), width=float(hi[0]-lo[0]), height=float(hi[1]-lo[1]), confidence=float(score)))
                speaker, text = parse_dialogue(fallback)
                if text:
                    refined = fallback
                    scores = [r['confidence'] for r in fallback if not is_interface_text(r['text'])]
        confidence = min(scores) if scores else .8
        reading = Reading(speaker, text, image, round((time.perf_counter()-started)*1000), confidence, refined, False, self.engine)
        self.cache_key, self.cache_value = key, reading
        return reading

    def close(self):
        self.native.close()


def text_key(speaker, text):
    return speaker + '|' + re.sub(r'[\W_]+', '', text)


class StableDialogue:
    """Require a repeated completed observation, and suppress punctuation flicker."""
    def __init__(self, settle_seconds=.22):
        self.settle = settle_seconds
        self.reset()

    def reset(self):
        self.pending = ''
        self.since = 0.0
        self.spoken = ''

    def observe(self, reading, now=None):
        now = time.monotonic() if now is None else now
        if not reading.text:
            self.pending = ''
            return False
        key = text_key(reading.speaker, reading.text)
        if key != self.pending:
            self.pending, self.since = key, now
            return False
        if now-self.since < self.settle or key == self.spoken or reading.confidence < .65:
            return False
        # One-glyph OCR oscillations should not replay a long spoken sentence.
        if self.spoken and len(key) > 22 and SequenceMatcher(None, key, self.spoken).ratio() > .97:
            return False
        self.spoken = key
        return True
