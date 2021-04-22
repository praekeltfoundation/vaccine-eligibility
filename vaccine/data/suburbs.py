from dataclasses import dataclass
from operator import itemgetter
from urllib.parse import urljoin

import aiohttp
from aiohttp_client_cache import CacheBackend, CachedSession
from fuzzywuzzy import process

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
                    suburbs[suburb["value"]] = Suburb(
                        suburb["text"],
                        city["text"],
                        municipality["value"],
                        municipality["text"],
                    )
        return suburbs

    async def whatsapp_search(self, province_id, search_text):
        """
        WhatsApp displays and searches name, city, and municipality
        """
        suburbs = await self.suburbs_for_province(province_id)
        suburbs_search = {
            k: f"{v.name}, {v.city}, {v.municipality}" for k, v in suburbs.items()
        }
        possibilities = process.extract(search_text, suburbs_search, limit=3)
        return [(id, value) for value, _, id in possibilities]

    async def ussd_search(self, province_id, search_text, municipality_id=None):
        """
        USSD displays name and city, and if there are too many close matches, we confirm
        municipality first
        """
        suburbs = await self.suburbs_for_province(province_id)
        if municipality_id is not None:
            suburbs_search = {
                k: f"{v.name}, {v.city}"
                for k, v in suburbs.items()
                if v.municipality_id == municipality_id
            }
        else:
            suburbs_search = {k: f"{v.name}, {v.city}" for k, v in suburbs.items()}
        possibilities = process.extract(search_text, suburbs_search, limit=5)
        possibilities = [
            (id, value) for value, score, id in possibilities if score >= 80
        ]
        if municipality_id is not None:
            return (
                False,
                [
                    p
                    for p in possibilities
                    if suburbs[p[0]].municipality_id == municipality_id
                ][:3],
            )
        elif len(possibilities) > 3:
            return (
                True,
                {
                    suburbs[id].municipality_id: suburbs[id].municipality
                    for id, _ in possibilities
                },
            )
        else:
            return (False, possibilities)

    async def suburb_name(self, suburb_id, province_id):
        suburbs = await self.suburbs_for_province(province_id)
        return suburbs[suburb_id].name


suburbs = Suburbs()
