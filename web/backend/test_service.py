import importlib.util,io,json,os,tempfile,unittest,wave
from pathlib import Path
temp=tempfile.TemporaryDirectory()
os.environ["ZHOU_DATA_DIR"]=temp.name
spec=importlib.util.spec_from_file_location("voice_service",Path(__file__).with_name("server.py"))
server=importlib.util.module_from_spec(spec);spec.loader.exec_module(server)
class ServiceTests(unittest.TestCase):
 def setUp(self):server.save_store({})
 def make(self):
  c=server.create_character("阿米娅");return c["id"]
 def test_duplicate(self):
  self.make()
  with self.assertRaises(ValueError):self.make()
 def test_public_data_contains_no_sample_paths(self):
  ident=self.make();data=server.read_store();data[ident]["clips"]=[{"id":"clip","duration":4,"text":"你好","path":"/private/file.wav"}];server.save_store(data)
  self.assertNotIn("/private",json.dumps(server.public_character(data[ident])))
 def test_unpublished_voice_rejected(self):
  with self.assertRaisesRegex(ValueError,"未发布"):server.synthesize(self.make(),"测试","v")
 def test_publication_snapshots_reference(self):
  ident=self.make();data=server.read_store();folder=server.DATA/ident;folder.mkdir(exist_ok=True)
  for filename in ("gpt.ckpt","sovits.pth","clip.wav"):(folder/filename).write_bytes(b"fixture")
  c=data[ident];c["models"]={"gpt":str(folder/"gpt.ckpt"),"sovits":str(folder/"sovits.pth")};c["clips"]=[{"id":"c","duration":5,"text":"旧版本","path":str(folder/"clip.wav")}];server.save_store(data)
  version=server.publish(ident,"trained")["version"];data=server.read_store();data[ident]["clips"][0]["text"]="新版本";server.save_store(data)
  self.assertEqual(server.read_store()[ident]["published"]["reference"]["text"],"旧版本")
  with self.assertRaisesRegex(ValueError,"已更新"):server.synthesize(ident,"测试","obsolete")
 def test_training_requires_transcribed_samples(self):
  ident=self.make()
  with self.assertRaises(ValueError):server.queue_job("train",ident)
 def test_edit_lock(self):
  with self.assertRaises(ValueError):server.editable({"busy":"job"})
 def test_audio_upload_normalizes_and_splits(self):
  import numpy as np
  samples=(np.sin(np.arange(16000*12)*2*np.pi*220/16000)*3000).astype(np.int16)
  buffer=io.BytesIO()
  with wave.open(buffer,"wb") as audio:
   audio.setnchannels(1);audio.setsampwidth(2);audio.setframerate(16000);audio.writeframes(samples.tobytes())
  ident=self.make();result=server.ingest(ident,"sample.wav",buffer.getvalue())
  self.assertGreaterEqual(result["added"],2)
  for clip in server.read_store()[ident]["clips"]:
   with wave.open(clip["path"]) as audio:self.assertEqual(audio.getframerate(),32000)
 def test_empty_upload(self):
  with self.assertRaises(ValueError):server.ingest(self.make(),"empty.wav",b"")
 def test_length_limit(self):
  with self.assertRaises(ValueError):server.synthesize("any","x"*601)
if __name__=="__main__":unittest.main()
