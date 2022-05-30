import logging
from urllib.parse import urljoin

from vaccine.utils import HTTP_EXCEPTIONS
from yal import config, utils

logger = logging.getLogger(__name__)


async def get_profile(whatsapp_id):
    fields = {}
    async with utils.get_turn_api() as session:
        for i in range(3):
            try:
                response = await session.get(
                    urljoin(config.API_HOST, f"/v1/contacts/{whatsapp_id}/profile")
                )
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
                response = await session.patch(
                    urljoin(config.API_HOST, f"/v1/contacts/{whatsapp_id}/profile")
                )
                response.raise_for_status()
                break
            except HTTP_EXCEPTIONS as e:
                if i == 2:
                    logger.exception(e)
                    return True
                else:
                    continue

    return False
