import logging
import random
import re
from datetime import date
from enum import Enum
from urllib.parse import urljoin

import aiohttp
import sentry_sdk

from vaccine import vacreg_config as config
from vaccine.base_application import BaseApplication
from vaccine.data.suburbs import suburbs
from vaccine.states import (
    Choice,
    ChoiceState,
    EndState,
    ErrorMessage,
    FreeText,
    MenuState,
)
from vaccine.utils import (
    HTTP_EXCEPTIONS,
    SAIDNumber,
    calculate_age,
    clean_name,
    countries,
    display_phonenumber,
    enforce_character_limit_in_choices,
    normalise_phonenumber,
)
from vaccine.validators import name_validator, nonempty_validator

logger = logging.getLogger(__name__)


def get_evds():
    # TODO: Cache the session globally. Things that don't work:
    # - Declaring the session at the top of the file
    #   You get a `Timeout context manager should be used inside a task` error
    # - Declaring it here but caching it in a global variable for reuse
    #   You get a `Event loop is closed` error
    return aiohttp.ClientSession(
        timeout=aiohttp.ClientTimeout(total=5),
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "vaccine-registration-ussd",
        },
        auth=aiohttp.BasicAuth(config.EVDS_USERNAME, config.EVDS_PASSWORD),
    )


def get_eventstore():
    # TODO: Cache the session globally. Things that don't work:
    # - Declaring the session at the top of the file
    #   You get a `Timeout context manager should be used inside a task` error
    # - Declaring it here but caching it in a global variable for reuse
    #   You get a `Event loop is closed` error
    return aiohttp.ClientSession(
        timeout=aiohttp.ClientTimeout(total=5),
        headers={
            "Authorization": f"Token {config.VACREG_EVENTSTORE_TOKEN}",
            "Content-Type": "application/json",
            "User-Agent": "healthcheck-ussd",
        },
    )


