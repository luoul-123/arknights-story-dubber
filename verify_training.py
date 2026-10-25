"""Integration smoke test with generated system speech, never user game recordings."""
import json
import argparse
import threading
import wave
from pathlib import Path
from speech_engine import SpeechEngine
from training import TrainingJob, Transcriber

ROOT=Path(__file__).resolve().parent
WORK=ROOT/'.demo_cache/training_smoke'


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--quick',action='store_true'); args=parser.parse_args()
    WORK.mkdir(parents=True,exist_ok=True)
    synth=SpeechEngine();synth.warmup()
    clips=[]
    sentences=[
        '今天的阳光很好，我们可以沿着这条小路，慢慢走到山顶。',
        '请先检查设备是否准备妥当，确认之后，我们就可以出发了。',
        '远处传来了清脆的钟声，街道上的人们纷纷停下了脚步。',
        '如果明天没有下雨，我想带你看看这座城市最美的风景。',
        '故事还没有结束，让我们保持耐心，继续听下一段内容。',
        '她轻轻地推开窗户，看见一只小鸟落在了树梢上。',
        '这是一段用于检验语音训练流程的合成录音，只在本机测试使用。',
        '桌子上放着一本旧书，翻开第一页，就能看见熟悉的文字。',
        '我们约定在傍晚见面，到时候，请记得带上你的笔记本。',
        '听见这个消息之后，他终于露出了轻松的笑容。',
        '请把这段话读得清楚一些，大家都在认真地听着。',
        '风渐渐停了，天空也慢慢亮了起来，新的一天开始了。',
    ]
    try:
        for index,text in enumerate(sentences):
            path=WORK/f'test_{index:02d}.wav'
            synth.native.call('tts',text=text,voice=synth.voice,path=str(path))
            with wave.open(str(path),'rb') as w: duration=w.getnframes()/w.getframerate()
            clips.append(dict(path=str(path),text=text,duration=duration,clipped=False,id=path.stem))
    finally:synth.close()
    if args.quick:
        chosen=[]
        for clip in clips:
            chosen.append(clip)
            if sum(c['duration'] for c in chosen)>=30: break
        clips=chosen
    print('Synthetic seconds:',sum(c['duration'] for c in clips),flush=True)
    asr=Transcriber().run(clips[:1]); print('ASR:',asr[0]['text'],flush=True)
    job=TrainingJob()
    done=threading.Event()
    def messages():
        while not done.is_set() or not job.messages.empty():
            try:
                message,_=job.messages.get(timeout=.2)
                print(message,flush=True)
            except Exception:pass
    thread=threading.Thread(target=messages,daemon=True);thread.start()
    try:
        result=job.train({'clips':clips,'language':'zh'},WORK,epochs=2 if args.quick else 1)
        (WORK/'result.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
        print('TRAINING_VERIFIED',result,flush=True)
    finally:
        done.set();thread.join(timeout=2)


if __name__=='__main__':main()
