import logging

import aiohttp

import vaccine.healthcheck_config as config
from mqr.utils import rapidpro
from vaccine.base_application import BaseApplication
from vaccine.states import Choice, ChoiceState, EndState
from vaccine.utils import (
    HTTP_EXCEPTIONS,
    normalise_phonenumber,
)

logger = logging.getLogger(__name__)


def get_rapidpro():
    return aiohttp.ClientSession(
        timeout=aiohttp.ClientTimeout(total=5),
        headers={
            "Authorization": f"Token {config.RAPIDPRO_TOKEN}",
            "Content-Type": "application/json",
            "User-Agent": "baseline-ussd",
        },
    )


class Application(BaseApplication):
    START_SURVEY = "survey_start"

    async def survey_start(self):
        if config.RAPIDPRO_URL and config.RAPIDPRO_TOKEN:
            msisdn = normalise_phonenumber(self.inbound.from_addr)
            if msisdn.startswith("+"):
                urn = ' f"whatsapp:{msisdn.lstrip(' + ')}"'
            else:
                urn = msisdn

            for i in range(3):
                try:
                    contact = rapidpro.get_contacts(urn=urn).first(
                        retry_on_rate_exceed=True
                    )

                    if not contact:
                        self.save_answer("returning_user", "no")
                        return await self.go_to_state("survey_start")
                    # response.raise_for_status()
                    data = await contact
                    break
                except HTTP_EXCEPTIONS as e:
                    if i == 2:
                        logger.exception(e)
                        return await self.go_to_state("state_error")
                    else:
                        continue

        self.save_answer("returning_user", "yes")
        self.save_answer("state_age", data.age)
        return await self.go_to_state("breast_feeding")

    async def breast_feeding(self):
        question = self._(
            "1/13 \n" "\n" "Do you plan to breastfeed your baby after birth?"
        )
        error = self._(
            "Please use numbers from list.\n"
            "\n"
            "Do you plan to breastfeed your baby after birth?"
        )
        choices = [
            Choice("1", "Yes"),
            Choice("2", "No"),
            Choice("3", "Skip"),
        ]

        return ChoiceState(
            self,
            question=question,
            error=error,
            choices=choices,
            next="breast_feeding_term",
        )

    async def breast_feeding_term(self):
        question = self._(
            "2/13 \n"
            "\n"
            "*How long do you plan to give your baby only breastmilk "
            "before giving other foods and water?*"
        )
        error = self._(
            "Please use numbers from list.\n"
            "\n"
            "*How long do you plan to give your baby only"
            " breastmilk before giving other foods and water?*"
        )
        choices = [Choice("1", "Next")]

        return ChoiceState(
            self,
            question=question,
            error=error,
            choices=choices,
            next="next_survey",
        )

    async def next_survey(self):
        pass

    async def survey_error(self):
        return EndState(
            self,
            self._(
                "Sorry, something went wrong. We have been notified. Please try again "
                "later"
            ),
            next=self.START_SURVEY,
        )
