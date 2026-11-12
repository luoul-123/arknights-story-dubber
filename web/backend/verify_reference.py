import json,time,wave,io
from pathlib import Path
from urllib.request import Request,urlopen
config=dict(line.split("=",1) for line in (Path(__file__).resolve().parent.parent/".dev.vars").read_text("utf-8").splitlines() if "=" in line)
def call(path,payload=None):
 req=Request("http://127.0.0.1:9881/"+path,data=json.dumps(payload).encode() if payload is not None else None,headers={"Authorization":"Bearer "+config["VOICE_BACKEND_TOKEN"],"Content-Type":"application/json"})
 with urlopen(req,timeout=180) as response:return response.read()
trained=json.loads(call("admin/import-operator",{"name":"杜宾"}))
print(json.dumps({"imported":trained["speaker"],"has_reference":trained["hasReference"],"trained_model":trained["models"]},ensure_ascii=False),flush=True)
# Publish only this local workspace copy; nothing is sent to cloud hosting.
published=json.loads(call("admin/publish",{"id":trained["id"],"mode":"reference"}))
start=time.monotonic()
raw=call("speech",{"voiceId":trained["id"],"version":published["version"],"text":"博士，我们已经抵达目的地。请做好下一步的准备。"})
with wave.open(io.BytesIO(raw)) as a:duration=a.getnframes()/a.getframerate()
print(json.dumps({"character":trained["speaker"],"warm_seconds":round(time.monotonic()-start,2),"audio_seconds":round(duration,2),"published_locally":True},ensure_ascii=False))
