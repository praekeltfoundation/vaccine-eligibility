import difflib
import gzip
import json
from functools import cache, cached_property


class Suburbs:
    @cached_property
    def data(self):
        with gzip.open("vaccine/data/suburbs.json.gz", "r") as f:
            data = json.load(f)
        return data["data"]["items"]

    @cached_property
    def provinces(self):
        return [(i["value"], i["text"]) for i in self.data]

    @cache
    def suburbs_for_province(self, province_id):
        for province in self.data:
            if province["value"] == province_id:
                break

        suburbs = {}
        for municipality in province["children"]:
            for city in municipality["children"]:
                for suburb in city["children"]:
                    suburbs[suburb["text"]] = suburb["value"]
        return suburbs

    def search_for_suburbs(self, province_id, search_text):
        suburbs = self.suburbs_for_province(province_id)
        possibilities = difflib.get_close_matches(search_text, suburbs.keys(), n=3)
        return [(suburbs[p], p) for p in possibilities]


suburbs = Suburbs()
