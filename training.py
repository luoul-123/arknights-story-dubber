"""Recorded-character profiles and the official GPT-SoVITS v2 training pipeline."""
from __future__ import annotations
import copy
import hashlib
import json
import os
import queue
import re
import subprocess
import threading
import time
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parent
LIBRARY = ROOT / 'voice_profiles'
SETTINGS = ROOT / 'app_settings.json'


def settings():
    data = {'engine_root': str(ROOT/'engines/GPT-SoVITS'),
            'engine_python': str(ROOT/'engines/runtime/Scripts/python.exe')}
    if SETTINGS.exists():
        data.update(json.loads(SETTINGS.read_text(encoding='utf-8')))
    return data


def save_settings(data):
    SETTINGS.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')


class CharacterStore:
    def __init__(self):
        LIBRARY.mkdir(exist_ok=True)
        self.path = LIBRARY/'profiles.json'
        self.data = json.loads(self.path.read_text(encoding='utf-8')) if self.path.exists() else {}

    def save(self):
        temp = self.path.with_suffix('.tmp')
        temp.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), encoding='utf-8')
        temp.replace(self.path)

    def ensure(self, name, language='zh'):
        name = name.strip()
        if not name or any(c in name for c in '\r\n|'):
            raise ValueError('请填写角色名，例如“阿米娅”')
        if name not in self.data:
            self.data[name] = {'speaker':name, 'clips':[], 'language':language, 'status':'未录制'}
            self.save()
        return self.data[name]

    def folder(self, name):
        path = LIBRARY/'characters'/hashlib.sha256(name.encode()).hexdigest()[:16]
        path.mkdir(parents=True, exist_ok=True)
        return path

    def reference(self, name):
        profile = self.data.get(name, {})
        valid = [c for c in profile.get('clips', []) if c.get('text') and 3 <= c.get('duration', 0) <= 10 and Path(c['path']).exists()]
        if not valid:
            return None
        clip = dict(min(valid, key=lambda c: (c.get('clipped', False), abs(c['duration']-6))))
        clip['language'] = profile.get('language', 'zh')
        clip['models'] = profile.get('models', {})
        return clip


class Transcriber:
    def __init__(self):
        self.model = None

    def run(self, clips, language='zh', progress=lambda *args: None):
        from faster_whisper import WhisperModel
        model_path = ROOT/'models/faster-whisper-small'
        if not (model_path/'model.bin').is_file():
            raise RuntimeError('请先在“运行设置”下载中文转写模型；录音已保存在本机')
        if self.model is None:
            self.model = WhisperModel(str(model_path), device='cpu', compute_type='int8', cpu_threads=4)
        result = copy.deepcopy(clips)
        for index, clip in enumerate(result):
            progress(f'正在转写第 {index+1}/{len(result)} 段语音', int(index/max(1,len(result))*100))
            segments, _ = self.model.transcribe(clip['path'], language=language, beam_size=3,
                condition_on_previous_text=False, vad_filter=True,
                initial_prompt='以下为简体中文语音转写。' if language=='zh' else None)
            clip['text'] = ''.join(s.text for s in segments).strip()
        return result


class ProcessJob:
    def __init__(self):
        self.messages = queue.Queue()
        self.cancelled = threading.Event()
        self.process = None

    def progress(self, text, percent=0):
        if self.cancelled.is_set():
            raise RuntimeError('任务已取消')
        self.messages.put((text, percent))

    def cancel(self):
        self.cancelled.set()
        if self.process and self.process.poll() is None:
            subprocess.run(['taskkill','/PID',str(self.process.pid),'/T','/F'], capture_output=True,
                           creationflags=subprocess.CREATE_NO_WINDOW)

    def run_process(self, args, cwd=ROOT, env=None, line_progress=None):
        if self.cancelled.is_set():
            raise RuntimeError('任务已取消，已保存的录音和样本仍保留')
        env = dict(env or os.environ)
        env.update(PYTHONUTF8='1', PYTHONIOENCODING='utf-8', PYTHONUNBUFFERED='1')
        self.process = subprocess.Popen([str(a) for a in args], cwd=cwd, env=env,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding='utf-8', errors='replace',
            creationflags=subprocess.CREATE_NO_WINDOW)
        tail = []
        for line in self.process.stdout:
            line = line.strip()
            if line:
                tail.append(line)
                tail = tail[-12:]
                self.messages.put((line[-300:], -1))
                if line_progress:
                    line_progress(line)
        code = self.process.wait()
        if self.cancelled.is_set():
            raise RuntimeError('任务已取消')
        if code:
            raise RuntimeError('任务未完成：\n'+'\n'.join(tail[-4:]))


