import logging
from urllib.parse import ParseResult, urlunparse

from vaccine.utils import HTTP_EXCEPTIONS
from yal import config, utils

logger = logging.getLogger(__name__)


def get_profile_url(whatsapp_id):
    return urlunparse(
        ParseResult(
            scheme="https",
            netloc=config.API_HOST or "",
            path=f"/v1/contacts/{whatsapp_id}/profile",
            params="",
            query="",
            fragment="",
        )
    )


async def get_profile(whatsapp_id):
    fields = {}
    async with utils.get_turn_api() as session:
        for i in range(3):
            try:
                response = await session.get(get_profile_url(whatsapp_id))
                response.raise_for_status()
                response_body = await response.json()

                fields = response_body["fields"]
                break
            except HTTP_EXCEPTIONS as e:
                if i == 2:
                    logger.exception(e)
                    return True, fields
                else:
                    continue

    return False, fields


async def update_profile(whatsapp_id, data):
    async with utils.get_turn_api() as session:
        for i in range(3):
            try:
                response = await session.patch(get_profile_url(whatsapp_id))
                response.raise_for_status()
                break
            except HTTP_EXCEPTIONS as e:
                if i == 2:
                    logger.exception(e)
                    return True
                else:
                    continue

    return False
