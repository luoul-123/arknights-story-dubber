"""CPU narration/NPC TTS. Emits real audio files for background playback."""
import hashlib,json,queue,subprocess,threading
from pathlib import Path
class Narration:
 def __init__(self):
  self.process=None;self.lock=threading.Lock();self.messages=queue.Queue();self.voices=[]
 def call(self,op,**payload):
  with self.lock:
   if self.process is None or self.process.poll() is not None:
    self.messages=queue.Queue()
    self.process=subprocess.Popen(["powershell.exe","-NoProfile","-ExecutionPolicy","Bypass","-File",str(Path(__file__).with_name("narration-worker.ps1"))],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,encoding="utf-8",bufsize=1,creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
    process=self.process;messages=self.messages
    def read():
     try:
      for line in process.stdout:messages.put(json.loads(line))
     finally:messages.put({"error":"旁白进程已退出"})
    threading.Thread(target=read,daemon=True).start()
    if not self.messages.get(timeout=20).get("ready"):raise RuntimeError("旁白服务启动失败")
   self.process.stdin.write(json.dumps({"op":op,**payload},ensure_ascii=False)+"\n");self.process.stdin.flush()
   answer=self.messages.get(timeout=30)
   if answer.get("error"):raise RuntimeError(answer["error"])
   return answer
 def render(self,text,target,speaker="",narrator=False):
  if not self.voices:self.voices=self.call("voices")["voices"]
  if not self.voices:raise RuntimeError("服务器没有可用的中文旁白声音")
  index=0 if narrator else int(hashlib.sha256(speaker.encode()).hexdigest()[:8],16)%len(self.voices)
  self.call("tts",text=text,voice=self.voices[index]["id"],path=str(target))
 def close(self):
  if self.process and self.process.poll() is None:
   self.process.terminate()
   try:self.process.wait(timeout=3)
   except subprocess.TimeoutExpired:self.process.kill()
