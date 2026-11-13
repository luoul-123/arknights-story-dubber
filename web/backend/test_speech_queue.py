import unittest
from speech_queue import register,check_current
class QueueTests(unittest.TestCase):
 def tearDown(self):register('','','0')
 def test_old_request_is_rejected_after_newer_request(self):
  register('u','tab',10);check_current();register('u','tab',11);check_current();register('u','tab',10)
  with self.assertRaises(ValueError):check_current()
 def test_independent_tabs_do_not_cancel_each_other(self):
  register('u','a',2);register('u','b',1);check_current();register('u','a',2);check_current()

 def test_waiting_request_sees_newer_sequence_from_another_thread(self):
  import threading
  ready=threading.Event();resume=threading.Event();result=[]
  def old_request():
   register('u','threaded',1);ready.set();resume.wait(2)
   try:check_current();result.append('ran')
   except ValueError:result.append('skipped')
  worker=threading.Thread(target=old_request);worker.start()
  self.assertTrue(ready.wait(2));register('u','threaded',2);check_current();resume.set();worker.join(2)
  self.assertEqual(result,['skipped'])
