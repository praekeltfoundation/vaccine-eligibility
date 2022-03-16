import logging
import secrets
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
from vaccine.utils import (
    DECODE_MESSAGE_EXCEPTIONS,
    HTTP_EXCEPTIONS,
    normalise_phonenumber,
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


def get_google_api():
    return aiohttp.ClientSession(
        timeout=aiohttp.ClientTimeout(total=5),
        headers={"Content-Type": "application/json", "User-Agent": "healthcheck-ussd"},
    )


def get_rapidpro():
    return aiohttp.ClientSession(
        timeout=aiohttp.ClientTimeout(total=5),
        headers={
            "Authorization": f"Token {config.RAPIDPRO_TOKEN}",
            "Content-Type": "application/json",
            "User-Agent": "healthcheck-ussd",
        },
    )


class Application(BaseApplication):
    START_STATE = "state_start"

    def calculate_risk(self):
        answers = self.user.answers

        symptom_count = 0
        for answer in [
            answers.get("state_fever"),
            answers.get("state_cough"),
            answers.get("state_sore_throat"),
            answers.get("state_breathing"),
            answers.get("state_taste_and_smell"),
        ]:
            if answer == "yes":
                symptom_count += 1

        if symptom_count == 0:
            if answers.get("state_exposure") == "yes":
                return "moderate"
            return "low"

        if symptom_count == 1:
            if answers.get("state_exposure") == "yes":
                return "high"
            return "moderate"

        if symptom_count == 2:
            if answers.get("state_exposure") == "yes":
                return "high"
            if answers.get("state_age") == ">65":
                return "high"
            return "moderate"

        return "high"

    def format_location(self, latitude, longitude):
        """
        Returns the location in ISO6709 format
        """

        def fractional_part(f):
            if not f % 1:
                return ""
            parts = str(f).split(".")
            return f".{parts[1]}"

        # latitude integer part must be fixed width 2, longitude 3
        return (
            f"{int(latitude):+03d}"
            f"{fractional_part(latitude)}"
            f"{int(longitude):+04d}"
            f"{fractional_part(longitude)}"
            "/"
        )

    async def state_start(self):
        msisdn = normalise_phonenumber(self.inbound.from_addr)
        self.save_answer("google_session_token", secrets.token_bytes(20).hex())
        async with get_eventstore() as session:
            for i in range(3):
                try:
                    response = await session.get(
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
                except HTTP_EXCEPTIONS as e:
                    if i == 2:
                        logger.exception(e)
                        return await self.go_to_state("state_error")
                    else:
                        continue

        self.save_answer("returning_user", "yes")
        self.save_answer("state_province", data["province"])
        self.save_answer("state_city", data["city"])
        if data["city_location"]:
            self.save_answer("city_location", data["city_location"])
        self.save_answer("state_age", data["age"])
        for data_field in [
            "age_years",
            "preexisting_condition",
            "privacy_policy_accepted",
        ]:
            if data["data"].get(data_field):
                self.save_answer(
                    f"state_{data_field}",
                    data["data"].get(data_field),
                )
        return await self.go_to_state("state_save_healthcheck_start")

    async def state_save_healthcheck_start(self):
        async with get_eventstore() as session:
            for i in range(3):
                try:
                    response = await session.post(
                        urljoin(
                            config.EVENTSTORE_API_URL, "/api/v2/covid19triagestart/"
                        ),
                        json={
                            "msisdn": self.inbound.from_addr,
                            "source": f"USSD {self.inbound.to_addr}",
                        },
                    )
                    response.raise_for_status()
                    break
                except HTTP_EXCEPTIONS as e:
                    if i == 2:
                        logger.exception(e)
                        return await self.go_to_state("state_error")
                    else:
                        continue
        return await self.go_to_state("state_welcome")

    async def state_welcome(self):
        error = "This service works best when you select numbers from the list"
        if self.user.answers.get("returning_user") == "yes":
            question = self._(
                "Welcome back to HealthCheck, your weekly COVID-19 Risk Assesment "
                "tool. Let's see how you are feeling today.\n"
                "\n"
                "Reply"
            )
        else:
            question = self._(
                "The National Department of Health thanks you for contributing to "
                "the health of all citizens. Stop the spread of COVID-19\n"
                "\n"
                "Reply"
            )
        return MenuState(
            self,
            question=question,
            choices=[Choice("state_terms", self._("START"))],
            error=error,
        )

    async def state_terms(self):
        if self.user.answers.get("returning_user") == "yes":
            return await self.go_to_state("state_send_privacy_policy_sms")
        return MenuState(
            self,
            question=self._(
                "Confirm that you're responsible for your medical care & treatment. "
                "This service only provides info.\n"
                "\n"
                "Reply"
            ),
            error=self._(
                "Please use numbers from list. Confirm that u're responsible for ur "
                "medical care & treatment. This service only provides info.\n"
                "\n"
                "Reply"
            ),
            choices=[
                Choice("state_send_privacy_policy_sms", self._("YES")),
                Choice("state_end", self._("NO")),
                Choice("state_more_info_pg1", self._("MORE INFO")),
            ],
        )

    async def state_send_privacy_policy_sms(self):
        if self.user.answers.get("state_privacy_policy_accepted") == "yes":
            return await self.go_to_state("state_privacy_policy")

        if (
            config.RAPIDPRO_URL
            and config.RAPIDPRO_TOKEN
            and config.RAPIDPRO_PRIVACY_POLICY_SMS_FLOW
        ):
            async with get_rapidpro() as session:
                for i in range(3):
                    try:
                        data = {
                            "flow": config.RAPIDPRO_PRIVACY_POLICY_SMS_FLOW,
                            "urns": [f"tel:{self.inbound.from_addr}"],
                        }
                        response = await session.post(
                            urljoin(config.RAPIDPRO_URL, "/api/v2/flow_starts.json"),
                            json=data,
                        )
                        response.raise_for_status()
                        break
                    except HTTP_EXCEPTIONS as e:
                        if i == 2:
                            logger.exception(e)
                            return await self.go_to_state("state_error")
                        else:
                            continue

        return await self.go_to_state("state_privacy_policy")

    async def state_privacy_policy(self):
        next_state = "state_age"
        if self.user.answers.get("state_privacy_policy_accepted") == "yes":
            return await self.go_to_state(next_state)

        return MenuState(
            self,
            question=self._(
                "Your personal information is protected under POPIA and in "
                "accordance with the provisions of the HealthCheck Privacy "
                "Notice sent to you by SMS."
            ),
            error=self._(
                "Your personal information is protected under POPIA and in "
                "accordance with the provisions of the HealthCheck Privacy "
                "Notice sent to you by SMS."
            ),
            choices=[Choice(next_state, "Accept")],
        )

    async def state_end(self):
        text = self._(
            "You can return to this service at any time. Remember, if you think "
            "you have COVID-19 STAY HOME, avoid contact with other people and "
            "self-isolate."
        )
        return EndState(self, text=text, next=self.START_STATE)

    async def state_more_info_pg1(self):
        return MenuState(
            self,
            question=self._(
                "It's not a substitute for professional medical advice/diagnosis/"
                "treatment. Get a qualified health provider's advice about your "
                "medical condition/care."
            ),
            error=self._(
                "It's not a substitute for professional medical advice/diagnosis/"
                "treatment. Get a qualified health provider's advice about your "
                "medical condition/care."
            ),
            choices=[Choice("state_more_info_pg2", self._("Next"))],
        )

    async def state_more_info_pg2(self):
        return MenuState(
            self,
            question=self._(
                "You confirm that you shouldn't disregard/delay seeking medical advice "
                "about treatment/care because of this service. Rely on info at your "
                "own risk."
            ),
            error=self._(
                "You confirm that you shouldn't disregard/delay seeking medical advice "
                "about treatment/care because of this service. Rely on info at your "
                "own risk."
            ),
            choices=[Choice("state_terms", self._("Next"))],
        )

    async def state_age(self):
        if self.user.answers.get("state_age"):
            return await self.go_to_state("state_province")

        return ChoiceState(
            self,
            question=self._("How old are you?"),
            error=self._("Please use numbers from list.\n" "\n" "How old are you?"),
            choices=[
                Choice("<18", "<18"),
                Choice("18-40", "18-39"),
                Choice("40-65", "40-65"),
                Choice(">65", ">65"),
            ],
            next="state_province",
        )

    async def state_province(self):
        if self.user.answers.get("state_province"):
            return await self.go_to_state("state_city")
        return ChoiceState(
            self,
            question=self._("Select your province\n" "\n" "Reply:"),
            error=self._("Select your province\n" "\n" "Reply:"),
            choices=[
                Choice("ZA-EC", self._("EASTERN CAPE")),
                Choice("ZA-FS", self._("FREE STATE")),
                Choice("ZA-GT", self._("GAUTENG")),
                Choice("ZA-NL", self._("KWAZULU NATAL")),
                Choice("ZA-LP", self._("LIMPOPO")),
                Choice("ZA-MP", self._("MPUMALANGA")),
                Choice("ZA-NW", self._("NORTH WEST")),
                Choice("ZA-NC", self._("NORTHERN CAPE")),
                Choice("ZA-WC", self._("WESTERN CAPE")),
            ],
            next="state_city",
        )

    async def state_city(self):
        skip = False

        if self.user.answers.get("state_city") and self.user.answers.get(
            "city_location"
        ):
            skip = True

        if self.user.answers.get("state_age") == "<18":
            self.save_answer("state_city", "<not collected>")
            skip = True

        if skip:
            return await self.go_to_state("state_fever")

        text = self._(
            "Please TYPE the name of your Suburb, Township, Town or Village (or "
            "nearest)"
        )

        async def validate_city(content):
            if not content or not content.strip():
                raise ErrorMessage(text)

        return FreeText(
            self, question=text, check=validate_city, next="state_google_places_lookup"
        )

    async def state_google_places_lookup(self):

        async with get_google_api() as session:
            for i in range(3):
                try:
                    response = await session.get(
                        urljoin(
                            config.GOOGLE_PLACES_URL,
                            "/maps/api/place/autocomplete/json",
                        ),
                        params={
                            "input": self.user.answers.get("state_city"),
                            "key": config.GOOGLE_PLACES_KEY,
                            "sessiontoken": self.user.answers.get(
                                "google_session_token"
                            ),
                            "language": "en",
                            "components": "country:za",
                        },
                    )
                    response.raise_for_status()
                    data = await response.json()

                    if data["status"] != "OK":
                        return await self.go_to_state("state_city")

                    first_result = data["predictions"][0]
                    self.save_answer("place_id", first_result["place_id"])
                    self.save_answer("state_city", first_result["description"])

                    return await self.go_to_state("state_confirm_city")
                except HTTP_EXCEPTIONS as e:
                    if i == 2:
                        logger.exception(e)
                        return await self.go_to_state("state_error")
                    else:
                        continue

    async def state_confirm_city(self):
        address = self.user.answers.get("state_city")[: 160 - 79]
        return MenuState(
            self,
            question=self._(
                "Please confirm the address below based on info you shared:\n"
                "{address}\n"
                "\n"
                "Reply"
            ).format(address=address),
            error=self._(
                "Please confirm the address below based on info you shared:\n"
                "{address}\n"
                "\n"
                "Reply"
            ).format(address=address),
            choices=[
                Choice("state_place_details_lookup", self._("Yes")),
                Choice("state_city", self._("No")),
            ],
        )

    async def state_place_details_lookup(self):
        async with get_google_api() as session:
            for i in range(3):
                try:
                    response = await session.get(
                        urljoin(
                            config.GOOGLE_PLACES_URL, "/maps/api/place/details/json"
                        ),
                        params={
                            "key": config.GOOGLE_PLACES_KEY,
                            "place_id": self.user.answers.get("place_id"),
                            "sessiontoken": self.user.answers.get(
                                "google_session_token"
                            ),
                            "language": "en",
                            "fields": "geometry",
                        },
                    )
                    response.raise_for_status()
                    data = await response.json()

                    if data["status"] != "OK":
                        return await self.go_to_state("state_city")

                    location = data["result"]["geometry"]["location"]

                    self.save_answer(
                        "city_location",
                        self.format_location(location["lat"], location["lng"]),
                    )

                    return await self.go_to_state("state_fever")
                except HTTP_EXCEPTIONS as e:
                    if i == 2:
                        logger.exception(e)
                        return await self.go_to_state("state_error")
                    else:
                        continue

    async def state_age_years(self):
        if self.user.answers.get("state_age") and self.user.answers.get(
            "state_age_years"
        ):
            return await self.go_to_state("state_province")

        question = self._("Please TYPE your age in years (eg. 35)")

        async def validate_age(content):
            try:
                age = int(content)
            except DECODE_MESSAGE_EXCEPTIONS:
                raise ErrorMessage(question)

            if age < 1:
                raise ErrorMessage(question)
            elif age < 18:
                self.save_answer("state_age", "<18")
            elif age < 40:
                self.save_answer("state_age", "18-40")
            elif age <= 65:
                self.save_answer("state_age", "40-65")
            elif age < 150:
                self.save_answer("state_age", ">65")
            else:
                raise ErrorMessage(question)

        return FreeText(
            self, question=question, check=validate_age, next="state_province"
        )

    async def state_fever(self):
        return ChoiceState(
            self,
            question=self._(
                "Do you feel very hot or cold? Are you sweating or shivering? When you "
                "touch your forehead, does it feel hot?\n"
                "\n"
                "Reply"
            ),
            error=self._(
                "Please use numbers from list. Do you feel very hot or cold? Are you "
                "sweating or shivering? When you touch your forehead, does it feel "
                "hot?\n"
                "\n"
                "Reply"
            ),
            choices=[Choice("yes", self._("Yes")), Choice("no", self._("No"))],
            next="state_cough",
        )

    async def state_cough(self):
        question = self._("Do you have a cough that recently started?\n" "\n" "Reply")
        error = self._(
            "Please use numbers from list.\n"
            "Do you have a cough that recently started?\n"
            "\n"
            "Reply"
        )
        return ChoiceState(
            self,
            question=question,
            error=error,
            choices=[Choice("yes", self._("Yes")), Choice("no", self._("No"))],
            next="state_sore_throat",
        )

    async def state_sore_throat(self):
        return ChoiceState(
            self,
            question=self._(
                "Do you have a sore throat, or pain when swallowing?\n" "\n" "Reply"
            ),
            error=self._(
                "Please use numbers from list.\n"
                "Do you have a sore throat, or pain when swallowing?\n"
                "\n"
                "Reply"
            ),
            choices=[Choice("yes", self._("Yes")), Choice("no", self._("No"))],
            next="state_breathing",
        )

    async def state_breathing(self):
        question = self._(
            "Do you have breathlessness or a difficulty breathing, that you've "
            "noticed recently?\n"
            "Reply"
        )
        error = self._(
            "Please use numbers from list. Do you have breathlessness or a "
            "difficulty breathing, that you've noticed recently?\n"
            "Reply"
        )
        next_state = "state_exposure"
        return ChoiceState(
            self,
            question=question,
            error=error,
            choices=[Choice("yes", self._("Yes")), Choice("no", self._("No"))],
            next=next_state,
        )

    async def state_taste_and_smell(self):
        return ChoiceState(
            self,
            question=self._(
                "Have you noticed any recent changes in your ability to taste or "
                "smell things?\n"
                "\n"
                "Reply"
            ),
            error=self._(
                "This service works best when you select numbers from the list.\n"
                "Have you noticed any recent changes in your ability to taste or "
                "smell things?\n"
                "\n"
                "Reply"
            ),
            choices=[Choice("yes", self._("Yes")), Choice("no", self._("No"))],
            next="state_preexisting_conditions",
        )

    async def state_preexisting_conditions(self):
        if self.user.answers.get("state_preexisting_conditions"):
            return await self.go_to_state("state_age_years")

        return ChoiceState(
            self,
            question=self._(
                "Have you been diagnosed with either Obesity, Diabetes, "
                "Hypertension or Cardiovascular disease?\n"
                "\n"
                "Reply"
            ),
            error=self._(
                "Please use numbers from list.\n"
                "\n"
                "Have you been diagnosed with either Obesity, Diabetes, "
                "Hypertension or Cardiovascular disease?\n"
                "\n"
                "Reply"
            ),
            choices=[
                Choice("yes", self._("YES")),
                Choice("no", self._("NO")),
                Choice("not_sure", self._("NOT SURE")),
            ],
            next="state_age_years",
        )

    async def state_exposure(self):
        return ChoiceState(
            self,
            question=self._(
                "Have you been in close contact to someone confirmed to be "
                "infected with COVID19?\n"
                "\n"
                "Reply"
            ),
            error=self._(
                "Please use numbers from list. Have u been in contact with someone"
                " with COVID19 or been where COVID19 patients are treated?\n"
                "\n"
                "Reply"
            ),
            choices=[
                Choice("yes", self._("Yes")),
                Choice("no", self._("No")),
                Choice("not_sure", self._("NOT SURE")),
            ],
            next="state_tracing",
        )

    async def state_tracing(self):
        question = self._(
            "Please confirm that the information you shared is correct & that the "
            "National Department of Health can contact you if necessary?\n"
            "\n"
            "Reply"
        )
        error = self._(
            "Please reply with numbers\n"
            "Is the information you shared correct & can the National Department "
            "of Health contact you if necessary?\n"
            "\n"
            "Reply"
        )
        choices = [
            Choice("yes", self._("YES")),
            Choice("no", self._("NO")),
            Choice("restart", self._("RESTART")),
        ]
        return ChoiceState(
            self,
            question=question,
            error=error,
            choices=choices,
            next="state_submit_data",
        )

    async def state_submit_data(self):

        if self.user.answers.get("state_tracing") == "restart":
            return await self.go_to_state("state_start")

        async with get_eventstore() as session:
            for i in range(3):
                try:
                    data = {
                        "msisdn": self.inbound.from_addr,
                        "source": f"USSD {self.inbound.to_addr}",
                        "province": self.user.answers.get("state_province"),
                        "city": self.user.answers.get("state_city"),
                        "city_location": self.user.answers.get("city_location"),
                        "age": self.user.answers.get("state_age"),
                        "fever": self.user.answers.get("state_fever"),
                        "cough": self.user.answers.get("state_cough"),
                        "sore_throat": self.user.answers.get("state_sore_throat"),
                        "difficulty_breathing": self.user.answers.get(
                            "state_breathing"
                        ),
                        "smell": self.user.answers.get("state_taste_and_smell"),
                        "preexisting_condition": self.user.answers.get(
                            "state_preexisting_conditions", ""
                        ),
                        "exposure": self.user.answers.get("state_exposure"),
                        "tracing": self.user.answers.get("state_tracing"),
                        "risk": self.calculate_risk(),
                        "data": {
                            "age_years": self.user.answers.get("state_age_years"),
                            "privacy_policy_accepted": "yes",
                        },
                    }
                    logger.info(">>>> state_submit_data /api/v3/covid19triage/")
                    logger.info(config.EVENTSTORE_API_URL)
                    logger.info(data)
                    response = await session.post(
                        urljoin(config.EVENTSTORE_API_URL, "/api/v3/covid19triage/"),
                        json=data,
                    )
                    response.raise_for_status()
                    break
                except HTTP_EXCEPTIONS as e:
                    if i == 2:
                        logger.exception(e)
                        return await self.go_to_state("state_error")
                    else:
                        continue
        return await self.go_to_state("state_display_risk")

    async def state_display_risk(self):
        answers = self.user.answers
        risk = self.calculate_risk()
        text = ""

        if answers.get("state_tracing") == "yes":
            if risk == "low":
                text = self._(
                    "Complete this HealthCheck again in 7 days or sooner if you feel "
                    "ill or you come into contact with someone infected with COVID-19"
                )
            if risk == "moderate":
                text = self._(
                    "Use this HealthCheck to watch out for COVID symptoms. You do not "
                    "need to isolate at this stage. If symptoms develop please see a "
                    "healthcare professional."
                )

            if risk == "high":
                text = self._(
                    "You may be ELIGIBLE FOR A COVID-19 TEST. Go to a testing centre, "
                    "call 0800029999 or see a health worker. Self-isolate if you test "
                    "positive AND have symptoms"
                )
        else:
            if risk == "low":
                # This needs to be a separate state because it needs timeout handling
                return await self.go_to_state("state_no_tracing_low_risk")
            if risk == "moderate":
                # This needs to be a separate state because it needs timeout handling
                return await self.go_to_state("state_no_tracing_moderate_risk")
            if risk == "high":
                text = self._(
                    "You will not be contacted. You may be ELIGIBLE FOR COVID-19 "
                    "TESTING. Go to a testing center or Call 0800029999 or your "
                    "healthcare practitioner for info."
                )

        if config.TB_USSD_CODE and risk != "high":
            return MenuState(
                self,
                question=self._(text),
                error=self._(text),
                choices=[Choice("state_tb_prompt_1", self._("Next"))],
            )
        else:
            return EndState(self, text, next=self.START_STATE)

    async def state_tb_prompt_1(self):
        answers = self.user.answers
        risk = self.calculate_risk()

        text = ""
        if risk == "moderate":
            if answers.get("state_cough") == "yes":
                text = self._(
                    "A cough may also be a sign of TB - a dangerous but treatable "
                    "disease."
                )
            elif answers.get("state_fever") == "yes":
                text = self._("A fever or night sweats may also be signs of TB.")
        else:
            text = self._(
                "One of the less obvious signs of TB is losing weight without "
                "realising it."
            )

        if text:
            return MenuState(
                self,
                question=self._(text),
                error=self._(text),
                choices=[Choice("state_tb_prompt_2", self._("Next"))],
            )
        else:
            return await self.go_to_state("state_tb_prompt_2")

    async def state_tb_prompt_2(self):
        risk = self.calculate_risk()
        text = ""
        if risk == "moderate":
            text = self._(
                "Some COVID symptoms are like TB symptoms. To protect your health, we "
                "recommend that you complete a TB HealthCheck. To start, please dial "
                f"{config.TB_USSD_CODE}"
            )
        else:
            text = self._(
                "If you or a family member has cough, fever, weight loss or night "
                "sweats, please also check if you have TB by dialling "
                f"{config.TB_USSD_CODE}"
            )
        return EndState(self, text, next=self.START_STATE)

    async def state_no_tracing_low_risk(self):
        question = self._(
            "You will not be contacted. If you think you have COVID-19 please"
            " STAY HOME, avoid contact with other people in your community and "
            "self-quarantine."
        )
        next_text = "START OVER"
        next_state = "state_start"
        if config.TB_USSD_CODE:
            next_text = "Next"
            next_state = "state_tb_prompt_1"
        return MenuState(
            self,
            question=question,
            choices=[Choice(next_state, next_text)],
            error=question,
        )

    async def state_no_tracing_moderate_risk(self):
        question = self._(
            "You will not be contacted. Use HealthCheck to check for COVID symptoms. "
            "You do not need to isolate. If symptoms develop please isolate for 7 days."
        )
        next_text = "START OVER"
        next_state = "state_start"
        if config.TB_USSD_CODE:
            next_text = "Next"
            next_state = "state_tb_prompt_1"
        return MenuState(
            self,
            question=question,
            choices=[Choice(next_state, next_text)],
            error=question,
        )

    async def state_error(self):
        return EndState(
            self,
            self._(
                "Sorry, something went wrong. We have been notified. Please try again "
                "later"
            ),
            next=self.START_STATE,
        )
