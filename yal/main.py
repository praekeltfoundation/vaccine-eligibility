import logging
from urllib.parse import ParseResult, urlunparse

from vaccine.states import EndState
from vaccine.utils import HTTP_EXCEPTIONS, normalise_phonenumber
from yal import config, utils
from yal.mainmenu import Application as MainMenuApplication
from yal.onboarding import Application as OnboardingApplication
from yal.terms_and_conditions import Application as TermsApplication

logger = logging.getLogger(__name__)

GREETING_KEYWORDS = {"hi", "hello"}


class Application(TermsApplication, OnboardingApplication, MainMenuApplication):
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

        async with utils.get_turn_api() as session:
            for i in range(3):
                try:
                    response = await session.get(self.turn_profile_url(whatsapp_id))
                    response.raise_for_status()
                    response_body = await response.json()

                    fields = response_body["fields"]
                    prototype_user = fields.get("prototype_user")
                    terms_accepted = fields.get("terms_accepted")
                    onboarding_completed = fields.get("onboarding_completed")

                    break
                except HTTP_EXCEPTIONS as e:
                    if i == 2:
                        logger.exception(e)
                        return await self.go_to_state("state_error")
                    else:
                        continue

        if not prototype_user:
            return await self.go_to_state("state_coming_soon")

        inbound = utils.clean_inbound(self.inbound.content or "")

        if inbound in GREETING_KEYWORDS:
            if terms_accepted and onboarding_completed:
                return await self.go_to_state(MainMenuApplication.START_STATE)
            elif terms_accepted:
                return await self.go_to_state(OnboardingApplication.START_STATE)
            else:
                return await self.go_to_state(TermsApplication.START_STATE)

        return await self.go_to_state("state_catch_all")

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
