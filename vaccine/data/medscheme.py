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
        lowercase = {v.strip().lower(): k for k, v in schemes}
        schemes_kv = {k: v for k, v in schemes}
        return lowercase, schemes_kv

    def search_for_scheme(self, search_text):
        search_text = search_text.strip().lower()
        lowercase, _ = self.schemes
        possibilities = difflib.get_close_matches(search_text, lowercase.keys(), n=3)
        return [(lowercase[p], self.scheme_name(lowercase[p])) for p in possibilities]

    def scheme_name(self, scheme_id):
        _, schemes_kv = self.schemes
        return schemes_kv[scheme_id]


medical_aids = MedicalAids()
