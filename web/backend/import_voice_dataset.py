"""Admin-only local import of complete, transcribed voice clips. Does not train or publish."""
import argparse,hashlib,json,subprocess,uuid,wave
from pathlib import Path
import numpy as np
import imageio_ffmpeg
import server


def import_dataset(manifest):
    imported=[]
    for person in manifest:
        name=person["speaker"].strip()
        with server.LOCK:
            store=server.read_store();profile=next((c for c in store.values() if c["speaker"]==name),None)
            if profile is None:
                ident=server.create_character(name)["id"];store=server.read_store();profile=store[ident]
            server.editable(profile);folder=server.DATA/profile["id"];folder.mkdir(exist_ok=True)
            for clip in person["clips"]:
                text=clip["text"].strip();source=Path(clip["path"]).resolve()
                if not source.is_file() or not text:raise ValueError("每条录音必须有现存文件及对应文字")
                source_id=hashlib.sha256((str(clip.get("source",source))+text).encode()).hexdigest()
                existing=next((c for c in profile["clips"] if c.get("sourceKey")==source_id),None)
                if existing:
                    if clip.get("reference"):profile["referenceId"]=existing["id"]
                    continue
                ident=uuid.uuid4().hex;target=folder/(ident+".wav")
                result=subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(),"-nostdin","-v","error","-y","-i",str(source),"-vn","-ac","1","-ar","32000","-c:a","pcm_s16le",str(target)],capture_output=True,timeout=30,creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
                if result.returncode:raise ValueError("录音转换失败")
                with wave.open(str(target)) as wav:samples=np.frombuffer(wav.readframes(wav.getnframes()),dtype=np.int16);duration=len(samples)/wav.getframerate()
                clipped=bool(np.mean(np.abs(samples.astype(np.int32))>=32760)>.01)
                if duration<.7 or np.max(np.abs(samples.astype(np.int32)))<100:raise ValueError("录音过短或接近静音")
                profile["clips"].append({"id":ident,"path":str(target),"text":text,"duration":duration,"clipped":clipped,"sourceKey":source_id,"source":clip.get("source"),"referenceOnly":bool(clip.get("referenceOnly"))})
                if clip.get("reference"):profile["referenceId"]=ident
            profile["gender"]=person["gender"];profile["sourceCharacterId"]=person.get("characterId");server.save_store(store)
            imported.append({"id":profile["id"],"speaker":name,"gender":person["gender"],"clips":len(profile["clips"]),"seconds":round(sum(c["duration"] for c in profile["clips"] if not c.get("referenceOnly")),2)})
    return imported

if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("manifest",type=Path);args=parser.parse_args()
    print(json.dumps(import_dataset(json.loads(args.manifest.read_text("utf-8"))),ensure_ascii=False))
