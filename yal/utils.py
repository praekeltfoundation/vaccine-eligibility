import re

import aiohttp

from yal import config


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


def clean_inbound(content):
    return re.sub(r"\W+", " ", content).strip().lower()
