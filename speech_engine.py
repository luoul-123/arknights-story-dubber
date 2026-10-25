"""Warm system speech, cached utterances and an optional managed character engine."""
from __future__ import annotations
import hashlib
import json
import os
import re
import subprocess
import time
import wave
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from urllib.parse import urlencode, urlsplit
import yaml
from windows_services import WindowsWorker, CACHE, ROOT
from training import engine_files, check_engine


def speech_text(text):
    adverbs='慢慢|轻轻|悄悄|静静|默默|缓缓|狠狠|仔细|认真|努力|用力|小心|温柔|艰难|清楚|坚定|迅速|清晰|冷静|愉快|惊讶|突然|不安|无声|安静|平静|激动|自信'
    return re.sub(rf'({adverbs})地',r'\1的',text).replace('——','，')


class SpeechEngine:
    def __init__(self):
        self.native=WindowsWorker()
        self.voice=''
        self.server=None
        self.server_log=None
        self.loaded_models=None
        self.cooldown=0.0
        self.endpoint='http://127.0.0.1:9880'
        self.character_ready=False
        self.last_error=''

    def warmup(self):
        voices=self.native.call('voices')['voices']
        if not voices: raise RuntimeError('未安装 Windows 中文语音')
        self.voice=next((v['id'] for v in voices if 'Huihui' in v['name']),voices[0]['id'])
        temp=CACHE/'warmup.wav'
        self.native.call('tts',text='就绪',voice=self.voice,path=str(temp))
        temp.unlink(missing_ok=True)
        return '系统中文声线就绪'

    def _json(self,path,payload,timeout=5):
        if path.startswith('/set_'):
            request=Request(self.endpoint+path+'?'+urlencode(payload))
        else:
            request=Request(self.endpoint+path,data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'})
        try:
            with urlopen(request,timeout=timeout) as response: return response.read()
        except HTTPError as exc:
            detail=exc.read().decode('utf-8',errors='replace')[:1800]
            raise RuntimeError(f'角色引擎 {exc.code}: {detail}') from exc

    def start_server(self,progress=lambda *args:None,cancel_event=None):
        try:
            with urlopen(self.endpoint+'/docs',timeout=1) as response:
                if response.status==200:
                    self.character_ready=True
                    return '角色语音引擎已连接'
        except Exception: pass
        missing=check_engine()
        if missing: raise RuntimeError('请先在运行设置安装本地语音引擎')
        files=engine_files()
        config={'custom':{'device':'cuda','is_half':True,'version':'v2','t2s_weights_path':str(files['gpt']),
            'vits_weights_path':str(files['sovits']),'bert_base_path':str(files['bert']),'cnhuhbert_base_path':str(files['hubert'])}}
        config_path=CACHE/'tts_runtime.yaml'; config_path.write_text(yaml.safe_dump(config),encoding='utf-8')
        env=os.environ.copy(); env['PATH']=str(ROOT/'engines/tools')+os.pathsep+env.get('PATH',''); env['PYTHONUTF8']='1'
        self.server_log=(CACHE/'character_engine.log').open('a',encoding='utf-8')
        self.server=subprocess.Popen([str(files['python']),str(files['root']/'api_v2.py'),'-a','127.0.0.1','-p',str(urlsplit(self.endpoint).port or 9880),'-c',str(config_path)],
            cwd=files['root'],env=env,stdout=self.server_log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
        for _ in range(120):
            if cancel_event is not None and cancel_event.is_set():
                self.release_character()
                raise RuntimeError('角色引擎加载已取消')
            if self.server.poll() is not None:
                self.release_character()
                raise RuntimeError('角色语音引擎启动失败，请查看 .demo_cache/character_engine.log')
            try:
                with urlopen(self.endpoint+'/docs',timeout=1) as response:
                    if response.status==200:
                        self.loaded_models={'gpt':str(files['gpt']),'sovits':str(files['sovits'])}
                        self.character_ready=True
                        return '角色语音引擎已连接'
            except Exception: time.sleep(.5)
        self.release_character()
        raise RuntimeError('角色语音引擎启动超时')

    def synthesize(self,text,reference=None,use_cache=True):
        started=time.perf_counter()
        spoken=speech_text(text)
        identity={'text':spoken,'voice':self.voice,'reference':reference}
        digest=hashlib.sha256(json.dumps(identity,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
        target=CACHE/f'voice_{digest}.wav'
        is_character=bool(reference)
        if use_cache and target.exists(): return target,'角色声线' if is_character else '默认旁白',0
        mode='默认旁白'
        if reference and self.character_ready and time.monotonic()>=self.cooldown:
            try:
                models=reference.get('models') or {k:str(engine_files()[k]) for k in ('gpt','sovits')}
                if models != self.loaded_models:
                    self._json('/set_gpt_weights',{'weights_path':models['gpt']},15)
                    self._json('/set_sovits_weights',{'weights_path':models['sovits']},15)
                    self.loaded_models=models
                audio=self._json('/tts',{'text':text.replace('——','，'),'text_lang':'zh','ref_audio_path':reference['path'],
                    'prompt_text':reference['text'],'prompt_lang':reference.get('language','zh'),
                    'text_split_method':'cut5','media_type':'wav','streaming_mode':False},30)
                if not (audio.startswith(b'RIFF') and audio[8:12]==b'WAVE'): raise RuntimeError('角色引擎未返回音频')
                target.write_bytes(audio)
                self.last_error=''
                mode='角色声线'
                return target,mode,round((time.perf_counter()-started)*1000)
            except Exception as exc:
                self.last_error=str(exc)
                with (CACHE/'voice_errors.log').open('a',encoding='utf-8') as log:
                    log.write(time.strftime('%Y-%m-%d %H:%M:%S')+' '+self.last_error+'\n')
                self.cooldown=time.monotonic()+20
                mode='角色引擎未就绪 · 默认旁白'
        # Do not cache a fallback under a character model's identity.
        if reference:
            if mode=='默认旁白': mode='角色引擎未就绪 · 默认旁白'
            target=CACHE/f'default_{hashlib.sha256(spoken.encode()).hexdigest()}.wav'
        if not target.exists():
            self.native.call('tts',text=spoken,voice=self.voice,path=str(target))
        with wave.open(str(target),'rb') as wav:
            if wav.getnframes()==0: raise RuntimeError('生成的音频为空')
        return target,mode,round((time.perf_counter()-started)*1000)

    def close(self):
        self.native.close()
        self.release_character()

    def release_character(self):
        self.character_ready=False
        self.loaded_models=None
        if self.server and self.server.poll() is None:
            self.server.terminate()
            try: self.server.wait(timeout=3)
            except subprocess.TimeoutExpired: self.server.kill()
        self.server=None
        if self.server_log: self.server_log.close(); self.server_log=None
