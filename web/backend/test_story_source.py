import json, os, tempfile, threading, time, unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from story_source import StorySource

CHAPTER="obt/main/level_main_00-01_beg"
STORY='[name="阿米娅"] 博士，准备好了吗？'.encode()
CATALOG=json.dumps({"main_0":{"infoUnlockDatas":[{"storyTxt":CHAPTER}]} }).encode()

class StorySourceTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
 def tearDown(self):self.temp.cleanup()
 def test_persisted_cache_survives_restart_and_network_failure(self):
  first=StorySource(self.root,fetcher=lambda *_:STORY)
  self.assertFalse(first.get(CHAPTER)["cached"])
  def offline(*_):raise AssertionError("Cached chapter must not require the network")
  second=StorySource(self.root,fetcher=offline)
  self.assertEqual(second.get(CHAPTER)["data"],STORY.decode())
  self.assertTrue(second.get(CHAPTER)["cached"])
 def test_second_source_used_when_primary_fails(self):
  calls=[]
  def fetch(url,_):
   calls.append(url)
   if len(calls)==1:raise TimeoutError()
   return STORY
  self.assertEqual(StorySource(self.root,fetcher=fetch).get(CHAPTER)["data"],STORY.decode())
  self.assertEqual(len(calls),2);self.assertIn("cdn.jsdelivr.net",calls[1])
 def test_invalid_html_response_is_not_cached(self):
  def bad(*_):return b'<!doctype html><html>Unavailable</html>'
  with self.assertRaises(RuntimeError):StorySource(self.root,fetcher=bad).get(CHAPTER)
  self.assertFalse(list(self.root.iterdir()))
 def test_stale_cache_is_served_while_background_refresh_is_offline(self):
  store=StorySource(self.root,fetcher=lambda *_:STORY)
  store.get(CHAPTER)
  for target in self.root.iterdir():os.utime(target,(0,0))
  finished=threading.Event()
  def offline(*_):finished.set();raise TimeoutError()
  store.fetcher=offline
  result=store.get(CHAPTER)
  self.assertTrue(result["stale"]);self.assertEqual(result["data"],STORY.decode())
  self.assertTrue(finished.wait(2))
  for _ in range(100):
   if not store.refreshing:break
   time.sleep(.01)
  self.assertEqual(store.get(CHAPTER)["data"],STORY.decode())
 def test_concurrent_requests_fetch_only_once(self):
  calls=[]
  def fetch(*_):calls.append(1);time.sleep(.02);return STORY
  store=StorySource(self.root,fetcher=fetch)
  with ThreadPoolExecutor(max_workers=6) as pool:results=list(pool.map(lambda _:store.get(CHAPTER),range(6)))
  self.assertEqual(len(calls),1);self.assertTrue(all(r["data"]==STORY.decode() for r in results))
 def test_invalid_ids_never_reach_network_or_filesystem(self):
  def unused(*_):raise AssertionError("Must reject before downloading")
  store=StorySource(self.root,fetcher=unused)
  for ident in ["", "../secret", "/absolute", "https://example.com", "a?b", "x"*181]:
   with self.assertRaises(ValueError):store.get(ident)
  self.assertFalse(list(self.root.iterdir()))
 def test_catalog_is_validated_and_cached(self):
  store=StorySource(self.root,fetcher=lambda *_:CATALOG)
  self.assertIn("main_0",store.get()["data"])
  self.assertTrue(store.get()["cached"])

if __name__=="__main__":unittest.main()
