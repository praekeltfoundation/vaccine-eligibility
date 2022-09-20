import logging
from urllib.parse import ParseResult, urlunparse

import aiohttp

from vaccine.utils import HTTP_EXCEPTIONS
from yal import config

logger = logging.getLogger(__name__)


def get_turn_api():
    # TODO: Cache the session globally. Things that don't work:
    # - Declaring the session at the top of the file
    #   You get a `Timeout context manager should be used inside a task` error
    # - Declaring it here but caching it in a global variable for reuse
    #   You get a `Event loop is closed` error
    return aiohttp.ClientSession(
        timeout=aiohttp.ClientTimeout(total=5),
        headers={
            "Content-Type": "application/json",
            "Accept": "application/vnd.v1+json",
            "User-Agent": "yal-whatsapp-bot",
            "Authorization": f"Bearer {config.API_TOKEN}",
        },
    )


def get_turn_url(path: str) -> str:
    return urlunparse(
        ParseResult(
            scheme="https",
            netloc=config.API_HOST or "",
            path=path,
            params="",
            query="",
            fragment="",
        )
    )


async def label_message(message_id, label):
    async with get_turn_api() as session:
        for i in range(3):
            try:
                response = await session.post(
                    url=get_turn_url(f"v1/messages/{message_id}/labels"),
                    json={"labels": [label]},
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
