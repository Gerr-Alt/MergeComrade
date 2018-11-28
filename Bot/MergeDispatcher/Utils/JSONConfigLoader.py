import json
from json import JSONDecodeError

from Bot.MergeDispatcher import Config


class JSONConfigLoader:
    JSON_BRANCHES_KEY = "branches"

    @staticmethod
    def parse_json(json_data):
        try:
            json_object = json.loads(json_data)
        except JSONDecodeError:
            return None

        if JSONConfigLoader.JSON_BRANCHES_KEY in json_object:
            branches = json_object[JSONConfigLoader.JSON_BRANCHES_KEY]
            return Config(branches)
        else:
            return None
