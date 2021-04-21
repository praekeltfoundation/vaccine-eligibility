import gzip
import json
from functools import cached_property
from fuzzywuzzy import process


class MedicalAids:
    @cached_property
    def data(self):
        # TODO: Get and cache this from the API
        with gzip.open("vaccine/data/medscheme.json.gz", "r") as f:
            data = json.load(f)
        return data["data"]["items"]

    @cached_property
    def schemes(self):
        return {k: v for k, v in self.data}

    def search_for_scheme(self, search_text):
        possibilities = process.extract(search_text, self.data, limit=3)
        return [(p['value'], p['text']) for p, _ in possibilities]

    def scheme_name(self, scheme_id):
        return self.schemes[scheme_id]


medical_aids = MedicalAids()
