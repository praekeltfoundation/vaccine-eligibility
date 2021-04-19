import difflib
import gzip
import json
from functools import cached_property
from operator import itemgetter


class MedicalAids:
    @cached_property
    def data(self):
        # TODO: Get and cache this from the API
        with gzip.open("vaccine/data/medscheme.json.gz", "r") as f:
            data = json.load(f)
        return data["data"]["items"]

    @cached_property
    def schemes(self):
        schemes = [(i["value"], i["text"]) for i in self.data]
        schemes.sort(key=itemgetter(1))
        return schemes

    def search_for_scheme(self, search_text):
        search_text = search_text.strip().lower()
        schemes = {v.strip().lower(): k for k, v in self.schemes}
        possibilities = difflib.get_close_matches(search_text, schemes.keys(), n=3)
        return [(schemes[p], self.scheme_name(schemes[p])) for p in possibilities]

    def scheme_name(self, scheme_id):
        schemes = {k: v for k, v in self.schemes}
        return schemes[scheme_id]


medical_aids = MedicalAids()