class Application(BaseApplication):
    START_STATE = "state_age_gate"

    def __init__(self, user):
        super().__init__(user)

        class ID_TYPES(Enum):
            rsa_id = self._("RSA ID Number")
            passport = self._("NON-RSA Passport Number")
            asylum_seeker = self._("Asylum Seeker Permit number")
            refugee = self._("Refugee Permit number")

        self.ID_TYPES = ID_TYPES

    async def state_age_gate(self):
        self.user.answers = {}

        if random.random() < config.THROTTLE_PERCENTAGE / 100.0:
            return await self.go_to_state("state_throttle")

        return MenuState(
            self,
            question=self._(
                "VACCINE REGISTRATION\n"
                "The SA Department of Health thanks you for helping to defeat "
                "COVID-19!\n"
                "\n"
                "Are you {minimum_age} years or older?"
            ).format(minimum_age=config.ELIGIBILITY_AGE_GATE_MIN),
            choices=[
                Choice("state_terms_and_conditions", "Yes"),
                Choice("state_under_age_notification", "No"),
            ],
            error=self._(
                "Self-registration is currently only available to those {minimum_age} "
                "years of age or older. Please tell us if you are {minimum_age} or "
                "older?"
            ).format(minimum_age=config.ELIGIBILITY_AGE_GATE_MIN),
        )

    async def state_throttle(self):
        return EndState(
            self,
            text=self._(
                "We are currently experiencing high volumes of registrations.\n"
                "\n"
                "Your registration is important! Please try again in 15 minutes"
            ),
            next=self.START_STATE,
        )

    async def state_under_age_notification(self):
        return ChoiceState(
            self,
            question=self._(
                "Self-registration is only available to people {minimum_age} years or "
                "older. Can we contact you on this number when this changes?"
            ).format(minimum_age=config.ELIGIBILITY_AGE_GATE_MIN),
            choices=[Choice("yes", self._("Yes")), Choice("no", self._("No"))],
            error=self._("Can we notify you to let you know when you can register?"),
            next="state_confirm_notification",
        )

    async def state_confirm_notification(self):
        return EndState(self, text="Thank you for confirming")

    async def state_terms_and_conditions(self):
        return MenuState(
            self,
            question=self._(
                "PRIVACY POLICY\n"
                "EVDS is POPIA compliant. Your data is kept private + confidential"
                " & only used with your consent for the purpose of "
                "getting vaccinated.\n"
            ),
            choices=[Choice("state_terms_and_conditions_2", self._("Next"))],
            error=self._("TYPE 1 to continue"),
        )

    async def state_terms_and_conditions_2(self):
        return MenuState(
            self,
            question=self._(
                "EVDS uses your data to check eligibility & inform you  of your "
                "vaccination date & venue. Registration is voluntary & does not "
                "guarantee vaccination.\n"
            ),
            choices=[Choice("state_terms_and_conditions_3", self._("Next"))],
            error=self._("TYPE 1 to continue"),
        )

    async def state_terms_and_conditions_3(self):
        return MenuState(
            self,
            question=self._(
                "All security measures are taken to make sure your information is "
                "safe. No personal data will be transferred from EVDS without POPIA "
                "compliance\n"
            ),
            choices=[Choice("state_identification_type", self._("ACCEPT"))],
            error=self._("TYPE 1 to ACCEPT our Privacy Policy"),
        )

    async def state_identification_type(self):
        if self.user.answers.get("state_identification_type"):
            return await self.go_to_state("state_identification_number")
        return ChoiceState(
            self,
            question=self._("How would you like to register?"),
            choices=[Choice(i.name, i.value) for i in self.ID_TYPES],
            error=self._("Please choose 1 of the following ways to register:"),
            next="state_identification_number",
        )

    async def state_identification_number(self):
        idtype = self.ID_TYPES[self.user.answers["state_identification_type"]]
        idtype_label = idtype.value

        if self.user.answers.get("state_identification_number"):
            return await self.go_to_state("state_check_id_number")

        async def validate_identification_number(value):
            error_msg = self._("Invalid {id_type}. Please try again").format(
                id_type=idtype_label
            )
            if idtype == self.ID_TYPES.rsa_id:
                try:
                    id_number = SAIDNumber(value)
                    dob = id_number.date_of_birth
                    if id_number.age > config.AMBIGUOUS_MAX_AGE - 100:
                        self.save_answer("state_dob_year", str(dob.year))
                    self.save_answer("state_dob_month", str(dob.month))
                    self.save_answer("state_dob_day", str(dob.day))
                    self.save_answer("state_gender", id_number.sex.value)
                except ValueError:
                    raise ErrorMessage(error_msg)
            else:
                await nonempty_validator(error_msg)(value)

        return FreeText(
            self,
            question=self._("Please enter your {id_type}").format(id_type=idtype_label),
            next="state_check_id_number",
            check=validate_identification_number,
        )

    async def state_check_id_number(self):
        """
        Checks to see if there's an SA ID number for a non-SA ID ID type
        """
        idtype = self.ID_TYPES[self.user.answers["state_identification_type"]]
        idnumber = self.user.answers["state_identification_number"]

        try:
            SAIDNumber(idnumber)
            if idtype != self.ID_TYPES.rsa_id:
                return MenuState(
                    self,
                    question=self._(
                        "The number you have entered appears to be a RSA ID Number. Is "
                        "this correct?\n"
                    ),
                    choices=[
                        Choice("state_change_to_rsa_id", self._("Yes")),
                        Choice("state_reset_identification", self._("No")),
                    ],
                    error=self._("This looks like an SA ID number"),
                )
        except ValueError:
            pass

        if idtype == self.ID_TYPES.passport:
            next_state = "state_passport_country"
        else:
            next_state = "state_gender"
        return await self.go_to_state(next_state)

    async def state_change_to_rsa_id(self):
        self.save_answer("state_identification_type", self.ID_TYPES.rsa_id.name)
        return await self.go_to_state("state_gender")

    async def state_reset_identification(self):
        del self.user.answers["state_identification_type"]
        del self.user.answers["state_identification_number"]
        return await self.go_to_state("state_identification_type")

    async def state_passport_country(self):
        async def next_state(choice: Choice):
            if choice.value == "other":
                return "state_passport_country_search"
            return "state_gender"

        return ChoiceState(
            self,
            question=self._("Which country issued your passport?"),
            error=self._("Which country issued your passport?"),
            choices=[
                Choice("ZW", self._("Zimbabwe")),
                Choice("MZ", self._("Mozambique")),
                Choice("MW", self._("Malawi")),
                Choice("NG", self._("Nigeria")),
                Choice("CD", self._("DRC")),
                Choice("SO", self._("Somalia")),
                Choice("other", self._("Other")),
            ],
            next=next_state,
        )

    async def state_passport_country_search(self):
        return FreeText(
            self,
            question=self._("Please TYPE in your passport's COUNTRY of origin."),
            next="state_passport_country_list",
        )

    async def state_passport_country_list(self):
        async def next_state(choice: Choice):
            if choice.value == "other":
                return "state_passport_country_search"
            return "state_gender"

        search = self.user.answers["state_passport_country_search"] or ""
        choices = [
            Choice(country[0], country[1][:27])
            for country in countries.search_for_country(search)
        ]
        choices.append(Choice("other", self._("Other")))
        return ChoiceState(
            self,
            question=self._("Please choose the best match for your COUNTRY of origin:"),
            choices=choices,
            error=self._("Do any of these match your COUNTRY:"),
            next=next_state,
        )

    async def state_gender(self):
        if self.user.answers.get("state_gender"):
            return await self.go_to_state("state_dob_year")

        return ChoiceState(
            self,
            question=self._("What is your gender?"),
            choices=[
                Choice("Male", self._("Male")),
                Choice("Female", self._("Female")),
                Choice("Other", self._("Other")),
            ],
            error=self._("Please select your gender using one of the numbers below"),
            next="state_dob_year",
        )

    async def state_dob_year(self):
        if self.user.answers.get("state_dob_year"):
            return await self.go_to_state("state_dob_month")

        async def validate_dob_year(value):
            try:
                assert isinstance(value, str)
                assert value.isdigit()
                assert int(value) > date.today().year - config.AMBIGUOUS_MAX_AGE
                assert int(value) <= date.today().year
            except AssertionError:
                raise ErrorMessage(
                    self._(
                        "REQUIRED: Please TYPE the 4 digits of the YEAR you were born "
                        "(Example: 1980)"
                    )
                )

            idtype = self.ID_TYPES[self.user.answers["state_identification_type"]]
            if idtype == self.ID_TYPES.rsa_id:
                idno = self.user.answers["state_identification_number"]
                if value[-2:] != idno[:2]:
                    raise ErrorMessage(
                        self._(
                            "The YEAR you have given does not match the YEAR of your "
                            "ID number. Please try again"
                        )
                    )

        return FreeText(
            self,
            question=self._(
                "Date of birth: In which YEAR were you born? (Please TYPE just the "
                "YEAR)"
            ),
            next="state_dob_month",
            check=validate_dob_year,
        )

    async def state_dob_month(self):
        if self.user.answers.get("state_dob_month"):
            return await self.go_to_state("state_dob_day")

        return ChoiceState(
            self,
            question=self._("Date of birth: In which MONTH were you born?"),
            choices=[
                Choice("1", self._("Jan")),
                Choice("2", self._("Feb")),
                Choice("3", self._("Mar")),
                Choice("4", self._("Apr")),
                Choice("5", self._("May")),
                Choice("6", self._("June")),
                Choice("7", self._("July")),
                Choice("8", self._("Aug")),
                Choice("9", self._("Sep")),
                Choice("10", self._("Oct")),
                Choice("11", self._("Nov")),
                Choice("12", self._("Dec")),
            ],
            next="state_dob_day",
            error=self._(
                "REQUIRED: Choose your birthday MONTH using the numbers below:"
            ),
        )

    async def state_dob_day(self):
        if self.user.answers.get("state_dob_day"):
            return await self.go_to_state("state_first_name")

        async def validate_dob_day(value):
            dob_year = int(self.user.answers["state_dob_year"])
            dob_month = int(self.user.answers["state_dob_month"])
            try:
                assert isinstance(value, str)
                assert value.isdigit()
                date(dob_year, dob_month, int(value))
            except (AssertionError, ValueError, OverflowError):
                raise ErrorMessage(
                    self._(
                        "ERROR: Please reply with just the DAY of your birthday.\n"
                        "\n"
                        "Example: If you were born on 31 May, type _31_"
                    )
                )

        return FreeText(
            self,
            question=self._(
                "Date of birth: On which DAY of the month were you born? (Please type "
                "just the DAY)"
            ),
            next="state_first_name",
            check=validate_dob_day,
        )

    async def state_first_name(self):
        year = int(self.user.answers["state_dob_year"])
        month = int(self.user.answers["state_dob_month"])
        day = int(self.user.answers["state_dob_day"])
        age = calculate_age(date(year, month, day))
        if age < config.ELIGIBILITY_AGE_GATE_MIN:
            return await self.go_to_state("state_under_age_notification")

        return FreeText(
            self,
            question=self._(
                "Please TYPE your FIRST NAME as it appears in your identification "
                "document"
            ),
            check=name_validator(
                self._(
                    "ERROR: Reply with your FIRST NAME as it appears in your "
                    "identification document"
                )
            ),
            next="state_surname",
        )

    async def state_surname(self):
        return FreeText(
            self,
            question=self._(
                "Please TYPE your SURNAME as it appears in your identification "
                "document."
            ),
            check=name_validator(
                self._(
                    "ERROR: Reply with your SURNAME as it appears in your "
                    "identification document"
                )
            ),
            next="state_confirm_profile",
        )

    async def state_confirm_profile(self):
        first_name = clean_name(self.user.answers["state_first_name"])[:36]
        surname = clean_name(self.user.answers["state_surname"])[:36]
        id_number = self.user.answers["state_identification_number"][:25]
        return MenuState(
            self,
            question=self._(
                "Confirm the following:\n"
                "\n"
                "{first_name} {surname}\n"
                "{id_number}\n"
            ).format(first_name=first_name, surname=surname, id_number=id_number),
            choices=[
                Choice("state_province_id", self._("Correct")),
                Choice("state_identification_type", self._("Wrong")),
            ],
            error=self._(
                "Is the information you shared correct?\n"
                "\n"
                "{first_name} {surname}\n"
                "{id_number}"
            ).format(first_name=first_name, surname=surname, id_number=id_number),
        )

    async def state_province_id(self):
        return ChoiceState(
            self,
            question=self._("Select Your Province"),
            choices=[Choice(*province) for province in await suburbs.provinces()],
            error=self._("Reply with a NUMBER:"),
            next="state_suburb_search",
        )

    async def state_suburb_search(self):
        return FreeText(
            self,
            question=self._(
                "Please TYPE the name of the SUBURB to help us allocate your "
                "appointment"
            ),
            next="state_municipality",
        )

    async def state_municipality(self):
        province = self.user.answers["state_province_id"]
        search = self.user.answers["state_suburb_search"] or ""
        required, results = await suburbs.search(province, search)
        if not required:
            return await self.go_to_state("state_suburb")

        async def next_state(choice: Choice):
            if choice.value == "other":
                return "state_suburb_search"
            return "state_suburb"

        question = self._("Please select your municipality")
        choices = [Choice(k, v[:30]) for k, v in results]
        choices = enforce_character_limit_in_choices(
            choices, 160 - len(question) - len(f"X. {self._('Other')}\n\n")
        )
        choices.append(Choice("other", self._("Other")))
        return ChoiceState(
            self, question=question, error=question, choices=choices, next=next_state
        )

    async def state_suburb(self):
        async def next_state(choice: Choice):
            if choice.value == "other":
                return "state_province_id"
            return "state_self_registration"

        province = self.user.answers["state_province_id"]
        search = self.user.answers["state_suburb_search"] or ""
        municipality = self.user.answers.get("state_municipality")
        _, results = await suburbs.search(province, search, municipality)

        if len(results) == 0:
            return await self.go_to_state("state_province_no_results")

        choices = [Choice(suburb[0], suburb[1][:30]) for suburb in results]
        question = self._("Please choose the best match for your location:")
        choices = enforce_character_limit_in_choices(
            choices, 160 - len(question) - len(f"X. {self._('Other')}\n\n")
        )
        choices.append(Choice("other", self._("Other")))
        return ChoiceState(
            self,
            question=question,
            choices=choices,
            error=self._("Do any of these match your location:"),
            next=next_state,
        )

    async def state_province_no_results(self):
        async def next_(choice: Choice):
            self.save_answer("state_province_id", choice.value)
            return "state_suburb_search"

        return ChoiceState(
            self,
            question=self._("Suburb not found. Try again"),
            choices=[Choice(*province) for province in await suburbs.provinces()],
            error=self._("Reply with a NUMBER:"),
            next=next_,
        )

    async def state_self_registration(self):
        number = display_phonenumber(self.inbound.from_addr)
        return MenuState(
            self,
            question=self._(
                "Can we use this number: {number} to send you SMS appointment "
                "information?"
            ).format(number=number),
            choices=[
                Choice("state_vaccination_time", self._("Yes")),
                Choice("state_phone_number", self._("No")),
            ],
            error=self._(
                "Please reply with a number 1 or 2 to confirm if we can use this "
                "number: {number} to send you SMS appointment information?"
            ).format(number=number),
        )

    async def state_phone_number(self):
        async def phone_number_validation(content):
            try:
                normalise_phonenumber(content)
            except ValueError:
                raise ErrorMessage(
                    self._(
                        "ERROR: Please enter a valid mobile number (do not use spaces)"
                    )
                )

        return FreeText(
            self,
            question=self._(
                "Please TYPE a MOBILE NUMBER we can send an SMS to with your "
                "appointment information"
            ),
            next="state_confirm_phone_number",
            check=phone_number_validation,
        )

    async def state_confirm_phone_number(self):
        number = self.user.answers["state_phone_number"]
        return MenuState(
            self,
            question=self._("Please confirm that your number is {number}.").format(
                number=number
            ),
            choices=[
                Choice("state_vaccination_time", self._("Correct")),
                Choice("state_phone_number", self._("Wrong")),
            ],
            error=self._(
                "ERROR: Please try again. Is the number {number} correct?"
            ).format(number=number),
        )

    async def state_vaccination_time(self):
        return ChoiceState(
            self,
            question=self._(
                "In which time slot would you prefer to get your vaccination?\n"
            ),
            choices=[
                Choice("weekday_morning", self._("Weekday Morning")),
                Choice("weekday_afternoon", self._("Weekday Afternoon")),
                Choice("weekend_morning", self._("Weekend Morning")),
            ],
            error=self._(
                "When would you prefer your vaccine appointment based on the options "
                "below?"
            ),
            next="state_medical_aid",
        )

    async def state_medical_aid(self):
        return ChoiceState(
            self,
            question=self._("Do you belong to a Medical Aid?"),
            choices=[Choice("yes", self._("Yes")), Choice("no", self._("No"))],
            error=self._("ERROR: Please try again. Do you belong to a Medical Aid?"),
            next="state_submit_to_evds",
        )

    async def state_submit_to_evds(self):
        evds = get_evds()
        date_of_birth = date(
            int(self.user.answers["state_dob_year"]),
            int(self.user.answers["state_dob_month"]),
            int(self.user.answers["state_dob_day"]),
        )
        vac_day, vac_time = self.user.answers["state_vaccination_time"].split("_")
        suburb_id = self.user.answers["state_suburb"]
        province_id = self.user.answers["state_province_id"]
        location = {
            "value": suburb_id,
            "text": await suburbs.suburb_name(suburb_id, province_id),
        }
        phonenumber = self.user.answers.get(
            "state_phone_number", self.inbound.from_addr
        )
        data = {
            "gender": self.user.answers["state_gender"],
            "surname": clean_name(self.user.answers["state_surname"]),
            "firstName": clean_name(self.user.answers["state_first_name"]),
            "dateOfBirth": date_of_birth.isoformat(),
            "mobileNumber": normalise_phonenumber(phonenumber).lstrip("+"),
            "preferredVaccineScheduleTimeOfDay": vac_time,
            "preferredVaccineScheduleTimeOfWeek": vac_day,
            "preferredVaccineLocation": location,
            "termsAndConditionsAccepted": True,
            "sourceId": "008c0f09-db09-4d60-83c5-63505c7f05ba",
            "medicalAidMember": self.user.answers["state_medical_aid"] == "yes",
        }
        id_type = self.user.answers["state_identification_type"]
        id_number = re.sub(r"\W", "", self.user.answers["state_identification_number"])
        if id_type == self.ID_TYPES.rsa_id.name:
            data["iDNumber"] = id_number
        if (
            id_type == self.ID_TYPES.refugee.name
            or id_type == self.ID_TYPES.asylum_seeker.name
        ):
            data["refugeeNumber"] = id_number
        if id_type == self.ID_TYPES.passport.name:
            data["passportNumber"] = id_number
            if self.user.answers["state_passport_country"] != "other":
                data["passportCountry"] = self.user.answers["state_passport_country"]
            else:
                data["passportCountry"] = self.user.answers[
                    "state_passport_country_list"
                ]

        async with evds as session:
            for i in range(3):
                try:
                    response = await session.post(
                        url=urljoin(
                            config.EVDS_URL,
                            f"/api/private/{config.EVDS_DATASET}/person/"
                            f"{config.EVDS_VERSION}/record",
                        ),
                        json=data,
                    )
                    response_data = await response.json()
                    self.evds_response = response_data
                    sentry_sdk.set_context(
                        "evds", {"request_data": data, "response_data": response_data}
                    )
                    response.raise_for_status()
                    break
                except HTTP_EXCEPTIONS as e:
                    if i == 2:
                        logger.exception(e)
                        return await self.go_to_state("state_err")
                    else:
                        continue

        return await self.go_to_state("state_submit_to_eventstore")

    async def state_submit_to_eventstore(self):
        eventstore = get_eventstore()
        date_of_birth = date(
            int(self.user.answers["state_dob_year"]),
            int(self.user.answers["state_dob_month"]),
            int(self.user.answers["state_dob_day"]),
        )
        vac_day, vac_time = self.user.answers["state_vaccination_time"].split("_")
        suburb_id = self.user.answers["state_suburb"]
        province_id = self.user.answers["state_province_id"]
        phonenumber = self.user.answers.get(
            "state_phone_number", self.inbound.from_addr
        )

        data = {
            "msisdn": normalise_phonenumber(phonenumber),
            "source": f"USSD {self.inbound.to_addr}",
            "gender": self.user.answers["state_gender"],
            "first_name": clean_name(self.user.answers["state_first_name"]),
            "last_name": clean_name(self.user.answers["state_surname"]),
            "date_of_birth": date_of_birth.isoformat(),
            "preferred_time": vac_time,
            "preferred_date": vac_day,
            "preferred_location_id": suburb_id,
            "preferred_location_name": await suburbs.suburb_name(
                suburb_id, province_id
            ),
            "data": self.evds_response,
        }
        id_type = self.user.answers["state_identification_type"]
        id_number = re.sub(r"\W", "", self.user.answers["state_identification_number"])
        if id_type == self.ID_TYPES.rsa_id.name:
            data["id_number"] = id_number
        if id_type == self.ID_TYPES.asylum_seeker.name:
            data["asylum_seeker_number"] = id_number
        if id_type == self.ID_TYPES.refugee.name:
            data["refugee_number"] = id_number
        if id_type == self.ID_TYPES.passport.name:
            data["passport_number"] = id_number
            if self.user.answers["state_passport_country"] != "other":
                data["passport_country"] = self.user.answers["state_passport_country"]
            else:
                data["passport_country"] = self.user.answers[
                    "state_passport_country_list"
                ]

        async with eventstore as session:
            for i in range(3):
                try:
                    response = await session.post(
                        url=urljoin(
                            config.VACREG_EVENTSTORE_URL, "/v2/vaccineregistration/"
                        ),
                        json=data,
                    )
                    response.raise_for_status()
                    break
                except HTTP_EXCEPTIONS as e:
                    if i == 2:
                        logger.exception(e)
                    else:
                        continue

        return await self.go_to_state("state_success")

    async def state_success(self):
        return EndState(
            self,
            text=self._(
                ":) You have SUCCESSFULLY registered to get vaccinated. Additional "
                "information and appointment details will be sent via SMS."
            ),
        )

    async def state_err(self):
        return EndState(
            self,
            text=self._(
                "Something went wrong with your registration session. Your "
                "registration was not able to be processed. Please try again later"
            ),
        )
