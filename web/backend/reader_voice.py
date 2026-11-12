"""One private reading voice per authenticated reader, using shared base weights."""
import hashlib,json,os,subprocess,threading,uuid,wave
from pathlib import Path

LOCK=threading.RLock()
ASR_LOCK=threading.Lock()
TRANSCRIBER=None

def folder_for(root,owner):
    if not owner:raise ValueError("请先登录后设置朗读声音")
    return Path(root)/"readers"/hashlib.sha256(owner.encode()).hexdigest()

def load_profile(root,owner):
    path=folder_for(root,owner)/"profile.json"
    if not path.exists():return {}
    return json.loads(path.read_text("utf-8"))

def save_profile(root,owner,profile):
    folder=folder_for(root,owner);folder.mkdir(parents=True,exist_ok=True)
    temporary=folder/"profile.tmp";temporary.write_text(json.dumps(profile,ensure_ascii=False),encoding="utf-8");temporary.replace(folder/"profile.json")

def public_profile(root,owner):
    with LOCK:profile=load_profile(root,owner)
    result={"voice":None,"draft":None}
    if profile.get("published"):result["voice"]={"id":"__reader","speaker":"我的朗读声","kind":"reader","version":profile["published"]["version"]}
    if profile.get("draft"):result["draft"]={k:profile["draft"].get(k) for k in ("text","duration","notice")}
    return result

def upload(root,owner,body):
    import imageio_ffmpeg
    if not body or len(body)>10*1024*1024:raise ValueError("请上传不超过 10 MB 的录音")
    folder=folder_for(root,owner);folder.mkdir(parents=True,exist_ok=True)
    ident=uuid.uuid4().hex;source=folder/(ident+".upload");target=folder/(ident+".wav")
    source.write_bytes(body)
    try:
        result=subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(),"-nostdin","-v","error","-y","-i",str(source),"-vn","-ac","1","-ar","32000","-t","11","-c:a","pcm_s16le",str(target)],capture_output=True,timeout=30,creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
        if result.returncode:raise ValueError("无法读取音频，请使用 WAV、MP3、M4A 或 FLAC")
        with wave.open(str(target),"rb") as audio:
            duration=audio.getnframes()/audio.getframerate();samples=audio.readframes(audio.getnframes())
        if not 3<=duration<=10:raise ValueError("请使用 3–10 秒的清晰短录音，建议保留完整的一句话")
        import numpy as np
        amplitude=np.abs(np.frombuffer(samples,dtype=np.int16).astype(np.int32))
        if amplitude.max()<100:raise ValueError("录音接近静音，请换一段清晰录音")
        if np.mean(amplitude>=32760)>.01:raise ValueError("录音存在明显破音，请换一段清晰录音")
        draft={"path":str(target),"duration":duration,"text":"","notice":""}
        try:
            global TRANSCRIBER
            from training_pipeline import Transcriber
            with ASR_LOCK:
                if TRANSCRIBER is None:TRANSCRIBER=Transcriber()
                draft["text"]=TRANSCRIBER.run([draft])[0]["text"]
        except Exception:draft["notice"]="自动识别暂不可用，请填写录音里说的原话。"
        with LOCK:
            profile=load_profile(root,owner);profile["draft"]=draft;save_profile(root,owner,profile)
            # Keep the active reference plus the newest two uploads for in-flight speech.
            keep={draft["path"],profile.get("published",{}).get("reference",{}).get("path")}
            recordings=sorted(folder.glob("*.wav"),key=lambda p:p.stat().st_mtime,reverse=True)
            keep.update(str(p) for p in recordings[:2])
            for old in recordings:
                if str(old) not in keep:old.unlink(missing_ok=True)
        return public_profile(root,owner)
    except Exception:
        target.unlink(missing_ok=True);raise
    finally:source.unlink(missing_ok=True)

def publish(root,owner,text):
    text=str(text).strip()
    if not text or len(text)>500:raise ValueError("请填写这段录音的原话（最多 500 字）")
    with LOCK:
        profile=load_profile(root,owner)
        if not profile.get("draft"):raise ValueError("请先上传一段参考录音")
        reference=dict(profile["draft"]);reference["text"]=text;profile["draft"]=reference
        version=uuid.uuid4().hex[:16];profile["published"]={"version":version,"reference":reference};save_profile(root,owner,profile)
    return public_profile(root,owner)

def reference_for(root,owner,version):
    with LOCK:published=load_profile(root,owner).get("published")
    if not published:raise ValueError("请先上传并选用朗读声音")
    if published["version"]!=version:raise ValueError("朗读声音已更新，请重新选用")
    return published["reference"]
