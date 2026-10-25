import unittest

from story_matcher import StoryMatcher, parse_script


class StoryMatcherTests(unittest.TestCase):
    def test_identity_revealed_later_resolves_earlier_alias(self):
        script = '''
[charslot(slot="m",name="avg_amiya_1#1$1",focus="m")]
[name="红衣少女"]我们先从这里出发。
[charslot(slot="m",name="avg_amiya_1#2$1",focus="m")]
[name="阿米娅"]我是阿米娅。
'''
        matcher = StoryMatcher(parse_script(script), {"阿米娅"})
        result = matcher.locate("我们先从这里出发")
        self.assertIsNotNone(result)
        self.assertEqual(result[1], "阿米娅")

    def test_shared_generic_sprite_does_not_guess(self):
        script = '''
[charslot(slot="m",name="avg_npc_1#1$1",focus="m")]
[name="甲"]这条路向左走。
[name="乙"]那条路向右走。
[name="神秘人"]请继续前进。
'''
        matcher = StoryMatcher(parse_script(script), {"甲", "乙"})
        result = matcher.locate("请继续前进")
        self.assertIsNotNone(result)
        self.assertIsNone(result[1])


if __name__ == "__main__":
    unittest.main()
