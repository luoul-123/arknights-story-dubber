import tempfile,unittest
from pathlib import Path
from reader_voice import folder_for,load_profile,save_profile,public_profile,publish,reference_for

class ReaderVoiceTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
  save_profile(self.root,'alice',{'draft':{'path':'sample.wav','duration':5,'text':'录音原话'}})
 def tearDown(self):self.temp.cleanup()
 def test_reader_profiles_are_isolated_and_hide_paths(self):
  alice=publish(self.root,'alice','录音原话')
  self.assertIsNone(public_profile(self.root,'bob')['voice'])
  self.assertNotIn('path',str(alice))
  with self.assertRaises(ValueError):reference_for(self.root,'bob',alice['voice']['version'])
 def test_unconfirmed_upload_does_not_change_active_voice(self):
  old=publish(self.root,'alice','原来的录音')['voice'];profile=load_profile(self.root,'alice')
  profile['draft']={'path':'new.wav','text':'新的录音','duration':5};save_profile(self.root,'alice',profile)
  self.assertEqual(reference_for(self.root,'alice',old['version'])['path'],'sample.wav')
  new=publish(self.root,'alice','新的录音')['voice'];self.assertNotEqual(new['version'],old['version'])
  with self.assertRaises(ValueError):reference_for(self.root,'alice',old['version'])
 def test_owner_and_transcript_required(self):
  with self.assertRaises(ValueError):folder_for(self.root,'')
  with self.assertRaises(ValueError):publish(self.root,'alice',' ')
  with self.assertRaises(ValueError):publish(self.root,'bob','没有录音')
  self.assertEqual(folder_for(self.root,'../../outside').parent,self.root/'readers')
if __name__=='__main__':unittest.main()
