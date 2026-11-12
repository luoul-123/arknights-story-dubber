"""Fetch one suitable Mandarin operator reference, never the whole voice pack."""
import json,re,time,uuid,subprocess,wave
from pathlib import Path
from urllib.request import Request,urlopen
DATA_ROOT="https://raw.githubusercontent.com/ArknightsAssets/ArknightsGamedata/master/cn/gamedata/excel/"
VOICE_ROOT="https://raw.githubusercontent.com/ArknightsAssets/ArknightsAssets2/voice/assets/dyn/audio/sound_beta_2/voice_cn/"
def source_json(data_dir,name,timeout=40):
    if name not in ("character_table","charword_table","handbook_info_table","zone_table"):raise ValueError("Unknown data source")
    cache=data_dir/"sources";cache.mkdir(exist_ok=True);target=cache/(name+".json")
    if target.exists() and time.time()-target.stat().st_mtime<86400:return json.loads(target.read_text("utf-8"))
    req=Request(DATA_ROOT+name+".json",headers={"User-Agent":"ZhouSheng-Local-Reference/1"})
    try:
        with urlopen(req,timeout=timeout) as response:raw=response.read(40*1024*1024+1)
        if len(raw)>40*1024*1024:raise ValueError("资源索引过大")
        result=json.loads(raw)
        target.write_text(json.dumps(result,ensure_ascii=False),encoding="utf-8")
        return result
    except Exception:
        if target.exists():return json.loads(target.read_text("utf-8"))
        raise RuntimeError("干员语音索引暂时无法访问，请稍后重试，或直接上传参考语音")

def fetch_reference(data_dir,name):
    import imageio_ffmpeg
    characters=source_json(data_dir,"character_table")
    match=next(((ident,c) for ident,c in characters.items() if c.get("name")==name),None)
    if not match:raise ValueError("未找到这个干员，请输入完整游戏名称。NPC 通常没有独立干员语音。")
    ident,_=match;table=source_json(data_dir,"charword_table")
    if "CN_MANDARIN" not in table.get("voiceLangDict",{}).get(ident,{}).get("dict",{}):raise ValueError("该干员暂未提供普通话语音，请上传可用的参考录音")
    words=table["charWords"]
    candidates=[w for w in words.values() if w.get("charId")==ident and w.get("voiceAsset") and w.get("voiceText") and 12<=len(w["voiceText"])<=80 and not re.search(r"[<>]",w["voiceText"])]
    order={"交谈2":0,"任命助理":1,"交谈1":2,"交谈3":3}
    candidates.sort(key=lambda w:(len(w["voiceText"])>40,order.get(w.get("voiceTitle"),9),abs(len(w["voiceText"])-25)))
    folder=data_dir/"reference-imports";folder.mkdir(exist_ok=True)
    for word in candidates[:12]:
        asset=word["voiceAsset"].lower()
        if not re.fullmatch(r"char_[a-z0-9_]+/cn_[0-9]+",asset):continue
        url=VOICE_ROOT+asset+".mp3"
        source=folder/(uuid.uuid4().hex+".mp3");normalized=source.with_suffix(".wav")
        try:
            with urlopen(Request(url,headers={"User-Agent":"ZhouSheng-Local-Reference/1"}),timeout=20) as response:raw=response.read(2*1024*1024+1)
            if len(raw)>2*1024*1024:continue
            source.write_bytes(raw)
            result=subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(),"-nostdin","-v","error","-y","-i",str(source),"-vn","-ac","1","-ar","32000","-c:a","pcm_s16le",str(normalized)],capture_output=True,timeout=30,creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
            if result.returncode:continue
            with wave.open(str(normalized),"rb") as w:duration=w.getnframes()/w.getframerate()
            if not 3<=duration<=10:continue
            return {"id":uuid.uuid4().hex,"path":str(normalized),"duration":duration,"text":word["voiceText"],"clipped":False,"source":url,"sourceVoiceId":word["charWordId"],"title":word.get("voiceTitle","参考语音"),"characterId":ident}
        except Exception:continue
    raise ValueError("没有找到可用的 3–10 秒普通话参考语音。可直接上传该角色的清晰录音。")
