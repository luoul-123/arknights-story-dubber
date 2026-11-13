"""Discard stale speech before it reaches the GPU. Active inference finishes once."""
import threading
from collections import OrderedDict
LOCK=threading.Lock();LATEST=OrderedDict();CONTEXT=threading.local()
def register(reader,stream,sequence):
 if not stream:CONTEXT.request=None;return
 key=(reader,str(stream)[:100]);sequence=int(sequence)
 with LOCK:
  LATEST[key]=max(sequence,LATEST.get(key,-1));LATEST.move_to_end(key)
  while len(LATEST)>512:LATEST.popitem(last=False)
 CONTEXT.request=(key,sequence)
def check_current():
 request=getattr(CONTEXT,'request',None)
 if request:
  key,sequence=request
  with LOCK:
   if LATEST.get(key)!=sequence:raise ValueError('台词已跳过')
