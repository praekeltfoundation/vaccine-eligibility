from operator import itemgetter
from urllib.parse import urljoin

import aiohttp
from aiohttp_client_cache import CacheBackend, CachedSession
from fuzzywuzzy import process

from vaccine import vacreg_config as config


class Suburbs:
    def __init__(self):
        self.cache_backend = CacheBackend(cache_control=True)

    async def data(self):
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
            return (await response.json())["data"]["items"]

    async def provinces(self):
        provinces = [(i["value"], i["text"]) for i in await self.data()]
        provinces.sort(key=itemgetter(1))
        return provinces

    async def suburbs_for_province(self, province_id):
        for province in await self.data():
            if province["value"] == province_id:
                break

        suburbs = {}
        for municipality in province["children"]:
            for city in municipality["children"]:
                for suburb in city["children"]:
                    suburbs[suburb["value"]] = f"{suburb['text']}, {city['text']}"
        return suburbs

    async def search_for_suburbs(self, province_id, search_text):
        suburbs = await self.suburbs_for_province(province_id)
        possibilities = process.extract(search_text, suburbs, limit=3)
        return [(id, value) for value, _, id in possibilities]

    async def suburb_name(self, suburb_id, province_id):
        for province in await self.data():
            if province["value"] == province_id:
                break
        for municipality in province["children"]:
            for city in municipality["children"]:
                for suburb in city["children"]:
                    if suburb["value"] == suburb_id:
                        return suburb["text"]


suburbs = Suburbs()
