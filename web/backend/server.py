"""Private GPU service for the browser-based story theater.

Run behind an HTTPS reverse proxy. Every request needs VOICE_BACKEND_TOKEN.
No desktop UI, screen capture or OCR dependencies are used.
"""
from __future__ import annotations
import argparse, copy, hashlib, hmac, io, json, os, re, secrets, subprocess, sys, threading, time, uuid, wave
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse, urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError
ROOT = Path(__file__).resolve().parent
DATA = Path(os.environ.get("ZHOU_DATA_DIR", str(ROOT.parent / ".voice-data"))).resolve()
DATA.mkdir(parents=True, exist_ok=True)
TOKEN = os.environ.get("VOICE_BACKEND_TOKEN", "")
LOCK = threading.RLock()
GPU = threading.RLock()
EXECUTOR = ThreadPoolExecutor(max_workers=1)
JOBS = {}
ENGINE = None
ENGINE_LOG = None
LOADED = None
NARRATION = None
NARRATION_LOCK = threading.RLock()
ENDPOINT = os.environ.get("GPT_SOVITS_URL", "http://127.0.0.1:9882").rstrip("/")
STORE = DATA / "characters.json"
from story_source import StorySource
STORIES = StorySource(DATA / "stories")
from catalog_metadata import CatalogMetadata
CATALOG_METADATA = CatalogMetadata(DATA)
from default_voices import read_defaults, save_defaults, defaults_version, selected_default
import reader_voice

def read_store():
    if not STORE.exists(): return {}
    return json.loads(STORE.read_text("utf-8"))

