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
from vaccine.utils import DECODE_MESSAGE_EXCEPTIONS

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
        headers={
            "Content-Type": "application/json",
            "User-Agent": "healthcheck-ussd",
        },
    )


def get_turn():
    return aiohttp.ClientSession(
        timeout=aiohttp.ClientTimeout(total=5),
        headers={
            "Authorization": f"Bearer {config.TURN_API_TOKEN}",
            "Accept": "application/vnd.v1+json",
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

        if answers.get("confirmed_contact") == "yes":
            if answers.get("state_province") == "ZA-WC":
                if (
                    int(answers.get("state_age_years")) > 55
                    or answers.get("state_preexisting_conditions") == "yes"
                ) and symptom_count >= 1:
                    return "high"
                return "moderate"
            if symptom_count >= 1:
                return "high"
            return "moderate"

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
        # TODO: normalise msisdn
        msisdn = self.inbound.from_addr
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
        self.save_answer("google_session_token", secrets.token_bytes(20).hex())
        # TODO: normalise msisdn
        msisdn = self.inbound.from_addr
        whatsapp_id = msisdn.lstrip("+")
        async with get_turn() as session:
            for i in range(3):
                try:
                    response = await session.get(
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
                            "sessiontoken": self.user.answers.get("google_session_token"),
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
                except aiohttp.ClientError as e:
                    if i == 2:
                        logger.exception(e)
                        return await self.go_to_state("state_error")
                    else:
                        continue

    async def state_confirm_city(self):
        address = self.user.answers.get("state_city")[: 160 - 79]
        return MenuState(
            self,
            question="\n".join(
                [
                    "Please confirm the address below based on info you shared:",
                    f"{address}",
                    "",
                    "Reply",
                ]
            ),
            error="\n".join(
                [
                    "Please confirm the address below based on info you shared:",
                    f"{address}",
                    "",
                    "Reply",
                ]
            ),
            choices=[
                Choice("state_place_details_lookup", "Yes"),
                Choice("state_city", "No"),
            ],
        )

    async def state_place_details_lookup(self):
        async with get_google_api() as session:
            for i in range(3):
                try:
                    response = await session.get(
                        urljoin(
                            config.GOOGLE_PLACES_URL,
                            "/maps/api/place/details/json",
                        ),
                        params={
                            "key": config.GOOGLE_PLACES_KEY,
                            "place_id": self.user.answers.get("place_id"),
                            "sessiontoken": self.user.answers.get("google_session_token"),
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

                    if self.user.answers.get("confirmed_contact"):
                        return await self.go_to_state("state_tracing")
                    return await self.go_to_state("state_age")
                except aiohttp.ClientError as e:
                    if i == 2:
                        logger.exception(e)
                        return await self.go_to_state("state_error")
                    else:
                        continue

    async def state_age(self):
        if self.user.answers.get("state_age"):
            return await self.go_to_state("state_fever")

        return ChoiceState(
            self,
            question="How old are you?",
            error="\n".join(
                [
                    "Please use numbers from list.",
                    "",
                    "How old are you?",
                ]
            ),
            choices=[
                Choice("<18", "<18"),
                Choice("18-40", "18-39"),
                Choice("40-65", "40-65"),
                Choice(">65", ">65"),
            ],
            next="state_fever",
        )

    async def state_age_years(self):
        if self.user.answers.get("state_age") and self.user.answers.get(
            "state_age_years"
        ):
            return await self.go_to_state("state_province")

        question = "Please TYPE your age in years (eg. 35)"

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
            self,
            question=question,
            check=validate_age,
            next="state_province",
        )

    async def state_fever(self):
        return ChoiceState(
            self,
            question="\n".join(
                [
                    "Do you feel very hot or cold? Are you sweating or shivering? "
                    "When you touch your forehead, does it feel hot?",
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

    async def state_cough(self):
        question = "\n".join(
            ["Do you have a cough that recently started?", "", "Reply"]
        )
        error = "\n".join(
            [
                "Please use numbers from list.",
                "Do you have a cough that recently started?",
                "",
                "Reply",
            ]
        )
        if self.user.answers.get("confirmed_contact") == "yes":
            question = "\n".join(
                [
                    "Do you have a cough that recently started in the last week?",
                    "",
                    "Reply",
                ]
            )
            error = "\n".join(
                [
                    "This service works best when you select numbers from the list.",
                    "",
                    "Do you have a cough that recently started in the last week?",
                    "",
                    "Reply",
                ]
            )
        return ChoiceState(
            self,
            question=question,
            error=error,
            choices=[Choice("yes", "Yes"), Choice("no", "No")],
            next="state_sore_throat",
        )

    async def state_sore_throat(self):
        return ChoiceState(
            self,
            question="\n".join(
                ["Do you have a sore throat, or pain when swallowing?", "", "Reply"]
            ),
            error="\n".join(
                [
                    "Please use numbers from list.",
                    "Do you have a sore throat, or pain when swallowing?",
                    "",
                    "Reply",
                ]
            ),
            choices=[Choice("yes", "Yes"), Choice("no", "No")],
            next="state_breathing",
        )

    async def state_breathing(self):
        question = "\n".join(
            [
                "Do you have breathlessness or a difficulty breathing, that you've "
                "noticed recently?",
                "Reply",
            ]
        )
        error = "\n".join(
            [
                "Please use numbers from list. Do you have breathlessness or a "
                "difficulty breathing, that you've noticed recently?",
                "Reply",
            ]
        )
        next_state = "state_exposure"
        if self.user.answers.get("confirmed_contact") == "yes":
            question = "\n".join(
                [
                    "Do you have shortness of breath while resting or difficulty "
                    "breathing, that you've noticed recently?",
                    "",
                    "Reply",
                ]
            )
            error = "\n".join(
                [
                    "Please use numbers from list.",
                    "",
                    "Do you have shortness of breath while resting or difficulty "
                    "breathing, that you've noticed recently?",
                    "",
                    "Reply",
                ]
            )
            self.save_answer("state_exposure", "yes")
            next_state = "state_taste_and_smell"
        return ChoiceState(
            self,
            question=question,
            error=error,
            choices=[Choice("yes", "Yes"), Choice("no", "No")],
            next=next_state,
        )

    async def state_taste_and_smell(self):
        return ChoiceState(
            self,
            question="\n".join(
                [
                    "Have you noticed any recent changes in your ability to taste or "
                    "smell things?",
                    "",
                    "Reply",
                ]
            ),
            error="\n".join(
                [
                    "This service works best when you select numbers from the list.",
                    "Have you noticed any recent changes in your ability to taste or "
                    "smell things?",
                    "",
                    "Reply",
                ]
            ),
            choices=[Choice("yes", "Yes"), Choice("no", "No")],
            next="state_preexisting_conditions",
        )

    async def state_preexisting_conditions(self):
        if self.user.answers.get("state_preexisting_conditions"):
            return await self.go_to_state("state_age_years")

        return ChoiceState(
            self,
            question="\n".join(
                [
                    "Have you been diagnosed with either Obesity, Diabetes, "
                    "Hypertension or Cardiovascular disease?",
                    "",
                    "Reply",
                ]
            ),
            error="\n".join(
                [
                    "Please use numbers from list.",
                    "",
                    "Have you been diagnosed with either Obesity, Diabetes, "
                    "Hypertension or Cardiovascular disease?",
                    "",
                    "Reply",
                ]
            ),
            choices=[
                Choice("yes", "YES"),
                Choice("no", "NO"),
                Choice("not_sure", "NOT SURE"),
            ],
            next="state_age_years",
        )

    async def state_exposure(self):
        return ChoiceState(
            self,
            question="\n".join(
                [
                    "Have you been in close contact to someone confirmed to be "
                    "infected with COVID19?",
                    "",
                    "Reply",
                ]
            ),
            error="\n".join(
                [
                    "Please use numbers from list. Have u been in contact with someone"
                    " with COVID19 or been where COVID19 patients are treated?",
                    "",
                    "Reply",
                ]
            ),
            choices=[
                Choice("yes", "Yes"),
                Choice("no", "No"),
                Choice("not_sure", "NOT SURE"),
            ],
            next="state_tracing",
        )

    async def state_tracing(self):
        question = "\n".join(
            [
                "Please confirm that the information you shared is correct & that the "
                "National Department of Health can contact you if necessary?",
                "",
                "Reply",
            ]
        )
        error = "\n".join(
            [
                "Please reply with numbers",
                "Is the information you shared correct & can the National Department "
                "of Health contact you if necessary?",
                "",
                "Reply",
            ]
        )
        choices = [
            Choice("yes", "YES"),
            Choice("no", "NO"),
            Choice("restart", "RESTART"),
        ]
        if self.user.answers.get("confirmed_contact") == "yes":
            question = "\n".join(
                [
                    "Finally, please confirm that the information you shared is "
                    "ACCURATE to the best of your knowledge?",
                    "",
                    "Reply",
                ]
            )
            error = "\n".join(
                [
                    "Please use numbers from the list.",
                    "",
                    "Finally, please confirm that the information you shared is "
                    "ACCURATE to the best of your knowledge?",
                    "",
                    "Reply",
                ]
            )
            choices = [
                Choice("yes", "YES"),
                Choice("no", "NO"),
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
                    response = await session.post(
                        urljoin(
                            config.EVENTSTORE_API_URL,
                            "/api/v3/covid19triage/",
                        ),
                        json={
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
                                "state_preexisting_conditions"
                            ),
                            "exposure": self.user.answers.get("state_exposure"),
                            "tracing": self.user.answers.get("state_tracing"),
                            "confirmed_contact": self.user.answers.get("confirmed_contact"),
                            "risk": self.calculate_risk(),
                            "data": {"age_years": self.user.answers.get("state_age_years")},
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
        return await self.go_to_state("state_display_risk")

    async def state_display_risk(self):
        answers = self.user.answers
        risk = self.calculate_risk()
        text = ""
        if answers.get("confirmed_contact"):
            if risk == "moderate":
                text = (
                    "We recommend you SELF-QUARANTINE for the next 10 days and do this "
                    "HealthCheck daily to monitor your symptoms. Stay/sleep alone in a "
                    "room with good air flow."
                )

            if risk == "high":
                text = (
                    "You may be ELIGIBLE FOR COVID-19 TESTING. Go to a testing center "
                    "or Call 0800029999 or visit your healthcare practitioner for info"
                    " on what to do & how to test."
                )
            return EndState(self, text, next=self.START_STATE)

        if answers.get("state_tracing") == "yes":
            if risk == "low":
                text = (
                    "Complete this HealthCheck again in 7 days or sooner if you feel "
                    "ill or you come into contact with someone infected with COVID-19"
                )
            if risk == "moderate":
                text = (
                    "We recommend you SELF-QUARANTINE for the next 10 days and do "
                    "this HealthCheck daily to monitor your symptoms. Stay/sleep "
                    "alone in a room with good air flow."
                )

            if risk == "high":
                text = (
                    "You may be ELIGIBLE FOR COVID-19 TESTING. Go to a testing center "
                    "or Call 0800029999 or visit your healthcare practitioner for "
                    "info on what to do & how to test."
                )
        else:
            if risk == "low":
                # This needs to be a separate state because it needs timeout handling
                return await self.go_to_state("state_no_tracing_low_risk")
            if risk == "moderate":
                # This needs to be a separate state because it needs timeout handling
                return await self.go_to_state("state_no_tracing_moderate_risk")
            if risk == "high":
                text = (
                    "You will not be contacted. You may be ELIGIBLE FOR COVID-19 "
                    "TESTING. Go to a testing center or Call 0800029999 or your "
                    "healthcare practitioner for info."
                )
        return EndState(self, text, next=self.START_STATE)

    async def state_no_tracing_low_risk(self):
        question = (
            "You will not be contacted. If you think you have COVID-19 please"
            " STAY HOME, avoid contact with other people in your community and "
            "self-quarantine."
        )
        return MenuState(
            self,
            question=question,
            choices=[Choice("state_start", "START OVER")],
            error=question,
        )

    async def state_no_tracing_moderate_risk(self):
        question = (
            "You won't be contacted. SELF-QUARANTINE for 10 days, do this HealthCheck "
            "daily to monitor symptoms. Stay/sleep alone in a room with good air flow."
        )
        return MenuState(
            self,
            question=question,
            choices=[Choice("state_start", "START OVER")],
            error=question,
        )

    async def state_error(self):
        return EndState(
            self,
            "Sorry, something went wrong. We have been notified. Please try again "
            "later",
            next=self.START_STATE,
        )
