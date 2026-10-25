import tempfile
import unittest
import wave
from pathlib import Path
from unittest.mock import Mock
import numpy as np
from PIL import Image
from dialogue import parse_dialogue
from recognition import Reading, StableDialogue
from audio_studio import slice_recording
from speech_engine import SpeechEngine
from streaming_dialogue import IncrementalDialogue
from training import training_clips

ROOT=Path(__file__).resolve().parent


class RuntimeTests(unittest.TestCase):
    def test_streaming_reads_prefix_before_full_line(self):
        gate=IncrementalDialogue()
        def frame(text,speaker='阿米娅'): return Reading(speaker,text,Image.new('RGB',(1,1)),1,.99,[])
        self.assertEqual(gate.observe(frame('博士，准备好了吗？'),0),(False,[]))
        self.assertEqual(gate.observe(frame('博士，准备好了吗？我们出'),.2),(False,['博士，准备好了吗？']))
        self.assertEqual(gate.observe(frame('博士，准备好了吗？我们出发吧。'),.4),(False,[]))
        self.assertEqual(gate.observe(frame('博士，准备好了吗？我们出发吧。'),.6),(False,['我们出发吧。']))
        self.assertEqual(gate.observe(frame('博士，准备好了吗？我们出发吧。'),1.5),(False,[]))
        self.assertEqual(gate.observe(frame('这里发生了什么？','凯尔希'),1.7),(True,[]))
        self.assertEqual(gate.observe(frame('这里发生了什么？','凯尔希'),1.9),(False,['这里发生了什么？']))

    def test_streaming_tail_and_ocr_flicker(self):
        gate=IncrementalDialogue()
        def frame(text): return Reading('旁白',text,Image.new('RGB',(1,1)),1,.99,[])
        gate.observe(frame('她慢慢地'),0)
        self.assertEqual(gate.observe(frame('她慢慢地走向前方'),.2)[1],[])
        self.assertEqual(gate.observe(frame('她慢慢地走向前方'),.8)[1],['她慢慢地走向前方'])
        self.assertEqual(gate.observe(frame('她慢慢地走向前方。'),1)[1],[])
        self.assertEqual(gate.observe(frame(''),1.1),(False,[]))
        self.assertEqual(gate.observe(frame('她慢慢地走向前方。'),1.2)[1],[])

    def test_30_seconds_threshold_excludes_bad_samples(self):
        path=str(Path(__file__).resolve())
        profile={'clips':[dict(path=path,text='有效录音',duration=15),dict(path=path,text='另一段录音',duration=15)]}
        self.assertEqual(len(training_clips(profile)),2)
        profile['clips'][1]['clipped']=True
        with self.assertRaisesRegex(ValueError,'还差 15.0 秒'): training_clips(profile)
        profile['clips'][1]['clipped']=False; profile['clips'][1]['text']=' '
        with self.assertRaises(ValueError): training_clips(profile)

    def test_multiline_and_controls(self):
        lines=[dict(text='自动 OFF',x=900,y=40),dict(text='跳过，',x=1000,y=40),
            dict(text='维娜相信同样的变',x=300,y=400),dict(text='化也能在自己身上看见。',x=300,y=434)]
        self.assertEqual(parse_dialogue(lines),('旁白 / 未识别','维娜相信同样的变化也能在自己身上看见。'))
        self.assertEqual(parse_dialogue(lines[:2]),('旁白 / 未识别',''))

    def test_typewriter_and_repeat_suppression(self):
        gate=StableDialogue()
        def frame(text): return Reading('阿米娅',text,Image.new('RGB',(1,1)),1,1,[])
        self.assertFalse(gate.observe(frame('博士'),0))
        self.assertFalse(gate.observe(frame('博士，准备好了吗？'),.3))
        self.assertFalse(gate.observe(frame('博士，准备好了吗？'),.4))
        self.assertTrue(gate.observe(frame('博士，准备好了吗？'),.6))
        self.assertFalse(gate.observe(frame('博士准备好了吗！'),.9))
        self.assertFalse(gate.observe(frame(''),1))
        self.assertFalse(gate.observe(frame('博士，准备好了吗？'),1.3))
        self.assertFalse(gate.observe(frame('博士，准备好了吗？'),1.6))

    def test_audio_silence_and_segmentation(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'.demo_cache') as directory:
            root=Path(directory).resolve()
            self.assertTrue(root.is_relative_to((ROOT/'.demo_cache').resolve()))
            rate=16000
            tone=(np.sin(np.arange(rate*4)*2*np.pi*220/rate)*.12).astype(np.float32)
            samples=np.concatenate([np.zeros(rate),tone,np.zeros(rate),tone,np.zeros(rate)])
            path=root/'source.wav'
            with wave.open(str(path),'wb') as out:
                out.setnchannels(1);out.setsampwidth(2);out.setframerate(rate)
                out.writeframes((samples*32767).astype('<i2').tobytes())
            clips=slice_recording(path,root/'clips')
            self.assertEqual(len(clips),2)
            self.assertTrue(all(3.9<c['duration']<4.5 for c in clips))

    def test_low_confidence_does_not_autoplay(self):
        gate=StableDialogue()
        frame=Reading('角色','一段不确定的文字',Image.new('RGB',(1,1)),1,.3,[])
        self.assertFalse(gate.observe(frame,0))
        self.assertFalse(gate.observe(frame,2))


if __name__=='__main__': unittest.main()