def save_store(data):
    temporary = STORE.with_suffix(".tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(STORE)

def public_character(c):
    return {k: v for k, v in c.items() if k not in ("models", "published")} | {
        "models": bool(c.get("models")), "published": bool(c.get("published")),
        "hasReference": any(x.get("text") and 3 <= x.get("duration",0) <= 10 and not x.get("clipped") for x in c.get("clips",[])),
        "clips": [{"id": x["id"], "duration": x["duration"], "text": x.get("text", "")} for x in c.get("clips", [])]
    }

def get_character(data, ident):
    if ident not in data: raise ValueError("角色不存在")
    return data[ident]

def editable(c):
    if c.get("busy"): raise ValueError("该角色有任务正在执行，请等待任务结束")

def create_character(name):
    name = str(name).strip()
    if not name or len(name) > 40 or re.search(r"[\r\n|]", name): raise ValueError("请填写有效的角色名")
    with LOCK:
        data = read_store()
        if any(c["speaker"] == name for c in data.values()): raise ValueError("角色已存在")
        ident = uuid.uuid4().hex
        c = {"id": ident, "speaker": name, "language": "zh", "clips": [], "aliases": [], "models": None, "published": None}
        data[ident] = c
        save_store(data)
    return public_character(c)

def ingest(ident, filename, body):
    if not body: raise ValueError("录音为空")
    import imageio_ffmpeg
    with LOCK:
        data = read_store()
        c = get_character(data, ident)
        editable(c)
        folder = DATA / ident
        folder.mkdir(exist_ok=True)
        source = folder / (uuid.uuid4().hex + ".upload")
        source.write_bytes(body)
        normalized = folder / (uuid.uuid4().hex + ".wav")
        command = [imageio_ffmpeg.get_ffmpeg_exe(), "-nostdin", "-v", "error", "-y", "-i", str(source), "-vn", "-ac", "1", "-ar", "32000", "-t", "600", "-c:a", "pcm_s16le", str(normalized)]
        result = subprocess.run(command, capture_output=True, timeout=90, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        if result.returncode: raise ValueError("文件无法解码，请上传有效音频")
        import numpy as np
        with wave.open(str(normalized), "rb") as w:
            samples = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16)
        duration = len(samples) / 32000
        if duration < 1: raise ValueError("录音太短，请至少上传 1 秒")
        if np.max(np.abs(samples.astype(np.int32))) < 100: raise ValueError("录音接近静音，请检查素材")
        clips = []
        start = 0
        # Boundaries near silence reduce cut-off words; all text remains editable.
        while start < len(samples):
            end = min(start + 8 * 32000, len(samples))
            if len(samples) - end > 32000 and end - start > 5 * 32000:
                candidates = range(start + 5 * 32000, end, 1600)
                end = min(candidates, key=lambda p: float(np.mean(np.abs(samples[p:p+1600].astype(np.float32)))))
            if len(samples) - end < 32000: end = len(samples)
            clip_samples = samples[start:end]
            if len(clip_samples) < 16000: break
            clip_id = uuid.uuid4().hex
            target = folder / (clip_id + ".wav")
            with wave.open(str(target), "wb") as w:
                w.setnchannels(1); w.setsampwidth(2); w.setframerate(32000); w.writeframes(clip_samples.tobytes())
            clips.append({"id": clip_id, "path": str(target), "duration": len(clip_samples)/32000, "text": "", "clipped": bool(np.mean(np.abs(clip_samples.astype(np.int32)) >= 32760) > .01)})
            start = end
        c["clips"].extend(clips)
        save_store(data)
        return {"added": len(clips), "duration": duration}

def import_operator(name):
    from operator_reference import fetch_reference
    name=str(name).strip()
    if not name or len(name)>40:raise ValueError("请输入干员名称")
    reference=fetch_reference(DATA,name)
    with LOCK:
        data=read_store()
        c=next((c for c in data.values() if c["speaker"]==name),None)
        if c is None:
            new=create_character(name);data=read_store();c=data[new["id"]]
        editable(c)
        old=next((x for x in c["clips"] if x.get("sourceVoiceId")==reference["sourceVoiceId"]),None)
        if not old:c["clips"].append(reference)
        c["referenceId"]=(old or reference)["id"]
        save_store(data)
        return public_character(c)

def engine_request(path, payload, timeout=120):
    if path.startswith("/set_"):
        request = Request(ENDPOINT+path+"?"+urlencode(payload))
    else:
        request = Request(ENDPOINT+path, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
    try:
        with urlopen(request, timeout=timeout) as response: return response.read()
    except HTTPError as e:
        raise RuntimeError("语音引擎请求失败："+str(e.code)) from e

def start_engine():
    global ENGINE, ENGINE_LOG, LOADED
    import training_pipeline as pipeline
    if ENGINE and ENGINE.poll() is None: return
    if os.environ.get("GPT_SOVITS_EXTERNAL") == "1":
        with urlopen(ENDPOINT+"/docs", timeout=3): pass
        return
    missing = pipeline.check_engine()
    if missing: raise RuntimeError("GPU 引擎未准备好，缺少 "+Path(missing[0]).name)
    f = pipeline.engine_files()
    import yaml
    config = {"custom": {"device": "cuda", "is_half": True, "version": "v2", "t2s_weights_path": str(f["gpt"]), "vits_weights_path": str(f["sovits"]), "bert_base_path": str(f["bert"]), "cnhuhbert_base_path": str(f["hubert"])}}
    config_path = DATA / "runtime.yaml"
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")
    ENGINE_LOG = (DATA / "engine.log").open("a", encoding="utf-8")
    environment = os.environ.copy()
    environment["PYTHONUTF8"] = "1"
    environment["PATH"] = str(pipeline.ROOT/"engines/tools")+os.pathsep+environment.get("PATH","")
    ENGINE = subprocess.Popen([str(f["python"]), str(f["root"]/"api_v2.py"), "-a", "127.0.0.1", "-p", str(urlparse(ENDPOINT).port or 9882), "-c", str(config_path)], cwd=f["root"], env=environment, stdout=ENGINE_LOG, stderr=subprocess.STDOUT, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    for _ in range(120):
        if ENGINE.poll() is not None: raise RuntimeError("语音引擎启动失败，请检查服务端 engine.log")
        try:
            with urlopen(ENDPOINT+"/docs", timeout=1): return
        except Exception: time.sleep(.5)
    raise RuntimeError("语音引擎启动超时")

def stop_engine():
    global ENGINE, ENGINE_LOG, LOADED
    if ENGINE and ENGINE.poll() is None:
        ENGINE.terminate()
        try: ENGINE.wait(timeout=15)
        except subprocess.TimeoutExpired: ENGINE.kill(); ENGINE.wait()
    ENGINE = None
    LOADED = None
    if ENGINE_LOG: ENGINE_LOG.close(); ENGINE_LOG = None

def select_reference(c):
    options = [x for x in c["clips"] if x.get("text","").strip() and 3 <= x["duration"] <= 10 and not x.get("clipped") and Path(x["path"]).is_file()]
    if not options: raise ValueError("至少需要一段 3–10 秒、已校对文字且无破音的录音")
    preferred=next((x for x in options if x["id"]==c.get("referenceId")),None)
    return copy.deepcopy(preferred or min(options, key=lambda x: abs(x["duration"]-6)))

def models_for(c, mode):
    if mode == "trained":
        if not c.get("models"): raise ValueError("尚未训练角色音色，可改用免训练参考音色")
        models = c["models"]
    elif mode == "reference":
        import training_pipeline as pipeline
        files = pipeline.engine_files()
        models = {k: str(files[k]) for k in ("gpt", "sovits")}
    else: raise ValueError("无效音色模式")
    if not all(Path(models[k]).is_file() for k in ("gpt", "sovits")): raise ValueError("语音模型文件缺失")
    return models

def publish(ident, mode="reference"):
    with LOCK:
        data = read_store(); c = get_character(data, ident); editable(c)
        models = models_for(c, mode)
        version = uuid.uuid4().hex[:16]
        c["published"] = {"version": version, "mode": mode, "models": copy.deepcopy(models), "reference": select_reference(c)}
        save_store(data)
        return {"published": True, "version": version, "mode": mode}

def default_speech(text, kind, speaker=""):
    global NARRATION
    with LOCK:
        config=read_defaults(DATA);store=read_store()
        selected=selected_default(config,speaker,narrator=kind=="__narrator",known=CATALOG_METADATA.get().get("genders",{})) if any(config.values()) else None
        profile=store.get(selected,{})
    if selected:
        if not profile.get("published"):raise ValueError("站点默认音色尚未发布，请联系管理员")
        return synthesize(selected,text,profile["published"]["version"])
    if os.name != "nt":raise RuntimeError("请由站点管理员配置服务器旁白引擎")
    speaker=str(speaker)[:100]
    digest=hashlib.sha256(json.dumps([text,kind,speaker],ensure_ascii=False).encode()).hexdigest()
    target=DATA/"audio"/("default_"+digest+".wav");target.parent.mkdir(exist_ok=True)
    with NARRATION_LOCK:
        if not target.exists():
            if NARRATION is None:
                from narration import Narration
                NARRATION=Narration()
            temporary=target.with_suffix(".tmp")
            NARRATION.render(text,temporary,speaker,narrator=kind=="__narrator")
            temporary.replace(target)
        return target.read_bytes()

def fallback_voices():
    with LOCK:
        config=read_defaults(DATA);store=read_store()
    if os.name!="nt" and not any(config.values()):return []
    version=defaults_version(config,store)
    narrator_id=config.get("narrator") or config.get("female")
    narrator_name=store.get(narrator_id,{}).get("speaker","系统旁白")
    return [{"id":"__narrator","speaker":narrator_name,"version":version,"kind":"narrator"},{"id":"__npc","speaker":"默认男女声" if any(config.values()) else "通用角色","version":version,"kind":"fallback"}]

def synthesize(ident, text, version=None, preview=False, mode="reference", speaker="", reader=""):
    global LOADED
    text = str(text).strip()
    if not text or len(text) > 600: raise ValueError("台词长度需要在 1–600 字之间")
    if not any(ch.isalnum() for ch in text):
        output=io.BytesIO()
        with wave.open(output,"wb") as sound:
            sound.setnchannels(1);sound.setsampwidth(2);sound.setframerate(32000);sound.writeframes(bytes(32000))
        return output.getvalue()
    if ident in ("__narrator","__npc"):return default_speech(text,ident,speaker)
    if ident=="__reader":
        reference=reader_voice.reference_for(DATA,reader,version)
        return render_reference("reader:"+hashlib.sha256(reader.encode()).hexdigest(),text,models_for({},"reference"),reference,version)
    with LOCK:
        c = copy.deepcopy(get_character(read_store(), ident))
    if preview:
        models = models_for(c, mode)
        reference = select_reference(c); identity = str(models)
    else:
        published = c.get("published")
        if not published: raise ValueError("该角色尚未发布音色")
        if version != published["version"]: raise ValueError("音色已更新，请刷新后重试")
        models = published["models"]; reference = published["reference"]; identity = version
    return render_reference(ident,text,models,reference,identity,c.get("language","zh"))

def render_reference(ident,text,models,reference,identity,language="zh"):
    global LOADED
    digest = hashlib.sha256(json.dumps([ident, identity, text, reference], sort_keys=True).encode()).hexdigest()
    target = DATA / "audio" / (digest+".wav")
    target.parent.mkdir(exist_ok=True)
    if target.exists(): return target.read_bytes()
    with GPU:
        if target.exists(): return target.read_bytes()
        start_engine()
        if LOADED != models:
            engine_request("/set_gpt_weights", {"weights_path": models["gpt"]})
            engine_request("/set_sovits_weights", {"weights_path": models["sovits"]})
            LOADED = models
        sound = engine_request("/tts", {"text": text, "text_lang": "zh", "ref_audio_path": reference["path"], "prompt_text": reference["text"], "prompt_lang": language, "text_split_method": "cut5", "media_type": "wav", "streaming_mode": False})
        if not (sound.startswith(b"RIFF") and sound[8:12] == b"WAVE"): raise RuntimeError("引擎没有返回有效音频")
        temporary = target.with_suffix(".tmp"); temporary.write_bytes(sound); temporary.replace(target)
        return sound

def queue_job(kind, ident, epochs=2):
    if kind not in ("train","transcribe"): raise ValueError("无效任务")
    if not 1 <= epochs <= 20: raise ValueError("训练轮次须为 1–20")
    with LOCK:
        data = read_store(); c = get_character(data, ident); editable(c)
        if not c.get("clips"): raise ValueError("请先上传角色录音")
        if kind == "train":
            import training_pipeline as pipeline
            pipeline.training_clips(c)
            select_reference(c)
        job_id = uuid.uuid4().hex
        job = {"id": job_id, "character": ident, "kind": kind, "state": "queued", "progress": 0, "message": "排队等待处理"}
        JOBS[job_id] = job; c["busy"] = job_id; save_store(data)
        profile = copy.deepcopy(c)
    def work():
        job.update(state="running", message="准备任务")
        def progress(message, percent=0):
            job.update(message=message, progress=max(0,min(percent,100)))
        try:
            import training_pipeline as pipeline
            if kind == "transcribe":
                clips = pipeline.Transcriber().run(profile["clips"], profile["language"], progress)
                with LOCK:
                    data = read_store(); data[ident]["clips"] = clips; save_store(data)
            else:
                with GPU:
                    if os.environ.get("GPT_SOVITS_EXTERNAL") == "1": raise RuntimeError("外部推理模式下请使用独立训练 GPU，当前实例未启动训练")
                    stop_engine()
                    train = pipeline.TrainingJob()
                    train.progress = progress
                    models = train.train(profile, DATA/ident, epochs=epochs)
                with LOCK:
                    data = read_store(); data[ident]["models"] = models; save_store(data)
            job.update(state="done", progress=100, message="任务完成")
        except Exception as exc:
            job.update(state="failed", error=str(exc), message="任务失败")
        finally:
            with LOCK:
                data = read_store(); data[ident].pop("busy",None); save_store(data)
    EXECUTOR.submit(work)
    return dict(job)

class Handler(BaseHTTPRequestHandler):
    server_version = "ZhouSheng/1"
    def log_message(self, fmt, *args): pass  # Never log credentials or uploaded content.
    def reply(self, value, status=200):
        if isinstance(value, bytes): body=value; mime="audio/wav"
        else: body=json.dumps(value, ensure_ascii=False).encode(); mime="application/json; charset=utf-8"
        self.send_response(status); self.send_header("Content-Type",mime); self.send_header("Content-Length",str(len(body))); self.send_header("Cache-Control","no-store"); self.end_headers()
        try: self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError): pass
    def dispatch(self):
        if not TOKEN or not hmac.compare_digest(self.headers.get("Authorization",""), "Bearer "+TOKEN):
            self.reply({"error":"未授权"},401);return
        parsed=urlparse(self.path); path=parsed.path.strip("/"); query=parse_qs(parsed.query)
        reader=self.headers.get("X-Reader-Id","")
        try:
            if self.command=="GET":
                if path=="stories":
                    ident=query.get("id",[None])[0];result=STORIES.get(ident)
                    if ident is None:result["metadata"]=CATALOG_METADATA.get()
                    return self.reply(result)
                if path=="reader/voice":return self.reply(reader_voice.public_profile(DATA,reader))
                if path=="voices":
                    with LOCK:
                        voices=[{"id":c["id"],"speaker":c["speaker"],"aliases":c.get("aliases",[]),"version":c["published"]["version"]} for c in read_store().values() if c.get("published")]
                    return self.reply({"voices":voices+fallback_voices()})
                if path=="admin/defaults":
                    with LOCK:return self.reply({"defaults":read_defaults(DATA)})
                if path=="admin/characters":
                    with LOCK: return self.reply({"characters":[public_character(c) for c in read_store().values()]})
                if path.startswith("admin/jobs/"):
                    job=JOBS.get(path.rsplit("/",1)[-1])
                    return self.reply(dict(job) if job else {"error":"任务不存在或服务已重启"},200 if job else 404)
                return self.reply({"error":"接口不存在"},404)
            length=int(self.headers.get("Content-Length","0"))
            if length<0 or length>50*1024*1024:return self.reply({"error":"请求不能超过 50 MB"},413)
            body=self.rfile.read(length)
            if path=="reader/upload":return self.reply(reader_voice.upload(DATA,reader,body))
            if path=="admin/upload":return self.reply(ingest(query.get("character",[""])[0],query.get("filename",["audio"])[0],body))
            if length>16384:return self.reply({"error":"请求过大"},413)
            data=json.loads(body or b"{}")
            if path=="reader/voice":return self.reply(reader_voice.publish(DATA,reader,data.get("text","")))
            if path=="admin/defaults":
                with LOCK:defaults=save_defaults(DATA,read_store(),data)
                return self.reply({"defaults":defaults})
            if path=="admin/characters":return self.reply(create_character(data.get("speaker","")))
            if path=="admin/import-operator":return self.reply(import_operator(data.get("name","")))
            if path=="admin/transcript":
                with LOCK:
                    store=read_store(); c=get_character(store,data["id"]); editable(c)
                    clip=next((x for x in c["clips"] if x["id"]==data["clipId"]),None)
                    if not clip:raise ValueError("录音不存在")
                    text=str(data.get("text","")).strip()
                    if len(text)>2000:raise ValueError("文本过长")
                    clip["text"]=text;save_store(store)
                return self.reply({"saved":True})
            if path in ("admin/transcribe","admin/train"):return self.reply(queue_job(path.split("/")[1],data["id"],int(data.get("epochs",2))),202)
            if path=="admin/publish":return self.reply(publish(data["id"], data.get("mode","reference")))
            if path=="admin/preview":return self.reply(synthesize(data["id"],data.get("text",""),preview=True, mode=data.get("mode","reference")))
            if path=="speech":return self.reply(synthesize(data["voiceId"],data.get("text",""),data.get("version"),speaker=data.get("speaker",""),reader=reader))
            return self.reply({"error":"接口不存在"},404)
        except (ValueError,KeyError,json.JSONDecodeError) as e:self.reply({"error":str(e)},400)
        except Exception as e:self.reply({"error":str(e)},500)
    do_GET=dispatch
    do_POST=dispatch

def main():
    if len(TOKEN)<24: raise SystemExit("设置至少 24 字符的 VOICE_BACKEND_TOKEN 后再启动。")
    with LOCK:
        data=read_store()
        for c in data.values():c.pop("busy",None)
        save_store(data)
    parser=argparse.ArgumentParser();parser.add_argument("--host",default="127.0.0.1");parser.add_argument("--port",type=int,default=9881);args=parser.parse_args()
    server=ThreadingHTTPServer((args.host,args.port),Handler)
    print(f"TerraVoice local service listening on {args.host}:{args.port}",flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:
        server.server_close();stop_engine()
        if NARRATION:NARRATION.close()
        EXECUTOR.shutdown(wait=False,cancel_futures=True)
if __name__=="__main__":main()
