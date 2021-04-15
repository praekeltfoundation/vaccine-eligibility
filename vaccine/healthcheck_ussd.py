import logging
from urllib.parse import urljoin

import aiohttp

import vaccine.healthcheck_config as config
from vaccine.base_application import BaseApplication
from vaccine.states import Choice, EndState, MenuState

logger = logging.getLogger(__name__)


def get_eventstore():
    # TODO: Cache the session globally. Things that don't work:
    # - Declaring the session at the top of the file
    #   You get a `Timeout context manager should be used inside a task` error
    # - Declaring it here but caching it in a global variable for reuse
    #   You get a `Event loop is closed` error
    return aiohttp.ClientSession(
        timeout=aiohttp.ClientTimeout(total=5),
        headers={
            "Authorization": f"Token {config.EVENTSTORE_API_TOKEN}",
            "Content-Type": "application/json",
            "User-Agent": "healthcheck-ussd",
        },
    )


def get_turn():
    return aiohttp.ClientSession(
        timeout=aiohttp.ClientTimeout(total=5),
        headers={
            "Authorization": f"Bearer {config.TURN_API_TOKEN}",
            "Content-Type": "application/vnd.v1+json",
            "User-Agent": "healthcheck-ussd",
        },
    )


class Application(BaseApplication):
    START_STATE = "state_start"

    async def state_start(self):
        # TODO: normalise msisdn
        msisdn = self.inbound.from_addr
        for i in range(3):
            try:
                response = await get_eventstore().get(
                    urljoin(
                        config.EVENTSTORE_API_URL,
                        f"/api/v2/healthcheckuserprofile/{msisdn}/",
                    )
                )
                if response.status == 404:
                    self.save_answer("returning_user", "no")
                    return await self.go_to_state("state_save_healthcheck_start")
                response.raise_for_status()
                data = await response.json()
                break
            except aiohttp.ClientError as e:
                if i == 2:
                    logger.exception(e)
                    return await self.go_to_state("state_error")
                else:
                    continue

        self.save_answer("returning_user", "yes")
        self.save_answer("state_province", data["province"])
        self.save_answer("state_city", data["city"])
        self.save_answer("city_location", data["city_location"])
        self.save_answer("state_age", data["age"])
        self.save_answer("state_age_years", data["data"].get("age_years"))
        self.save_answer(
            "state_preexisting_conditions", data["data"].get("preexisting_condition")
        )
        return await self.go_to_state("state_save_healthcheck_start")

    async def state_save_healthcheck_start(self):
        for i in range(3):
            try:
                response = await get_eventstore().post(
                    urljoin(config.EVENTSTORE_API_URL, "/api/v2/covid19triagestart/"),
                    json={
                        "msisdn": self.inbound.from_addr,
                        "source": f"USSD {self.inbound.to_addr}",
                    },
                )
                response.raise_for_status()
                break
            except aiohttp.ClientError as e:
                if i == 2:
                    logger.exception(e)
                    return await self.go_to_state("state_error")
                else:
                    continue
        return await self.go_to_state("state_get_confirmed_contact")

    async def state_get_confirmed_contact(self):
        # TODO: normalise msisdn
        msisdn = self.inbound.from_addr
        whatsapp_id = msisdn.lstrip("+")
        for i in range(3):
            try:
                response = await get_turn().get(
                    urljoin(config.TURN_API_URL, f"/v1/contacts/{whatsapp_id}/profile")
                )
                response.raise_for_status()
                data = await response.json()
                break
            except aiohttp.ClientError as e:
                if i == 2:
                    logger.exception(e)
                    return await self.go_to_state("state_error")
                else:
                    continue
        confirmed_contact = data.get("fields", {}).get("confirmed_contact", False)
        self.save_answer("confirmed_contact", "yes" if confirmed_contact else "no")
        return await self.go_to_state("state_welcome")

    async def state_welcome(self):
        error = "This service works best when you select numbers from the list"
        if self.user.answers["returning_user"] == "yes":
            question = "\n".join(
                [
                    "Welcome back to HealthCheck, your weekly COVID-19 Risk Assesment "
                    "tool. Let's see how you are feeling today.",
                    "",
                    "Reply",
                ]
            )
        else:
            question = "\n".join(
                [
                    "The National Department of Health thanks you for contributing to "
                    "the health of all citizens. Stop the spread of COVID-19",
                    "",
                    "Reply",
                ]
            )
        if self.user.answers["confirmed_contact"] == "yes":
            question = "\n".join(
                [
                    "The National Department of Health thanks you for contributing to "
                    "the health of all citizens. Stop the spread of COVID-19",
                    "",
                    "Reply",
                ]
            )
            error = question
        return MenuState(
            self,
            question=question,
            choices=[Choice("state_terms", "START")],
            error=error,
        )

    async def state_error(self):
        return EndState(
            self,
            "Sorry, something went wrong. We have been notified. Please try again "
            "later",
            next=self.START_STATE,
        )
