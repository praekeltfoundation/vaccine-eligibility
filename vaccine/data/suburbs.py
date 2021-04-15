from functools import cached_property
import json
import gzip


class Suburbs:
    @cached_property
    def data(self):
        with gzip.open("vaccine/data/suburbs.json.gz", "r") as f:
            data = json.load(f)
        return data["data"]["items"]

    @cached_property
    def provinces(self):
        return [(i["value"], i["text"]) for i in self.data]


suburbs = Suburbs()
