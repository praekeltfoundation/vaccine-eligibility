import difflib
import gzip
import json
from functools import cache, cached_property


class Suburbs:
    @cached_property
    def data(self):
        # TODO: Get and cache this from the API
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
                    suburbs[suburb["value"]] = suburb["text"]
        lowercase = {v.strip().lower(): k for k, v in suburbs.items()}
        return suburbs, lowercase

    def search_for_suburbs(self, province_id, search_text):
        search_text = search_text.strip().lower()
        suburbs, lowercase = self.suburbs_for_province(province_id)
        possibilities = difflib.get_close_matches(search_text, lowercase.keys(), n=3)
        return [(lowercase[p], suburbs[lowercase[p]]) for p in possibilities]

    def suburb_name(self, suburb_id, province_id):
        suburbs, _ = self.suburbs_for_province(province_id)
        return suburbs[suburb_id]


suburbs = Suburbs()
