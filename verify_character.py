"""Load smoke-test models and synthesize an unseen sentence without playback."""
import json
import wave
from pathlib import Path
from speech_engine import SpeechEngine

ROOT = Path(__file__).resolve().parent
WORK = ROOT / '.demo_cache/training_smoke'


def main():
    engine = SpeechEngine()
    try:
        engine.warmup()
        print(engine.start_server(), flush=True)
        models = json.loads((WORK/'result.json').read_text(encoding='utf-8'))
        reference = dict(path=str(WORK/'test_00.wav'), language='zh', models=models,
            text='今天的阳光很好，我们可以沿着这条小路，慢慢走到山顶。')
        # Ignore the audio cache so a repeated verification measures the engine.
        path, mode, milliseconds = engine.synthesize('这次测试已经完成，我们可以继续阅读新的故事了。', reference, use_cache=False)
        assert mode == '角色声线', (mode, engine.last_error)
        with wave.open(str(path), 'rb') as audio:
            duration = audio.getnframes()/audio.getframerate()
            assert duration > 1
        result = dict(path=str(path), mode=mode, milliseconds=milliseconds, seconds=duration)
        next_path, next_mode, warm_ms = engine.synthesize('风已经停了，远处的天空渐渐亮了起来。', reference, use_cache=False)
        assert next_mode == '角色声线', (next_mode, engine.last_error)
        result.update(warm_milliseconds=warm_ms, warm_path=str(next_path))
        (WORK/'synthesis.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
        print('SYNTHESIS_VERIFIED', result, flush=True)
    finally:
        engine.close()


if __name__ == '__main__':
    main()
