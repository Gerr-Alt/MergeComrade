import unittest

from Bot.MergeDispatcher import JSONConfigLoader


class JSONConfigLoaderTest(unittest.TestCase):
    def test_shouldParseCorrectJSON(self):
        json = '{"branches": ["branch1", "branch2"]}'
        config = JSONConfigLoader.parse_json(json)
        self.assertCountEqual(config.get_branches(), ["branch1", "branch2"])

    def test_shouldReturnNoneIfNoBranchesInJSON(self):
        json = '{}'
        config = JSONConfigLoader.parse_json(json)
        self.assertIsNone(config)

    def test_shouldReturnNoneIfJSONMalformed(self):
        json = 'Not a JSON hohoho'
        config = JSONConfigLoader.parse_json(json)
        self.assertIsNone(config)