def engine_files(config=None):
    config = config or settings()
    engine = Path(config['engine_root'])
    pretrained = engine/'GPT_SoVITS/pretrained_models'
    weights = pretrained/'gsv-v2final-pretrained'
    return {'root':engine, 'python':Path(config['engine_python']),
        'gpt':weights/'s1bert25hz-5kh-longer-epoch=12-step=369668.ckpt',
        'sovits':weights/'s2G2333k.pth', 'discriminator':weights/'s2D2333k.pth',
        'bert':pretrained/'chinese-roberta-wwm-ext-large', 'hubert':pretrained/'chinese-hubert-base'}


def check_engine(config=None):
    f = engine_files(config)
    required = [f['python'],f['root']/'api_v2.py',f['root']/'GPT_SoVITS/s1_train.py',f['root']/'GPT_SoVITS/s2_train.py',
        f['gpt'],f['sovits'],f['discriminator'],f['bert']/'pytorch_model.bin',f['hubert']/'pytorch_model.bin',
        f['root']/'GPT_SoVITS/pretrained_models/fast_langdetect/lid.176.bin',
        f['root']/'GPT_SoVITS/text/G2PWModel/g2pW.onnx']
    missing = [str(p) for p in required if not p.is_file()]
    return missing


def training_clips(profile, minimum_seconds=30):
    clips = [c for c in profile.get('clips', []) if c.get('text','').strip() and Path(c['path']).is_file() and not c.get('clipped')]
    seconds = sum(c.get('duration',0) for c in clips)
    if seconds < minimum_seconds:
        raise ValueError(f'还差 {minimum_seconds-seconds:.1f} 秒有效语音：快速训练需要 {minimum_seconds} 秒已转写、无破音的录音。也可以先直接试听。')
    return clips


