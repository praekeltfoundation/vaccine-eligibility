from dataclasses import dataclass
from functools import cache, lru_cache
from operator import itemgetter
from urllib.parse import urljoin

import aiohttp
from aiohttp_client_cache import CacheBackend, CachedSession
from rapidfuzz import process

from vaccine import vacreg_config as config


@dataclass
class Suburb:
    name: str
    city: str
    municipality_id: str
    municipality: str


class Suburbs:
    def __init__(self):
        self.cache_backend = CacheBackend(cache_control=True)

    async def fetch(self):
        async with CachedSession(cache=self.cache_backend) as session:
            url = urljoin(
                config.EVDS_URL,
                f"/api/private/{config.EVDS_DATASET}/person/{config.EVDS_VERSION}/"
                "lookup/location/1",
            )
            response = await session.get(
                url,
                params={"includeChildren": "true"},
                timeout=aiohttp.ClientTimeout(total=5),
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "User-Agent": "vaccine-registration",
                },
                auth=aiohttp.BasicAuth(config.EVDS_USERNAME, config.EVDS_PASSWORD),
            )
            response.raise_for_status()
            if not response.from_cache:
                self.data = (await response.json())["data"]["items"]
                self._provinces.cache_clear()
                self._suburbs_for_province.cache_clear()
                self._search.cache_clear()

    async def provinces(self):
        await self.fetch()
        return self._provinces()

    @cache
    def _provinces(self):
        provinces = [(i["value"], i["text"]) for i in self.data]
        provinces.sort(key=itemgetter(1))
        return provinces

    async def suburbs_for_province(self, province_id):
        await self.fetch()
        return self._suburbs_for_province(province_id)

    @cache
    def _suburbs_for_province(self, province_id):
        for province in self.data:
            if province["value"] == province_id:
                break

        suburbs = {}
        for municipality in province["children"]:
            for city in municipality["children"]:
                for suburb in city["children"]:
                    suburbs[suburb["value"]] = Suburb(
                        suburb["text"],
                        city["text"],
                        municipality["value"],
                        municipality["text"],
                    )
        return suburbs

    @staticmethod
    def _filter_duplicate_municipalities(municipalities):
        seen = set()
        deduped = []
        for id, name in municipalities:
            if id not in seen:
                seen.add(id)
                deduped.append((id, name))
        return deduped

    async def search(self, province_id, search_text, municipality_id=None, m_limit=3):
        """
        If there are too many close matches `m_limit`, we confirm municipality first
        """
        await self.fetch()
        return self._search(province_id, search_text, municipality_id, m_limit)

    # It might seem like it's unlikely that we'll have the same search term twice, but
    # we call this once when we generate the list of options for the user, and again
    # when we get the user's selection. This caching stops doing that expensive search
    # twice
    @lru_cache
    def _search(self, province_id, search_text, municipality_id=None, m_limit=3):
        suburbs = self._suburbs_for_province(province_id)
        if municipality_id is not None:
            suburbs_search = {
                k: f"{v.name}, {v.city}"
                for k, v in suburbs.items()
                if v.municipality_id == municipality_id
            }
        else:
            suburbs_search = {k: f"{v.name}, {v.city}" for k, v in suburbs.items()}
        possibilities = process.extract(
            search_text, suburbs_search, score_cutoff=70, limit=100
        )

        if municipality_id is None and len(possibilities) > m_limit:
            municipalities = [
                (suburbs[id].municipality_id, suburbs[id].municipality)
                for _, _, id in possibilities
            ]
            return (True, self._filter_duplicate_municipalities(municipalities))
        else:
            return (False, [(id, name) for name, _, id in possibilities])

    async def suburb_name(self, suburb_id, province_id):
        suburbs = await self.suburbs_for_province(province_id)
        return suburbs[suburb_id].name


suburbs = Suburbs()
