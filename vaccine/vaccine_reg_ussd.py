import logging
from datetime import date
from enum import Enum
from urllib.parse import urljoin

import aiohttp

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
from vaccine.utils import luhn_checksum

logger = logging.getLogger(__name__)

MAX_AGE = 122


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


class Application(BaseApplication):
    START_STATE = "state_age_gate"

    class ID_TYPES(Enum):
        rsa_id = "RSA ID Number"
        passport = "Passport Number"
        asylum_seeker = "Asylum Seeker Permit number"
        refugee = "Refugee Number Permit number"

    async def state_age_gate(self):
        return MenuState(
            self,
            question="\n".join(
                [
                    "VACCINE REGISTRATION",
                    "The SA Department of Health thanks you for helping to defeat "
                    "COVID-19!",
                    "",
                    f"Are you {config.ELIGIBILITY_AGE_GATE_MIN} years or older?",
                ]
            ),
            choices=[
                Choice("state_identification_type", "Yes"),
                Choice("state_under_age_notification", "No"),
            ],
            error="Self-registration is currently only available to those "
            f"{config.ELIGIBILITY_AGE_GATE_MIN} years of age or older. Please tell us "
            f"if you are {config.ELIGIBILITY_AGE_GATE_MIN} or older?",
        )

    async def state_under_age_notification(self):
        return ChoiceState(
            self,
            question="Self-registration is only available to people "
            f"{config.ELIGIBILITY_AGE_GATE_MIN} years or older. Can we SMS you on this "
            "number when this changes?",
            choices=[Choice("yes", "Yes"), Choice("no", "No")],
            error="Can we notify you via SMS to let you know when you can register?",
            next="state_confirm_notification",
        )

    async def state_confirm_notification(self):
        return EndState(self, text="Thank you for confirming", next=self.START_STATE)

    async def state_identification_type(self):
        return ChoiceState(
            self,
            question="How would you like to register?",
            choices=[Choice(i.name, i.value) for i in self.ID_TYPES],
            error="Please choose 1 of the following ways to register:",
            next="state_identification_number",
        )

    async def state_identification_number(self):
        # TODO: Validate age >= 40 for SAID and Refugee
        idtype = self.ID_TYPES[self.user.answers["state_identification_type"]]
        idtype_label = idtype.value

        if idtype == self.ID_TYPES.passport:
            next_state = "state_passport_country"
        else:
            next_state = "state_gender"

        async def validate_identification_number(value):
            if idtype == self.ID_TYPES.rsa_id or idtype == self.ID_TYPES.refugee:
                try:
                    assert isinstance(value, str)
                    value = value.strip()
                    assert value.isdigit()
                    assert len(value) == 13
                    assert luhn_checksum(value) == 0
                except AssertionError:
                    raise ErrorMessage(f"Invalid {idtype_label}. Please try again")

        return FreeText(
            self,
            question=f"Please enter your {idtype_label}",
            next=next_state,
            check=validate_identification_number,
        )

    async def state_passport_country(self):
        return ChoiceState(
            self,
            question="Which country issued your passport?",
            error="Which country issued your passport?",
            choices=[
                Choice("ZA", "South Africa"),
                Choice("ZW", "Zimbabwe"),
                Choice("MZ", "Mozambique"),
                Choice("MW", "Malawi"),
                Choice("NG", "Nigeria"),
                Choice("CD", "DRC"),
                Choice("SO", "Somalia"),
                Choice("other", "Other"),
            ],
            next="state_gender",
        )

    async def state_gender(self):
        # TODO: Extract from SAID/Refugee
        return ChoiceState(
            self,
            question="What is your gender?",
            choices=[
                Choice("Male", "Male"),
                Choice("Female", "Female"),
                Choice("Other", "Other"),
            ],
            error="Please select your gender using one of the numbers below",
            next="state_dob_year",
        )

    async def state_dob_year(self):
        # TODO: Extract for SAID/Refugee if non-ambiguous
        async def validate_dob_year(value):
            try:
                assert isinstance(value, str)
                assert value.isdigit()
                assert int(value) > date.today().year - MAX_AGE
                assert int(value) <= date.today().year
            except AssertionError:
                raise ErrorMessage(
                    "REQUIRED: Please TYPE the 4 digits of the YEAR you were born "
                    "(Example: 1980)"
                )

        return FreeText(
            self,
            question="Date of birth: In which YEAR were you born? (Please TYPE just "
            "the YEAR)",
            next="state_dob_month",
            check=validate_dob_year,
        )

    async def state_dob_month(self):
        return ChoiceState(
            self,
            question="Date of birth: In which MONTH were you born?",
            choices=[
                Choice("1", "Jan"),
                Choice("2", "Feb"),
                Choice("3", "Mar"),
                Choice("4", "Apr"),
                Choice("5", "May"),
                Choice("6", "June"),
                Choice("7", "July"),
                Choice("8", "Aug"),
                Choice("9", "Sep"),
                Choice("10", "Oct"),
                Choice("11", "Nov"),
                Choice("12", "Dec"),
            ],
            next="state_dob_day",
            error="REQUIRED: Choose your birthday MONTH using the numbers below:",
        )

    async def state_dob_day(self):
        # TODO: stop <age_limit year olds from continuing
        # TODO: confirm what happens if date doesn't match ID date
        async def validate_dob_day(value):
            dob_year = int(self.user.answers["state_dob_year"])
            dob_month = int(self.user.answers["state_dob_month"])
            try:
                assert isinstance(value, str)
                assert value.isdigit()
                date(dob_year, dob_month, int(value))
            except (AssertionError, ValueError):
                raise ErrorMessage(
                    "\n".join(
                        [
                            "ERROR: Please reply with just the DAY of your birthday.",
                            "",
                            "Example: If you were born on 31 May, type _31_",
                        ]
                    )
                )

        return FreeText(
            self,
            question="Date of birth: On which DAY of the month were you born? (Please "
            "type just the DAY)",
            next="state_first_name",
            check=validate_dob_day,
        )

    async def state_first_name(self):
        return FreeText(
            self,
            question="Please TYPE your FIRST NAME as it appears in your identification "
            "document",
            next="state_surname",
        )

    async def state_surname(self):
        return FreeText(
            self,
            question="Please TYPE your SURNAME as it appears in your identification "
            "document.",
            next="state_confirm_profile",
        )

    async def state_confirm_profile(self):
        first_name = self.user.answers["state_first_name"][:36]
        surname = self.user.answers["state_surname"][:36]
        id_number = self.user.answers["state_identification_number"][:25]
        return MenuState(
            self,
            question="\n".join(
                ["Confirm the following:", "", f"{first_name} {surname}", id_number]
            ),
            choices=[
                Choice("state_province", "Correct"),
                Choice("state_identification_type", "Wrong"),
            ],
            error="\n".join(
                [
                    "Is the information you shared correct?",
                    "",
                    f"{first_name} {surname}",
                    id_number,
                ]
            ),
        )

    async def state_province(self):
        return ChoiceState(
            self,
            question="Select Your Province",
            choices=[Choice(*province) for province in suburbs.provinces],
            error="Reply with a NUMBER:",
            next="state_suburb_search",
        )

    async def state_suburb_search(self):
        return FreeText(
            self,
            question="Please TYPE the name of the SUBURB where you live.",
            next="state_suburb",
        )

    async def state_suburb(self):
        async def next_state(choice: Choice):
            if choice.value == "other":
                return "state_province"
            return "state_self_registration"

        province = self.user.answers["state_province"]
        search = self.user.answers["state_suburb_search"] or ""
        choices = [
            Choice(suburb[0], suburb[1][:30])
            for suburb in suburbs.search_for_suburbs(province, search)
        ]
        choices.append(Choice("other", "Other"))
        return ChoiceState(
            self,
            question="Please choose the best match for your location:",
            choices=choices,
            error="Do any of these match your location:",
            next=next_state,
        )

    async def state_self_registration(self):
        number = self.inbound.from_addr
        return MenuState(
            self,
            question=f"Can we use this number: {number} to send you SMS appointment "
            "information?",
            choices=[
                Choice("state_vaccination_time", "Yes"),
                Choice("state_phone_number", "No"),
            ],
            error="Please reply with a number 1 or 2 to confirm if we can use this "
            f"number: {number} to send you SMS appointment information?",
        )

    async def state_phone_number(self):
        # TODO: validate phone number
        return FreeText(
            self,
            question="Please TYPE a CELL NUMBER we can send an SMS to with your "
            "appointment information",
            next="state_confirm_phone_number",
        )

    async def state_confirm_phone_number(self):
        number = self.user.answers["state_phone_number"]
        return MenuState(
            self,
            question=f"Please confirm that your number is {number}.",
            choices=[
                Choice("state_vaccination_time", "Correct"),
                Choice("state_phone_number", "Wrong"),
            ],
            error=f"ERROR: Please try again. Is the number {number} correct?",
        )

    async def state_vaccination_time(self):
        return ChoiceState(
            self,
            question="In which time slot would you prefer to get your vaccination?",
            choices=[
                Choice("weekday_morning", "Weekday Morning"),
                Choice("weekday_afternoon", "Weekday Afternoon"),
                Choice("weekend_morning", "Weekend Morning"),
            ],
            error="When would you prefer your vaccine appointment based on the options "
            "below?",
            next="state_medical_aid",
        )

    async def state_medical_aid(self):
        return ChoiceState(
            self,
            question="Do you belong to a Medical Aid?",
            choices=[Choice("yes", "Yes"), Choice("no", "No")],
            error="ERROR: Please try again. Do you belong to a Medical Aid?",
            next="state_terms_and_conditions",
        )

    async def state_terms_and_conditions(self):
        return MenuState(
            self,
            question="\n".join(
                [
                    "TERMS & CONDITIONS",
                    "",
                    "EVDS is POPI compliant. Your personal, contact, medical aid & "
                    "vaccine details are kept private & are processed with your "
                    "consent",
                ]
            ),
            choices=[Choice("state_terms_and_conditions_2", "Next")],
            error="TYPE 1 to continue",
        )

    async def state_terms_and_conditions_2(self):
        return MenuState(
            self,
            question="EVDS uses your data to check eligibility & inform you of your "
            "vaccination date & venue. Registration is voluntary & does not guarantee "
            "vaccination.",
            choices=[Choice("state_terms_and_conditions_3", "Next")],
            error="TYPE 1 to continue",
        )

    async def state_terms_and_conditions_3(self):
        return MenuState(
            self,
            question="All security measures are taken to make sure your information is "
            "safe. No personal data will be transferred from EVDS without legal "
            "authorisation.",
            choices=[Choice("state_submit_to_evds", "ACCEPT")],
            error="TYPE 1 to ACCEPT our terms and conditions",
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
        province_id = self.user.answers["state_province"]
        location = {
            "value": suburb_id,
            "text": suburbs.suburb_name(suburb_id, province_id),
        }
        data = {
            "gender": self.user.answers["state_gender"],
            "surname": self.user.answers["state_surname"],
            "firstName": self.user.answers["state_first_name"],
            "dateOfBirth": date_of_birth.isoformat(),
            "mobileNumber": self.inbound.from_addr,
            "preferredVaccineScheduleTimeOfDay": vac_time,
            "preferredVaccineScheduleTimeOfWeek": vac_day,
            "preferredVaccineLocation": location,
            "residentialLocation": location,
            "termsAndConditionsAccepted": True,
        }
        id_type = self.user.answers["state_identification_type"]
        if id_type == self.ID_TYPES.rsa_id.name:
            data["iDNumber"] = self.user.answers["state_identification_number"]
        if (
            id_type == self.ID_TYPES.refugee.name
            or id_type == self.ID_TYPES.asylum_seeker.name
        ):
            data["refugeeNumber"] = self.user.answers["state_identification_number"]
        if id_type == self.ID_TYPES.passport.name:
            data["passportNumber"] = self.user.answers["state_identification_number"]
            data["passportCountry"] = self.user.answers["state_passport_country"]

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
                    response.raise_for_status()
                    break
                except aiohttp.ClientError as e:
                    if i == 2:
                        logger.exception(e)
                        return await self.go_to_state("state_error")
                    else:
                        continue

        return await self.go_to_state("state_success")

    async def state_success(self):
        return EndState(
            self,
            text=":) You have SUCCESSFULLY registered to get vaccinated. Additional "
            "information and appointment details will be sent via SMS.",
            next=self.START_STATE,
        )

    async def state_error(self):
        return EndState(
            self,
            text="Something went wrong with your registration session. Your "
            "registration was not able to be processed. Please try again later",
            next=self.START_STATE,
        )
