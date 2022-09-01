import logging
from urllib.parse import urljoin

import aiohttp
import sentry_sdk

from vaccine.utils import HTTP_EXCEPTIONS
from yal import config

logger = logging.getLogger(__name__)


def get_aaq_api():
    return aiohttp.ClientSession(
        timeout=aiohttp.ClientTimeout(total=5),
        headers={
            "Authorization": f"BEARER {config.AAQ_TOKEN}",
            "Content-Type": "application/json",
        },
    )


async def inbound_check(user, message_id, question):
    data = {
        "text_to_match": question,
        "metadata": {
            "whatsapp_id": user.addr,
            "message_id": message_id,
            "session_id": user.session_id,
        },
    }

    async with get_aaq_api() as session:
        for i in range(3):
            try:
                response = await session.post(
                    url=urljoin(config.AAQ_URL, "/inbound/check"),
                    json=data,
                )
                response_data = await response.json()
                sentry_sdk.set_context(
                    "model", {"request_data": data, "response_data": response_data}
                )
                response.raise_for_status()

                break
            except HTTP_EXCEPTIONS as e:
                if i == 2:
                    logger.exception(e)
                    return True, {}
                else:
                    continue

    answers = {}
    for title, body in response_data["top_responses"]:
        answers[title] = body

    return False, {
        "model_answers": answers,
        "next_page_url": response_data.get("next_page_url"),
        "prev_page_url": response_data.get("prev_page_url"),
    }


async def get_page(url):
    async with get_aaq_api() as session:
        for i in range(3):
            try:
                response = await session.get(url=urljoin(config.AAQ_URL, url))
                response_data = await response.json()
                sentry_sdk.set_context("model", {"response_data": response_data})
                response.raise_for_status()
                break
            except HTTP_EXCEPTIONS as e:
                if i == 2:
                    logger.exception(e)
                    return True, {}
                else:
                    continue

    answers = {}
    for title, body in response_data["top_responses"]:
        answers[title] = body

    return False, {
        "model_answers": answers,
        "next_page_url": response_data.get("next_page_url"),
        "prev_page_url": response_data.get("prev_page_url"),
    }
