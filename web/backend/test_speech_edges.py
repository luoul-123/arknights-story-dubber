import io,wave,unittest
from unittest.mock import patch
import server
class SpeechEdgeTests(unittest.TestCase):
 def test_punctuation_is_half_second_pause_without_engine(self):
  for text in ('……','？！','— —','...'):
   with patch.object(server,'default_speech',side_effect=AssertionError('engine called')):
    data=server.synthesize('__npc',text)
   with wave.open(io.BytesIO(data)) as sound:self.assertEqual(sound.getnframes()/sound.getframerate(),.5)
 def test_words_and_numbers_are_not_silenced(self):
  for text in ('12345','Hello, Doctor.','8:50AM 龙门'):
   with patch.object(server,'default_speech',return_value=b'audio') as speak:
    self.assertEqual(server.synthesize('__npc',text),b'audio');speak.assert_called_once()
