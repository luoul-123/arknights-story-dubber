"""Fetch small story files through the host network and keep a durable local cache."""
from __future__ import annotations
import hashlib, json, re, threading, time, uuid
from pathlib import Path
from urllib.request import Request, urlopen

SOURCES = (
    "https://raw.githubusercontent.com/ArknightsAssets/ArknightsGamedata/master/cn/gamedata/",
    "https://cdn.jsdelivr.net/gh/ArknightsAssets/ArknightsGamedata@master/cn/gamedata/",
)


def valid_story_id(value):
    return isinstance(value, str) and 0 < len(value) <= 180 and re.fullmatch(r"[a-zA-Z0-9_/-]+", value) is not None and ".." not in value and not value.startswith("/")


def download(url, limit):
    request = Request(url, headers={"User-Agent": "ZhouSheng-Story/1", "Accept": "application/json,text/plain"})
    # urllib uses the host's configured proxy, including Windows Internet Settings.
    with urlopen(request, timeout=6) as response:
        body = response.read(limit + 1)
    if len(body) > limit:
        raise ValueError("剧情文件超过大小限制")
    return body


class StorySource:
    def __init__(self, folder, fetcher=download, now=time.time, ttl=86400):
        self.folder = Path(folder)
        self.folder.mkdir(parents=True, exist_ok=True)
        self.fetcher, self.now, self.ttl = fetcher, now, ttl
        self.guard = threading.Lock()
        self.locks, self.refreshing, self.last_attempt = {}, set(), {}

    def _key(self, ident):
        if ident is not None and not valid_story_id(ident):
            raise ValueError("无效章节")
        return hashlib.sha256(ident.encode()).hexdigest() + ".txt" if ident else "catalog.json"

    def _decode(self, ident, body):
        text = body.decode("utf-8-sig")
        if not text.strip() or text.lstrip().lower().startswith(("<!doctype html", "<html")):
            raise ValueError("资源返回的内容不是剧情")
        if ident:
            return text
        data = json.loads(text)
        if not isinstance(data, dict) or not any(isinstance(item, dict) and isinstance(item.get("infoUnlockDatas"), list) for item in data.values()):
            raise ValueError("剧情目录格式无效")
        return data

    def _cached(self, ident, target):
        try:
            return self._decode(ident, target.read_bytes())
        except (OSError, ValueError, UnicodeError):
            return None

    def _fetch(self, ident, target):
        relative = "story/" + ident + ".txt" if ident else "excel/story_review_table.json"
        limit = 4 * 1024 * 1024 if ident else 8 * 1024 * 1024
        for base in SOURCES:
            try:
                body = self.fetcher(base + relative, limit)
                data = self._decode(ident, body)
                temporary = target.with_name(target.name + "." + uuid.uuid4().hex + ".tmp")
                temporary.write_bytes(body)
                temporary.replace(target)
                return data
            except (OSError, ValueError, TimeoutError):
                continue
        raise RuntimeError("剧情源暂时无法连接，本章还没有本地缓存。请稍后重试；已缓存章节仍可阅读。")

    def get(self, ident=None):
        key = self._key(ident)
        target = self.folder / key
        with self.guard:
            lock = self.locks.setdefault(key, threading.Lock())
        with lock:
            data = self._cached(ident, target)
            if data is not None:
                stale = self.now() - target.stat().st_mtime > self.ttl
                if stale:
                    self._refresh_later(ident, key, target)
                return {"data": data, "cached": True, "stale": stale}
            data = self._fetch(ident, target)
            return {"data": data, "cached": False, "stale": False}

    def _refresh_later(self, ident, key, target):
        with self.guard:
            if key in self.refreshing or self.now() - self.last_attempt.get(key, 0) < 300:
                return
            self.refreshing.add(key)
            self.last_attempt[key] = self.now()
        def work():
            try:
                self._fetch(ident, target)
            except Exception:
                pass  # Existing valid cache remains usable during upstream failure.
            finally:
                with self.guard:
                    self.refreshing.discard(key)
        threading.Thread(target=work, daemon=True).start()
