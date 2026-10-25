"""Install only into this project's engines/models directories. Restartable."""
from __future__ import annotations
import argparse
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--asr-only',action='store_true')
    args=parser.parse_args()
    os.environ['HF_HOME']=str(ROOT/'models/hf_cache')
    os.environ['UV_CACHE_DIR']=str(ROOT/'.demo_cache/uv')
    os.environ['UV_PYTHON_INSTALL_DIR']=str(ROOT/'engines/python')
    os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING']='1'
    from huggingface_hub import snapshot_download
    print('下载本地转写模型（首次约 500 MB，支持断点续传）',flush=True)
    snapshot_download('Systran/faster-whisper-small',local_dir=str(ROOT/'models/faster-whisper-small'),
                      allow_patterns=['*.json','*.bin','*.txt'])
    if args.asr_only:
        print('转写模型已就绪',flush=True)
        return
    import requests
    import uv
    uv_exe=uv.find_uv_bin()
    def run(*parts):
        print('正在执行：'+' '.join(map(str,parts)),flush=True)
        subprocess.run([str(p) for p in parts],cwd=ROOT,check=True)
    engine=ROOT/'engines/GPT-SoVITS'
    if not (engine/'api_v2.py').exists():
        print('下载 GPT-SoVITS 官方源码',flush=True)
        archive=ROOT/'.demo_cache/gpt-sovits.zip'
        archive.parent.mkdir(exist_ok=True)
        with requests.get('https://codeload.github.com/RVC-Boss/GPT-SoVITS/zip/refs/heads/main',stream=True,timeout=(20,90)) as response:
            response.raise_for_status()
            with archive.open('wb') as out:
                for chunk in response.iter_content(1024*1024): out.write(chunk)
        engine.mkdir(parents=True,exist_ok=True)
        with zipfile.ZipFile(archive) as bundle:
            for item in bundle.infolist():
                parts=Path(item.filename).parts[1:]
                if not parts: continue
                target=engine.joinpath(*parts).resolve()
                if not target.is_relative_to(engine.resolve()): raise ValueError('源码压缩包包含非法路径')
                if item.is_dir(): target.mkdir(parents=True,exist_ok=True)
                else:
                    target.parent.mkdir(parents=True,exist_ok=True)
                    with bundle.open(item) as src,target.open('wb') as out: shutil.copyfileobj(src,out)
    print('准备独立 Python 3.10 环境',flush=True)
    runtime=ROOT/'engines/runtime'
    py=runtime/'Scripts/python.exe'
    if not py.exists():
        run(uv_exe,'python','install','3.10')
        run(uv_exe,'venv','--python','3.10',runtime)
    print('安装 GPU 运行库（数 GB，首次下载较久）',flush=True)
    run(uv_exe,'pip','install','--python',py,'torch==2.8.0','torchaudio==2.8.0','--index-url','https://download.pytorch.org/whl/cu128')
    # Windows wheels avoid requiring a system-wide C++ compiler. These expose
    # the same Python APIs used by the upstream text front end.
    requirements=(engine/'requirements.txt').read_text(encoding='utf-8').splitlines()
    requirements=[line for line in requirements if not line.startswith(('--no-binary','jieba_fast','pyopenjtalk','opencc','onnxruntime','gradio','av'))]
    requirements += ['pyopenjtalk-plus','opencc-python-reimplemented','onnxruntime','gradio==4.44.1','gradio-client==1.3.0','av<17','resampy==0.4.3']
    local_requirements=ROOT/'.demo_cache/requirements-voice-windows.txt'
    local_requirements.write_text('\n'.join(requirements),encoding='utf-8')
    run(uv_exe,'pip','install','--python',py,'-r',local_requirements,'faster-whisper')
    compatibility=engine/'jieba_fast'; compatibility.mkdir(exist_ok=True)
    (compatibility/'__init__.py').write_text('from jieba import *\n',encoding='utf-8')
    (compatibility/'posseg.py').write_text('from jieba.posseg import *\n',encoding='utf-8')
    print('下载声学、语义和中文文本模型',flush=True)
    pretrained=engine/'GPT_SoVITS/pretrained_models'
    snapshot_download('lj1995/GPT-SoVITS',local_dir=str(pretrained),allow_patterns=[
        'gsv-v2final-pretrained/*','chinese-roberta-wwm-ext-large/*','chinese-hubert-base/*'])
    language_model=pretrained/'fast_langdetect/lid.176.bin'
    if not language_model.is_file():
        print('下载 fastText 官方语言检测模型',flush=True)
        language_model.parent.mkdir(parents=True,exist_ok=True)
        partial=language_model.with_suffix('.part')
        with requests.get('https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.bin',stream=True,timeout=(20,90)) as response:
            response.raise_for_status()
            with partial.open('wb') as out:
                for chunk in response.iter_content(1024*1024): out.write(chunk)
        partial.replace(language_model)
    import imageio_ffmpeg
    tools=ROOT/'engines/tools'; tools.mkdir(parents=True,exist_ok=True)
    shutil.copy2(imageio_ffmpeg.get_ffmpeg_exe(),tools/'ffmpeg.exe')
    portable=engine/'runtime'; portable.mkdir(exist_ok=True)
    shutil.copy2(imageio_ffmpeg.get_ffmpeg_exe(),portable/'ffmpeg.exe')
    print('准备中文多音字模型',flush=True)
    subprocess.run([str(py),'GPT_SoVITS/download.py'],cwd=engine,check=True)
    print('检查 GPU 和语音依赖',flush=True)
    run(py,'-c','import torch,librosa,transformers,resampy; import numpy as np; librosa.resample(np.zeros(48000,dtype=np.float32),orig_sr=48000,target_sr=16000,res_type="kaiser_fast"); print(torch.__version__, torch.cuda.is_available()); assert torch.cuda.is_available(), "GPU unavailable"')
    print('本地录音转写和训练引擎已就绪',flush=True)


if __name__=='__main__':
    try:
        main()
    except Exception as exc:
        print('安装未完成：'+str(exc),flush=True)
        sys.exit(1)
