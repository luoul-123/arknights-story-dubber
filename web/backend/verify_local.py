"""Synthesize a fresh line using an existing trained character. Never plays it."""
import json,os,sys,time,wave,io
from pathlib import Path
from urllib.request import Request,urlopen
base=Path(__file__).resolve().parent
config=dict(line.split("=",1) for line in (base.parent/".dev.vars").read_text("utf-8").splitlines() if "=" in line)
def call(path,payload=None):
 req=Request("http://127.0.0.1:9881/"+path,data=json.dumps(payload).encode() if payload is not None else None,headers={"Authorization":"Bearer "+config["VOICE_BACKEND_TOKEN"],"Content-Type":"application/json"})
 with urlopen(req,timeout=180) as response:return response.read()
characters=json.loads(call("admin/characters"))["characters"]
trained=next((c for c in characters if c["models"]),None)
if not trained:raise SystemExit("No trained character to verify")
start=time.monotonic()
raw=call("admin/preview",{"id":trained["id"],"mode":"trained","text":"博士，网页剧场已经准备好了。我们继续前进吧。"})
with wave.open(io.BytesIO(raw)) as audio:
 result={"character":trained["speaker"],"duration":round(audio.getnframes()/audio.getframerate(),2),"sample_rate":audio.getframerate(),"seconds":round(time.monotonic()-start,2),"bytes":len(raw)}
out=base.parent/"work"/"verified-character.wav";out.write_bytes(raw)
print(json.dumps(result,ensure_ascii=False))
