"""Compact catalog metadata and official operator gender, cached on the host."""
import json,re,threading,time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from operator_reference import source_json


def build_metadata(handbook, characters, zones):
    personal, genders, mainline = {}, {}, {}
    for ident, book in handbook.get("handbookDict", {}).items():
        name = characters.get(ident, {}).get("name", "")
        for block in book.get("storyTextAudio", []):
            for story in block.get("stories", []):
                match = re.search(r"【性别】\s*([男女])", story.get("storyText", ""))
                if match and name:
                    genders[name] = "female" if match[1] == "女" else "male"
        for item in book.get("handbookAvgList", []):
            personal[item["storySetId"]] = {"operator": name, "releasedAt": item.get("storyGetTime", 0), "operatorId": ident}
    for ident, item in zones.get("mainlineAdditionInfo", {}).items():
        if item.get("zoneOpenTime", 0) > 0:
            mainline[ident] = item["zoneOpenTime"]
    return {"personal": personal, "genders": genders, "mainline": mainline}


class CatalogMetadata:
    def __init__(self, data_dir):
        self.root=Path(data_dir);self.path=self.root/"sources"/"catalog-metadata-v1.json"
        self.lock=threading.Lock();self.value=None;self.refreshed=0;self.refreshing=False
    def _build(self):
        names=("handbook_info_table","character_table","zone_table")
        with ThreadPoolExecutor(max_workers=3) as pool:
            values=list(pool.map(lambda name:source_json(self.root,name,timeout=6),names))
        data=build_metadata(*values)
        self.path.parent.mkdir(exist_ok=True)
        temporary=self.path.with_suffix(".tmp");temporary.write_text(json.dumps(data,ensure_ascii=False),encoding="utf-8");temporary.replace(self.path)
        self.value=data;self.refreshed=time.time()
        return data
    def get(self):
        with self.lock:
            if self.value is None and self.path.exists():
                try:self.value=json.loads(self.path.read_text("utf-8"));self.refreshed=self.path.stat().st_mtime
                except (OSError,ValueError):pass
            if self.value is None:
                try:return self._build()
                except Exception:return {"personal":{},"genders":{},"mainline":{},"incomplete":True}
            if time.time()-self.refreshed>86400 and not self.refreshing:
                self.refreshing=True
                def update():
                    try:self._build()
                    except Exception:self.refreshed=time.time()-85800
                    finally:self.refreshing=False
                threading.Thread(target=update,daemon=True).start()
            return self.value
