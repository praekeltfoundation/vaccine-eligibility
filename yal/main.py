import logging
from urllib.parse import ParseResult, urlunparse

import aiohttp

from vaccine.base_application import BaseApplication
from vaccine.states import EndState
from vaccine.utils import HTTP_EXCEPTIONS, normalise_phonenumber
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


class Application(BaseApplication):
    START_STATE = "state_start"

    @staticmethod
    def turn_profile_url(whatsapp_id):
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

    async def state_start(self):
        msisdn = normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.lstrip(" + ")
        prototype_user = False

        async with get_turn_api() as session:
            for i in range(3):
                try:
                    response = await session.get(self.turn_profile_url(whatsapp_id))
                    response.raise_for_status()
                    response_body = await response.json()

                    if response_body["fields"].get("prototype_user"):
                        prototype_user = True

                    break
                except HTTP_EXCEPTIONS as e:
                    if i == 2:
                        logger.exception(e)
                        return await self.go_to_state("state_error")
                    else:
                        continue

        if not prototype_user:
            return await self.go_to_state("state_coming_soon")

        if self.inbound.content == "hi":
            return await self.go_to_state("state_welcome")

        return await self.go_to_state("state_catch_all")

    async def state_welcome(self):
        return EndState(
            self,
            self._("TODO: welcome"),
            next=self.START_STATE,
        )

    async def state_coming_soon(self):
        return EndState(
            self,
            self._("TODO: coming soon"),
            next=self.START_STATE,
        )

    async def state_catch_all(self):
        return EndState(
            self,
            self._("TODO: Catch all temp flow"),
            next=self.START_STATE,
        )
