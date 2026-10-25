"""Run screenshot regressions and measure warmed services, without playing sound."""
import argparse
import json
import time
from pathlib import Path
from PIL import Image
from recognition import Recognizer
from speech_engine import SpeechEngine

ROOT=Path(__file__).resolve().parent
CASES=[
    ('旁白 / 未识别','维娜时常感到因陀罗、摩根和达格达有些变了。她相信同样的变化也能在自己身上看见。'),
    ('戴菲恩','卧倒！'),
    ('稳重的男声','他能在狂风中指出方向'),
]


def main():
    parser=argparse.ArgumentParser(description='使用三张本地截图验证 OCR 与系统配音')
    parser.add_argument('images',nargs=3,type=Path,metavar='IMAGE',help='依次提供旁白、短台词和角色标签截图')
    args=parser.parse_args()
    for path in args.images:
        if not path.is_file(): parser.error(f'找不到截图：{path}')
    recognizer=Recognizer(); speech=SpeechEngine(); report={'screenshots':[]}
    try:
        recognizer.warmup(); speech.warmup()
        for path,(speaker,expected) in zip(args.images,CASES):
            key=str(path.resolve())
            image=Image.open(path).convert('RGB')
            reading=recognizer.scan(image,key)
            assert reading.speaker==speaker,(reading.speaker,speaker)
            assert reading.text.startswith(expected),(reading.text,expected)
            report['screenshots'].append({'speaker':speaker,'text':reading.text,'ocr_ms':reading.elapsed_ms})
            cached=recognizer.scan(image,key)
            assert cached.cached
        _,_,elapsed=speech.synthesize(f'欢迎回来，博士。今天的旅程即将开始。{int(time.time())%100}')
        report['system_tts_ms']=elapsed
        report['old_ocr_ms']=1695; report['old_system_tts_ms']=916
        target=ROOT/'.demo_cache/verification.json'
        target.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps(report,ensure_ascii=False))
    finally:
        recognizer.close();speech.close()


if __name__=='__main__':main()
