from urllib.parse import urljoin

import aiohttp
from aiohttp_client_cache import CacheBackend, CachedSession
from fuzzywuzzy import process

from vaccine import vacreg_config as config


class MedicalAids:
    def __init__(self):
        self.cache_backend = CacheBackend(cache_control=True)

    async def data(self):
        async with CachedSession(cache=self.cache_backend) as session:
            url = urljoin(
                config.EVDS_URL,
                f"/api/private/{config.EVDS_DATASET}/person/{config.EVDS_VERSION}/"
                "lookup/medscheme/1",
            )
            response = await session.get(
                url,
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

    async def schemes(self):
        return {i["value"]: i["text"] for i in await self.data()}

    async def search_for_scheme(self, search_text):
        schemes = await self.schemes()
        possibilities = process.extract(search_text, schemes, limit=3)
        return [(id, value) for value, _, id in possibilities]

    async def scheme_name(self, scheme_id):
        schemes = await self.schemes()
        return schemes[scheme_id]


medical_aids = MedicalAids()
