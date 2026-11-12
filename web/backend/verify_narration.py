"""Synthesize a fresh line using an existing trained character. Never plays it."""
import json,os,sys,time,wave,io
from pathlib import Path
from urllib.request import Request,urlopen
base=Path(__file__).resolve().parent
config=dict(line.split("=",1) for line in (base.parent/".dev.vars").read_text("utf-8").splitlines() if "=" in line)
def call(path,payload=None):
 req=Request("http://127.0.0.1:9881/"+path,data=json.dumps(payload).encode() if payload is not None else None,headers={"Authorization":"Bearer "+config["VOICE_BACKEND_TOKEN"],"Content-Type":"application/json"})
 with urlopen(req,timeout=180) as response:return response.read()
for ident,speaker,text in [("__narrator","旁白","夜色渐深，罗德岛的灯光仍然亮着。"),("__npc","陌生的旅人","你好，博士，请沿着这条路继续前进。")]:
 start=time.monotonic()
 raw=call("speech",{"voiceId":ident,"speaker":speaker,"version":"system-v1","text":text})
 with wave.open(io.BytesIO(raw)) as a:duration=a.getnframes()/a.getframerate()
 print(json.dumps({"kind":ident,"duration":round(duration,2),"seconds":round(time.monotonic()-start,2)},ensure_ascii=False))
