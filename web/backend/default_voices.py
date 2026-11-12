"""Site-wide default voices; readers never configure NPC voices."""
import hashlib,json,re
from pathlib import Path


def gender_for(speaker, known=None):
    name=str(speaker or "").strip()
    if name in (known or {}):return known[name]
    if re.search(r"女性|女人|女孩|少女|女士|女声|妇人|老太太|老婆婆|姐姐|妹妹|母亲|妈妈",name):return "female"
    if re.search(r"男性|男人|男孩|少年|男士|男声|老爷爷|老先生|哥哥|弟弟|父亲|爸爸",name):return "male"
    return "female"


def read_defaults(data_dir):
    path=Path(data_dir)/"default-voices.json"
    try:return json.loads(path.read_text("utf-8"))
    except FileNotFoundError:return {"female":None,"male":None,"narrator":None}


def save_defaults(data_dir, store, requested):
    config=read_defaults(data_dir)
    for role in ("female","male","narrator"):
        if role not in requested:continue
        ident=requested[role] or None
        if ident and (ident not in store or not store[ident].get("published")):
            raise ValueError("请先发布音色，再设置为站点默认声音")
        config[role]=ident
    path=Path(data_dir)/"default-voices.json";temporary=path.with_suffix(".tmp")
    temporary.write_text(json.dumps(config,ensure_ascii=False),encoding="utf-8");temporary.replace(path)
    return config


def defaults_version(config, store):
    identities={role:[ident,store.get(ident,{}).get("published",{}).get("version")] for role,ident in config.items()}
    return "defaults-"+hashlib.sha256(json.dumps(identities,sort_keys=True).encode()).hexdigest()[:16]


def selected_default(config, speaker, narrator=False, known=None):
    if narrator:return config.get("narrator") or config.get("female")
    return config.get(gender_for(speaker,known))