class TrainingJob(ProcessJob):
    def train(self, profile, folder, config=None, epochs=2):
        files = engine_files(config)
        missing = check_engine(config)
        if missing:
            raise RuntimeError('本地训练引擎尚未准备好，请在“运行设置”完成安装。缺少：'+Path(missing[0]).name)
        clips = training_clips(profile)
        folder = Path(folder)
        work = folder/'training'/time.strftime('%Y%m%d_%H%M%S')
        work.mkdir(parents=True, exist_ok=True)
        name = folder.name
        language = profile.get('language','zh')
        listing = work/'recordings.list'
        listing.write_text('\n'.join(f"{c['path']}|{name}|{language}|{c['text'].replace('|','，').replace(chr(10),'')}" for c in clips)+'\n',encoding='utf-8')
        env = os.environ.copy()
        env.update({'version':'v2','is_half':'True','i_part':'0','all_parts':'1',
            '_CUDA_VISIBLE_DEVICES':'0','hz':'25hz','PYTHONUTF8':'1','PYTHONIOENCODING':'utf-8',
            'inp_text':str(listing),'inp_wav_dir':'','exp_name':name,'opt_dir':str(work),
            'bert_pretrained_dir':str(files['bert']), 'cnhubert_base_dir':str(files['hubert']),
            'pretrained_s2G':str(files['sovits']), 's2config_path':str(files['root']/'GPT_SoVITS/configs/s2.json')})
        env['PATH'] = str(ROOT/'engines/tools') + os.pathsep + env.get('PATH','')
        env['PYTHONPATH'] = str(files['root']) + os.pathsep + str(files['root']/'GPT_SoVITS')
        for script, label, percent in [('1-get-text.py','准备文字和发音特征',10),
                ('2-get-hubert-wav32k.py','提取角色声学特征',25),('3-get-semantic.py','准备语义特征',40)]:
            self.progress(label,percent)
            self.run_process([files['python'],'-s',files['root']/'GPT_SoVITS/prepare_datasets'/script],files['root'],env)
        text_part, semantic_part = work/'2-name2text-0.txt', work/'6-name2semantic-0.tsv'
        if not text_part.exists() or not semantic_part.exists():
            raise RuntimeError('特征提取没有生成训练数据，请查看任务日志')
        text_data = text_part.read_text(encoding='utf-8').strip()
        semantic_data = semantic_part.read_text(encoding='utf-8').strip()
        if not text_data or not semantic_data:
            raise RuntimeError('没有有效特征；请检查转写文字、录音语言和背景音乐')
        (work/'2-name2text.txt').write_text(text_data+'\n',encoding='utf-8')
        (work/'6-name2semantic.tsv').write_text('item_name\tsemantic_audio\n'+semantic_data+'\n',encoding='utf-8')
        output = work/'weights'
        output.mkdir(exist_ok=True)
        (work/'logs_s2_v2').mkdir(exist_ok=True)
        s2 = json.loads((files['root']/'GPT_SoVITS/configs/s2.json').read_text(encoding='utf-8'))
        s2['train'].update(batch_size=2,epochs=epochs,fp16_run=True,text_low_lr_rate=.4,
            pretrained_s2G=str(files['sovits']),pretrained_s2D=str(files['discriminator']),
            if_save_latest=True,if_save_every_weights=True,save_every_epoch=min(4,epochs),gpu_numbers='0',grad_ckpt=True)
        s2['model']['version']='v2'
        s2['data']['exp_dir']=str(work)
        s2.update(s2_ckpt_dir=str(work),save_weight_dir=str(output),name=name,version='v2')
        s2path=work/'s2.json'; s2path.write_text(json.dumps(s2),encoding='utf-8')
        self.progress('正在训练角色音色 · SoVITS',55)
        def epoch_progress(line, stage, start, span):
            match=re.search(r'(?:====> Epoch: |VOICE_EPOCH=)(\d+)',line)
            if match:
                epoch=int(match.group(1))
                self.progress(f'{stage} · 已完成 {epoch}/{epochs} 轮', min(start+span,start+round(span*epoch/epochs)))
        self.run_process([files['python'],'-s',files['root']/'GPT_SoVITS/s2_train.py','--config',s2path],files['root'],env,
                         lambda line:epoch_progress(line,'训练音色',55,22))
        s1=yaml.safe_load((files['root']/'GPT_SoVITS/configs/s1longer-v2.yaml').read_text(encoding='utf-8'))
        s1['train'].update(batch_size=2,epochs=epochs,save_every_n_epoch=min(4,epochs),if_save_every_weights=True,
            if_save_latest=True,if_dpo=False,half_weights_save_dir=str(output),exp_name=name)
        s1['data']['num_workers']=0
        s1.update(pretrained_s1=str(files['gpt']),train_semantic_path=str(work/'6-name2semantic.tsv'),
            train_phoneme_path=str(work/'2-name2text.txt'),output_dir=str(work/'logs_s1_v2'))
        s1path=work/'s1.yaml'; s1path.write_text(yaml.safe_dump(s1),encoding='utf-8')
        self.progress('正在训练台词生成 · GPT',78)
        self.run_process([files['python'],'-s',ROOT/'train_single_gpu.py','--source',files['root']/'GPT_SoVITS/s1_train.py','--config_file',s1path],files['root'],env,
                         lambda line:epoch_progress(line,'训练语气',78,20))
        gpt=sorted(output.glob('*.ckpt'),key=lambda p:p.stat().st_mtime)
        sovits=sorted(output.glob('*.pth'),key=lambda p:p.stat().st_mtime)
        if not gpt or not sovits:
            raise RuntimeError('训练进程已结束，但没有生成完整的角色模型；未标记为训练完成')
        self.progress('角色模型已生成，可以试听',100)
        return {'gpt':str(gpt[-1]),'sovits':str(sovits[-1]),'trained_at':int(time.time()),'epochs':epochs}
