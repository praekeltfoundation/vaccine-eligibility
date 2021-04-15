import logging
from urllib.parse import urljoin

import aiohttp

import vaccine.healthcheck_config as config
from vaccine.base_application import BaseApplication
from vaccine.states import (
    Choice,
    ChoiceState,
    EndState,
    ErrorMessage,
    FreeText,
    MenuState,
)

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
        if self.user.answers.get("returning_user") == "yes":
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
        if self.user.answers.get("confirmed_contact") == "yes":
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

    async def state_terms(self):
        if self.user.answers.get("confirmed_contact") == "yes":
            next_state = "state_fever"
        else:
            next_state = "state_province"
        if self.user.answers.get("returning_user") == "yes":
            return await self.go_to_state(next_state)

        return MenuState(
            self,
            question="\n".join(
                [
                    "Confirm that you're responsible for your medical care & "
                    "treatment. This service only provides info.",
                    "",
                    "Reply",
                ]
            ),
            error="\n".join(
                [
                    "Please use numbers from list. Confirm that u're responsible for "
                    "ur medical care & treatment. This service only provides info.",
                    "",
                    "Reply",
                ]
            ),
            choices=[
                Choice(next_state, "YES"),
                Choice("state_end", "NO"),
                Choice("state_more_info_pg1", "MORE INFO"),
            ],
        )

    async def state_end(self):
        if self.user.answers.get("confirmed_contact") == "yes":
            text = (
                "You can return to this service at any time. Remember, if you think "
                "you have COVID-19 STAY HOME, avoid contact with other people and "
                "self-quarantine."
            )
        else:
            text = (
                "You can return to this service at any time. Remember, if you think "
                "you have COVID-19 STAY HOME, avoid contact with other people and "
                "self-isolate."
            )
        return EndState(self, text=text, next=self.START_STATE)

    async def state_more_info_pg1(self):
        return MenuState(
            self,
            question="It's not a substitute for professional medical "
            "advice/diagnosis/treatment. Get a qualified health provider's advice "
            "about your medical condition/care.",
            error="It's not a substitute for professional medical "
            "advice/diagnosis/treatment. Get a qualified health provider's advice "
            "about your medical condition/care.",
            choices=[Choice("state_more_info_pg2", "Next")],
        )

    async def state_more_info_pg2(self):
        return MenuState(
            self,
            question="You confirm that you shouldn't disregard/delay seeking medical "
            "advice about treatment/care because of this service. Rely on info at your "
            "own risk.",
            error="You confirm that you shouldn't disregard/delay seeking medical "
            "advice about treatment/care because of this service. Rely on info at your "
            "own risk.",
            choices=[Choice("state_terms", "Next")],
        )

    async def state_province(self):
        if self.user.answers.get("state_province"):
            return await self.go_to_state("state_city")
        return ChoiceState(
            self,
            question="\n".join(["Select your province", "", "Reply:"]),
            error="\n".join(["Select your province", "", "Reply:"]),
            choices=[
                Choice("ZA-EC", "EASTERN CAPE"),
                Choice("ZA-FS", "FREE STATE"),
                Choice("ZA-GT", "GAUTENG"),
                Choice("ZA-NL", "KWAZULU NATAL"),
                Choice("ZA-LP", "LIMPOPO"),
                Choice("ZA-MP", "MPUMALANGA"),
                Choice("ZA-NW", "NORTH WEST"),
                Choice("ZA-NC", "NORTHERN CAPE"),
                Choice("ZA-WC", "WESTERN CAPE"),
            ],
            next="state_city",
        )

    async def state_city(self):
        if self.user.answers.get("state_city") and self.user.answers.get(
            "city_location"
        ):
            if self.user.answers.get("confirmed_contact") == "yes":
                return await self.go_to_state("state_tracing")
            return await self.go_to_state("state_age")

        text = (
            "Please TYPE the name of your Suburb, Township, Town or Village (or "
            "nearest)"
        )

        def validate_city(content):
            if not content.strip():
                raise ErrorMessage(text)

        return FreeText(
            self, question=text, check=validate_city, next="state_google_places_lookup"
        )

    async def state_fever(self):
        return ChoiceState(
            self,
            question="\n".join(
                [
                    "Do you feel very hot or cold? Are you sweating or shivering? When "
                    "you touch your forehead, does it feel hot?",
                    "",
                    "Reply",
                ]
            ),
            error="\n".join(
                [
                    "Please use numbers from list. Do you feel very hot or cold? Are "
                    "you sweating or shivering? When you touch your forehead, does it "
                    "feel hot?",
                    "",
                    "Reply",
                ]
            ),
            choices=[Choice("yes", "Yes"), Choice("no", "No")],
            next="state_cough",
        )

    async def state_error(self):
        return EndState(
            self,
            "Sorry, something went wrong. We have been notified. Please try again "
            "later",
            next=self.START_STATE,
        )
