import tempfile,unittest
from media_source import MediaSource
class MediaTests(unittest.TestCase):
 def test_exact_expression_and_legacy_folder(self):
  with tempfile.TemporaryDirectory() as folder:
   source=MediaSource(folder)
   self.assertIn('avg_180_amgoat_1#3$1.png',source.resource('portrait','avg_180_amgoat_1#3$1')[0])
   self.assertIn('char_002_amiya_1/char_002_amiya_10.png',source.resource('portrait','char_002_amiya_10')[0])
 def test_music_and_invalid_paths(self):
  with tempfile.TemporaryDirectory() as folder:
   source=MediaSource(folder)
   self.assertTrue(source.resource('music','$babel_loop')[0].endswith('m_dia_babel_loop.mp3'))
   for name in ('../../secret','https://example.com','missing_portrait'):
    with self.assertRaises(ValueError):source.resource('portrait',name)
