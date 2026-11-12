import tempfile,unittest
from pathlib import Path
from default_voices import gender_for,selected_default,save_defaults,read_defaults,defaults_version
from catalog_metadata import build_metadata

class DefaultVoiceTests(unittest.TestCase):
 def test_known_gender_and_explicit_npc_labels(self):
  self.assertEqual(gender_for("赫拉格",{"赫拉格":"male"}),"male")
  self.assertEqual(gender_for("女性"),"female");self.assertEqual(gender_for("男性"),"male")
  config={"female":"perlica","male":"endmin","narrator":None}
  self.assertEqual(selected_default(config,"男性"),"endmin")
  self.assertEqual(selected_default(config,"",narrator=True),"perlica")
 def test_unpublished_voice_cannot_be_assigned_as_default(self):
  with tempfile.TemporaryDirectory() as folder:
   with self.assertRaises(ValueError):save_defaults(Path(folder),{"v":{}},{"female":"v"})
   result=save_defaults(Path(folder),{"v":{"published":{"version":"a"}}},{"female":"v"})
   self.assertEqual(read_defaults(Path(folder)),result)
 def test_cache_version_changes_when_default_model_is_republished(self):
  config={"female":"v"};a=defaults_version(config,{"v":{"published":{"version":"a"}}});b=defaults_version(config,{"v":{"published":{"version":"b"}}})
  self.assertNotEqual(a,b)
 def test_personal_record_uses_its_own_release_time(self):
  book={"handbookDict":{"char_x":{"storyTextAudio":[{"stories":[{"storyText":"【性别】女"}]}],"handbookAvgList":[{"storySetId":"record","storyGetTime":1617091200}]}}}
  meta=build_metadata(book,{"char_x":{"name":"测试干员"}},{"mainlineAdditionInfo":{}})
  self.assertEqual(meta["personal"]["record"]["operator"],"测试干员");self.assertEqual(meta["personal"]["record"]["releasedAt"],1617091200);self.assertEqual(meta["genders"]["测试干员"],"female")
if __name__=="__main__":unittest.main()
