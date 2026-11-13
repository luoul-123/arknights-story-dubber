"""Allowlisted game media, downloaded on demand through the host network."""
import hashlib,json,re,threading
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.parse import quote
INDEX=Path(__file__).parent/'media-index'
PORTRAITS=json.loads((INDEX/'portraits.json').read_text('utf-8'))
MUSIC=json.loads((INDEX/'music.json').read_text('utf-8'))
HISTORY='2c7efe3c96ff8eb96af777ff7508144b4485654a'
class MediaSource:
 def __init__(self,folder):
  self.folder=Path(folder);self.folder.mkdir(parents=True,exist_ok=True);self.lock=threading.Lock();self.locks={}
 def resource(self,kind,name):
  if not re.fullmatch(r'[a-zA-Z0-9_#$-]{1,180}',name or ''):raise ValueError('无效媒体名称')
  if kind=='portrait':
   folder=PORTRAITS.get(name)
   if not folder:raise ValueError('暂未收录此立绘：'+name)
   return 'assets/dyn/avg/characters/'+folder+'/'+name+'.png','image/png',('cn',HISTORY)
  if kind=='music':
   key=name.lstrip('$');asset=MUSIC.get(key) or next((v for k,v in MUSIC.items() if k.lower()==key.lower()),None)
   if not asset:raise ValueError('暂未收录此音乐：'+key)
   return 'assets/dyn/audio/'+asset.lower()+'.mp3','audio/mpeg',(HISTORY,'cn')
  raise ValueError('无效媒体类型')
 def get(self,kind,name):
  relative,mime,versions=self.resource(kind,name)
  target=self.folder/(hashlib.sha256(relative.encode()).hexdigest()+('.png' if kind=='portrait' else '.mp3'))
  with self.lock:lock=self.locks.setdefault(relative,threading.Lock())
  with lock:
   if target.exists():return target.read_bytes(),mime
   for revision in versions:
    for base in ('https://raw.githubusercontent.com/ArknightsAssets/ArknightsAssets2/'+revision+'/', 'https://cdn.jsdelivr.net/gh/ArknightsAssets/ArknightsAssets2@'+revision+'/'):
     try:
      with urlopen(Request(base+quote(relative,safe='/'),headers={'User-Agent':'TerraVoice-Media/1'}),timeout=12) as response:data=response.read(30*1024*1024+1)
      if len(data)>30*1024*1024 or len(data)<10:continue
      if kind=='portrait' and not data.startswith(b'\x89PNG'):continue
      if kind=='music' and not (data.startswith(b'ID3') or data[0]==255):continue
      temporary=target.with_suffix('.tmp');temporary.write_bytes(data);temporary.replace(target);return data,mime
     except Exception:continue
   raise RuntimeError('媒体资源暂时无法加载，请稍后重试')
