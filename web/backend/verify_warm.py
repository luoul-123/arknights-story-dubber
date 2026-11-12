import json,time,wave,io
from pathlib import Path
from urllib.request import Request,urlopen
config=dict(line.split("=",1) for line in (Path(__file__).resolve().parent.parent/".dev.vars").read_text("utf-8").splitlines() if "=" in line)
def call(path,payload=None):
 req=Request("http://127.0.0.1:9881/"+path,data=json.dumps(payload).encode() if payload is not None else None,headers={"Authorization":"Bearer "+config["VOICE_BACKEND_TOKEN"],"Content-Type":"application/json"})
 with urlopen(req,timeout=180) as response:return response.read()
characters=json.loads(call("admin/characters"))["characters"]
trained=next(c for c in characters if c["models"])
# Publish only this local workspace copy; nothing is sent to cloud hosting.
published=json.loads(call("admin/publish",{"id":trained["id"]}))
start=time.monotonic()
raw=call("speech",{"voiceId":trained["id"],"version":published["version"],"text":"这是网页配音的第二句，切换时可以随时跳过。"})
with wave.open(io.BytesIO(raw)) as a:duration=a.getnframes()/a.getframerate()
print(json.dumps({"character":trained["speaker"],"warm_seconds":round(time.monotonic()-start,2),"audio_seconds":round(duration,2),"published_locally":True},ensure_ascii=False))
