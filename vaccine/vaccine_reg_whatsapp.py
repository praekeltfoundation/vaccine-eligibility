import logging
from datetime import date
from email.utils import parseaddr
from enum import Enum
from typing import List
from urllib.parse import urljoin

import aiohttp

from vaccine import vacreg_config as config
from vaccine.base_application import BaseApplication
from vaccine.data.medscheme import medical_aids
from vaccine.data.suburbs import suburbs
from vaccine.models import Message
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
    countries,
    display_phonenumber,
    normalise_phonenumber,
)

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

    class ID_TYPES(Enum):
        rsa_id = "RSA ID Number"
        passport = "Passport Number"
        asylum_seeker = "Asylum Seeker Permit number"
        refugee = "Refugee Permit number"

    async def process_message(self, message: Message) -> List[Message]:
        if message.session_event == Message.SESSION_EVENT.CLOSE:
            self.state_name = "state_timeout"
        return await super().process_message(message)

    async def state_timeout(self):
        return EndState(
            self,
            text="\n".join(
                [
                    "*VACCINE REGISTRATION SECURE CHAT* 🔐",
                    "",
                    "We haven’t heard from you in a while!",
                    "",
                    "The registration session has timed out due to inactivity. You "
                    "will need to start again. Just TYPE the word REGISTER.",
                    "",
                    "-----",
                    "📌 Reply *0* to return to the main *MENU*",
                ]
            ),
        )

    async def state_age_gate(self):
        self.user.answers = {}

        return MenuState(
            self,
            question="\n".join(
                [
                    "*VACCINE REGISTRATION SECURE CHAT* 🔐",
                    "",
                    "Welcome to the official Phase 2&3 COVID-19 Vaccination "
                    "Self-registration Portal from the National Department of Health. "
                    "Registration will take about 5 minutes. Please have your ID, "
                    "Passport, Refugee Permit or Asylum Seeker Permit *Number* on "
                    "hand. If you have Medical Aid, we will also ask for your Medical "
                    "Aid Number.",
                    "",
                    "Note: If you are a health professional, register for Phase 1 at "
                    "https://vaccine.enroll.health.gov.za/",
                    "",
                    "Registration is currently only open to those "
                    f"{config.ELIGIBILITY_AGE_GATE_MIN} years and older. Are you "
                    f"{config.ELIGIBILITY_AGE_GATE_MIN} or older?",
                    "",
                ]
            ),
            error="\n".join(
                [
                    "⚠️ This service works best when you use the numbered options "
                    "available",
                    "",
                    f"Please confirm that you are {config.ELIGIBILITY_AGE_GATE_MIN} "
                    "years or older by typing 1 (or 2 if you are NOT "
                    f"{config.ELIGIBILITY_AGE_GATE_MIN} years or older)",
                ]
            ),
            choices=[
                Choice(
                    "state_terms_pdf",
                    f"Yes, I am {config.ELIGIBILITY_AGE_GATE_MIN} or older",
                ),
                Choice("state_under_age_notification", "No"),
            ],
        )

    async def state_under_age_notification(self):
        return ChoiceState(
            self,
            question="\n".join(
                [
                    "Can we notify you via Whatsapp on this number when updates about "
                    "getting vaccinated become available?",
                    "",
                ]
            ),
            choices=[Choice("yes", "Yes"), Choice("no", "No")],
            error="\n".join(
                [
                    "⚠️ This service works best when you use the numbered options "
                    "available.",
                    "",
                    "Please let us know if we can notify you via Whatsapp on this "
                    "number when updates about getting vaccinated become available?",
                ]
            ),
            next="state_confirm_notification",
        )

    async def state_confirm_notification(self):
        return EndState(self, text="Thank you for confirming")

    async def state_terms_pdf(self):
        self.messages.append(
            self.inbound.reply(
                None,
                helper_metadata={
                    "document": "https://healthcheck-rasa-images.s3.af-south-1.amazonaw"
                    "s.com/ELECTRONIC+VACCINATION+DATA+SYSTEM+(EVDS)+%E2%80%93+DATA+"
                    "PROTECTION+%26+PRIVACY+POLICY.pdf"
                },
            )
        )
        return await self.go_to_state("state_terms_and_conditions")

    async def state_terms_and_conditions(self):
        return MenuState(
            self,
            question="\n".join(
                [
                    "*VACCINE REGISTRATION SECURE CHAT* 🔐",
                    "",
                    "Do you agree to the attached Electronic Vaccine Data System "
                    "PRIVACY POLICY that explains how your data is used and protected?",
                ]
            ),
            choices=[
                Choice("state_terms_and_conditions_summary", "Read summary"),
                Choice("state_province_id", "Accept"),
            ],
            error="⚠️ This service works best when you reply with one of the numbers "
            "next to the options provided.",
        )

    async def state_terms_and_conditions_summary(self):
        return MenuState(
            self,
            question="\n".join(
                [
                    "*VACCINE REGISTRATION SECURE CHAT* 🔐",
                    "",
                    "*Electronic Vaccine Data System DATA PROTECTION & PRIVACY POLICY "
                    "(“EVDS Privacy Policy) SUMMARY*",
                    "",
                    "The EVDS Privacy Policy complies with the POPI Act.",
                    "",
                    "Your personal data including: contact, medical aid & vaccine "
                    "protocol details are processed with your consent for the agreed "
                    "purpose (to support the COVID-19 Vaccination roll out in South "
                    "Africa) and remain confidential.",
                    "",
                    "EVDS uses your data to check your eligibility & inform you of the "
                    "date & venue of your vaccination.",
                    "",
                    "Registration is voluntary & does not guarantee vaccination.",
                    "",
                    "All security measures have been taken to keep your information "
                    "safe. No personal data will be transferred from EVDS without "
                    "legislative authorisation in compliance with the Popi Act.",
                    "",
                    "Do you accept the EVDS Privacy Notice?",
                ]
            ),
            choices=[
                Choice("state_province_id", "Yes, I accept"),
                Choice("state_no_terms", "No"),
            ],
            error="\n".join(
                [
                    "⚠️ This service works best when you reply with one of the numbers "
                    "next to the options provided.",
                    "",
                    "Do you accept the EVDS Privacy Notice?",
                ]
            ),
        )

    async def state_no_terms(self):
        return EndState(
            self,
            text="\n".join(
                [
                    "*VACCINE REGISTRATION SECURE CHAT* 🔐",
                    "",
                    "Thank you. If you change your mind, type *REGISTER* to restart "
                    "your registration session",
                ]
            ),
        )

    async def state_province_id(self):
        return ChoiceState(
            self,
            question="\n".join(
                [
                    "*VACCINE REGISTRATION SECURE CHAT* 🔐",
                    "",
                    "We need your location to help us match you with a nearby "
                    "vaccination site",
                    "",
                    "Select your province",
                ]
            ),
            choices=[Choice(*province) for province in await suburbs.provinces()],
            error="Reply with a NUMBER:",
            next="state_suburb_search",
        )

    async def state_suburb_search(self):
        return FreeText(
            self,
            question="\n".join(
                [
                    "*VACCINE REGISTRATION SECURE CHAT* 🔐",
                    "",
                    "Please TYPE the name of the SUBURB where you want to get "
                    "vaccinated",
                ]
            ),
            next="state_suburb",
        )

    async def state_suburb(self):
        async def next_state(choice: Choice):
            if choice.value == "other":
                return "state_province_id"
            return "state_identification_type"

        province = self.user.answers["state_province_id"]
        search = self.user.answers["state_suburb_search"] or ""
        choices = [
            Choice(suburb[0], suburb[1][:200])
            for suburb in await suburbs.whatsapp_search(province, search)
        ]
        choices.append(Choice("other", "Other"))
        return ChoiceState(
            self,
            question="\n".join(
                [
                    "*VACCINE REGISTRATION SECURE CHAT* 🔐" "",
                    "Please REPLY with a NUMBER to confirm your location:",
                ]
            ),
            choices=choices,
            error="\n".join(
                [
                    "⚠️ This service works best when you reply with one of the numbers "
                    "next to the options provided.",
                    "",
                    "Please REPLY with a NUMBER from the list below to confirm the "
                    "location you have shared:",
                ]
            ),
            next=next_state,
        )

    async def state_identification_type(self):
        return ChoiceState(
            self,
            question="\n".join(
                [
                    "*VACCINE REGISTRATION SECURE CHAT* 🔐",
                    "",
                    "Which method would you like to use for identification?",
                ]
            ),
            choices=[Choice(i.name, i.value) for i in self.ID_TYPES],
            error="\n".join(
                [
                    "⚠️ This service works best when you reply with one of the numbers "
                    "next to the options provided.",
                    "",
                    "Please choose the type of identification document you have from "
                    "the list below?",
                ]
            ),
            next="state_identification_number",
        )

    async def state_identification_number(self):
        idtype = self.ID_TYPES[self.user.answers["state_identification_type"]]
        idtype_label = idtype.value

        if idtype == self.ID_TYPES.passport:
            next_state = "state_passport_country"
        else:
            next_state = "state_first_name"

        async def validate_identification_number(value):
            if idtype == self.ID_TYPES.rsa_id:
                try:
                    id_number = SAIDNumber(value)
                    dob = id_number.date_of_birth
                    if id_number.age > MAX_AGE - 100:
                        self.save_answer("state_dob_year", str(dob.year))
                    self.save_answer("state_dob_month", str(dob.month))
                    self.save_answer("state_dob_day", str(dob.day))
                    self.save_answer("state_gender", id_number.sex.value)
                except ValueError:
                    raise ErrorMessage(f"⚠️ Please enter a valid {idtype_label}")

        return FreeText(
            self,
            question="\n".join(
                [
                    "*VACCINE REGISTRATION SECURE CHAT* 🔐",
                    "",
                    f"Please TYPE in your {idtype_label}",
                ]
            ),
            next=next_state,
            check=validate_identification_number,
        )

    async def state_passport_country(self):
        return FreeText(
            self,
            question="\n".join(
                [
                    "*VACCINE REGISTRATION SECURE CHAT* 🔐",
                    "",
                    "Please TYPE in your passport's COUNTRY of origin.",
                    "Example _Zimbabwe_",
                ]
            ),
            next="state_passport_country_list",
        )

    async def state_passport_country_list(self):
        async def next_state(choice: Choice):
            if choice.value == "other":
                return "state_passport_country"
            return "state_first_name"

        search = self.user.answers["state_passport_country"] or ""
        choices = [
            Choice(country[0], country[1][:30])
            for country in countries.search_for_country(search)
        ]
        choices.append(Choice("other", "Other"))
        return ChoiceState(
            self,
            question="\n".join(
                [
                    "*VACCINE REGISTRATION SECURE CHAT* 🔐",
                    "",
                    "Please confirm your passport's COUNTRY of origin. REPLY with a "
                    "NUMBER from the list below:",
                ]
            ),
            choices=choices,
            error="Do any of these match your COUNTRY:",
            next=next_state,
        )

    async def state_first_name(self):

        return FreeText(
            self,
            question="\n".join(
                [
                    "*VACCINE REGISTRATION SECURE CHAT* 🔐",
                    "",
                    "Please TYPE your FIRST NAME as it appears in your identification "
                    "document.",
                ]
            ),
            next="state_surname",
        )

    async def state_surname(self):
        return FreeText(
            self,
            question="\n".join(
                [
                    "*VACCINE REGISTRATION SECURE CHAT* 🔐",
                    "",
                    "Please TYPE your SURNAME as it appears in your identification "
                    "document.",
                ]
            ),
            next="state_dob_year",
        )

    async def state_dob_year(self):
        if self.user.answers.get("state_dob_year"):
            return await self.go_to_state("state_dob_month")

        async def validate_dob_year(value):
            try:
                assert isinstance(value, str)
                assert value.isdigit()
                assert int(value) > date.today().year - MAX_AGE
                assert int(value) <= date.today().year
            except AssertionError:
                raise ErrorMessage(
                    "\n".join(
                        [
                            "⚠️  Please TYPE in only the YEAR you were born.",
                            "Example _1980_",
                        ]
                    )
                )

            idtype = self.user.answers["state_identification_type"]
            if idtype == self.ID_TYPES.rsa_id.value:
                idno = self.user.answers["state_identification_number"]
                if value[-2:] != idno[:2]:
                    raise ErrorMessage(
                        "The YEAR you have given does not match the YEAR of your ID "
                        "number. Please try again"
                    )

        return FreeText(
            self,
            question="\n".join(
                [
                    "*VACCINE REGISTRATION SECURE CHAT* 🔐",
                    "",
                    "Please TYPE in the YEAR you were born?",
                ]
            ),
            next="state_dob_month",
            check=validate_dob_year,
        )

    async def state_dob_month(self):
        if self.user.answers.get("state_dob_month"):
            return await self.go_to_state("state_dob_day")

        return ChoiceState(
            self,
            question="\n".join(
                [
                    "*VACCINE REGISTRATION SECURE CHAT* 🔐",
                    "",
                    "In which MONTH were you born?",
                ]
            ),
            choices=[
                Choice("1", "January"),
                Choice("2", "February"),
                Choice("3", "March"),
                Choice("4", "April"),
                Choice("5", "May"),
                Choice("6", "June"),
                Choice("7", "July"),
                Choice("8", "August"),
                Choice("9", "September"),
                Choice("10", "October"),
                Choice("11", "November"),
                Choice("12", "December"),
            ],
            next="state_dob_day",
            error="\n".join(
                [
                    "⚠️ This service works best when you reply with one of the numbers "
                    "next to the options provided.",
                    "",
                    "In which MONTH were you born? ",
                ]
            ),
        )

    async def state_dob_day(self):
        if self.user.answers.get("state_dob_day"):
            return await self.go_to_state("state_gender")

        async def validate_dob_day(value):
            dob_year = int(self.user.answers["state_dob_year"])
            dob_month = int(self.user.answers["state_dob_month"])
            try:
                assert isinstance(value, str)
                assert value.isdigit()
                date(dob_year, dob_month, int(value))
            except (AssertionError, ValueError, OverflowError):
                raise ErrorMessage(
                    "\n".join(
                        [
                            "⚠️ Please enter a valid calendar DAY for your birth date. "
                            "Type in only the day.",
                            "",
                            "Example: If you were born on 20 May, type _20_",
                        ]
                    )
                )

        return FreeText(
            self,
            question="\n".join(
                [
                    "*VACCINE REGISTRATION SECURE CHAT* 🔐",
                    "",
                    "Please TYPE the DAY of your birth date.",
                    "",
                    "Example: If you were born on 31 May, type _31_",
                ]
            ),
            next="state_gender",
            check=validate_dob_day,
        )

    async def state_gender(self):
        year = int(self.user.answers["state_dob_year"])
        month = int(self.user.answers["state_dob_month"])
        day = int(self.user.answers["state_dob_day"])
        age = calculate_age(date(year, month, day))
        if age < config.ELIGIBILITY_AGE_GATE_MIN:
            return await self.go_to_state("state_under_age_notification")

        if self.user.answers.get("state_gender"):
            return await self.go_to_state("state_self_registration")

        return ChoiceState(
            self,
            question="\n".join(
                ["*VACCINE REGISTRATION SECURE CHAT* 🔐", "", "What is your GENDER?"]
            ),
            choices=[
                Choice("Male", "Male"),
                Choice("Female", "Female"),
                Choice("Other", "Other"),
            ],
            error="\n".join(
                [
                    "⚠️ This service works best when you reply with one of the numbers "
                    "next to the options provided."
                    "",
                    "REPLY with the NUMBER next to your gender in the list below.",
                ]
            ),
            next="state_self_registration",
        )

    async def state_self_registration(self):
        number = display_phonenumber(self.inbound.from_addr)
        return MenuState(
            self,
            question="\n".join(
                [
                    "*VACCINE REGISTRATION SECURE CHAT* 🔐",
                    "",
                    "We will use your cell phone number to send you notifications and "
                    "updates via WhatsApp and/or SMS about getting vaccinated.",
                    "" f"Can we use {number}?",
                ]
            ),
            choices=[
                Choice("state_email_address", "Yes"),
                Choice("state_phone_number", "No"),
            ],
            error="\n".join(
                [
                    "⚠️ This service works best when you reply with one of the numbers "
                    "next to the options provided.",
                    "",
                    f"Please confirm that we can use {number} to contact you.",
                ]
            ),
        )

    async def state_phone_number(self):
        async def phone_number_validation(content):
            try:
                normalise_phonenumber(content)
            except ValueError:
                raise ErrorMessage(
                    "\n".join(
                        [
                            "⚠️ Please type a valid cell phone number.",
                            "Example _081234567_",
                        ]
                    )
                )

        return FreeText(
            self,
            question="\n".join(
                [
                    "*VACCINE REGISTRATION SECURE CHAT* 🔐",
                    "",
                    "Please TYPE the CELL PHONE NUMBER we can contact you on.",
                ]
            ),
            next="state_email_address",
            check=phone_number_validation,
        )

    async def state_email_address(self):
        async def email_validation(content):
            if content and content.lower() == "skip":
                return

            if parseaddr(content) == ("", ""):
                raise ErrorMessage(
                    "⚠️ Please TYPE a valid EMAIL address. (Or type SKIP if you are "
                    "unable to share an email address.)"
                )

        return FreeText(
            self,
            question="\n".join(
                [
                    "*VACCINE REGISTRATION SECURE CHAT* 🔐",
                    "",
                    "Please TYPE your EMAIL address. (Or type SKIP if you are unable "
                    "to share an email address.)",
                ]
            ),
            check=email_validation,
            next="state_medical_aid",
        )

    async def state_medical_aid(self):
        return MenuState(
            self,
            question="\n".join(
                [
                    "*VACCINE REGISTRATION SECURE CHAT* 🔐",
                    "",
                    "Do you belong to a Medical Aid?",
                ]
            ),
            choices=[
                Choice("state_medical_aid_search", "Yes"),
                Choice("state_vaccination_time", "No"),
            ],
            error="\n".join(
                [
                    "⚠️ This service works best when you reply with one of the numbers "
                    "next to the options provided.",
                    "",
                    "Please confirm if you belong to a Medical Aid.",
                ]
            ),
        )

    async def state_medical_aid_search(self):
        return FreeText(
            self,
            question="\n".join(
                [
                    "*VACCINE REGISTRATION SECURE CHAT* 🔐",
                    "",
                    "Please TYPE the name of your Medical Aid PROVIDER.",
                ]
            ),
            next="state_medical_aid_list",
        )

    async def state_medical_aid_list(self):
        async def next_state(choice: Choice):
            if choice.value == "other":
                return "state_medical_aid_search"
            return "state_medical_aid_number"

        search = self.user.answers["state_medical_aid_search"] or ""
        choices = [
            Choice(medical_aid[0], medical_aid[1][:100])
            for medical_aid in await medical_aids.search_for_scheme(search)
        ]
        choices.append(Choice("other", "None of these"))
        return ChoiceState(
            self,
            question="\n".join(
                [
                    "*VACCINE REGISTRATION SECURE CHAT* 🔐",
                    "",
                    "Please confirm your Medical Aid Provider. REPLY with a NUMBER "
                    "from the list below:",
                ]
            ),
            choices=choices,
            error="\n".join(
                [
                    "⚠️ This service works best when you reply with one of the numbers "
                    "next to the options provided.",
                    "",
                    "REPLY with the NUMBER next to the name of your "
                    "Medical Aid Provider:",
                ]
            ),
            next=next_state,
        )

    async def state_medical_aid_number(self):
        return FreeText(
            self,
            question="\n".join(
                [
                    "*VACCINE REGISTRATION SECURE CHAT* 🔐",
                    "",
                    "Please TYPE your Medical Aid NUMBER.",
                ]
            ),
            next="state_vaccination_time",
        )

    async def state_vaccination_time(self):
        return ChoiceState(
            self,
            question="\n".join(
                [
                    "*VACCINE REGISTRATION SECURE CHAT* 🔐",
                    "",
                    "Which option do you prefer for your vaccination appointment?",
                ]
            ),
            choices=[
                Choice("weekday_morning", "Weekday Morning"),
                Choice("weekday_afternoon", "Weekday Afternoon"),
                Choice("weekend_morning", "Weekend Morning"),
            ],
            error="\n".join(
                [
                    "⚠️ This service works best when you reply with one of the numbers "
                    "next to the options provided.",
                    "",
                    "When would you be available for a vaccination appointment?",
                ]
            ),
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
            "surname": self.user.answers["state_surname"],
            "firstName": self.user.answers["state_first_name"],
            "dateOfBirth": date_of_birth.isoformat(),
            "mobileNumber": normalise_phonenumber(phonenumber),
            "preferredVaccineScheduleTimeOfDay": vac_time,
            "preferredVaccineScheduleTimeOfWeek": vac_day,
            "preferredVaccineLocation": location,
            "residentialLocation": location,
            "termsAndConditionsAccepted": True,
            "medicalAidMember": self.user.answers["state_medical_aid"]
            == "state_medical_aid_search",
            "sourceId": "aeb8444d-cfa4-4c52-bfaf-eed1495124b7",
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
            data["passportCountry"] = self.user.answers["state_passport_country_list"]
        email_addr = self.user.answers["state_email_address"]
        if email_addr.lower() != "skip":
            data["emailAddress"] = email_addr
        if self.user.answers["state_medical_aid"] == "state_medical_aid_search":
            scheme_id = self.user.answers["state_medical_aid_list"]
            data["medicalAidScheme"] = {
                "value": scheme_id,
                "text": await medical_aids.scheme_name(scheme_id),
            }
            data["medicalAidSchemeNumber"] = self.user.answers[
                "state_medical_aid_number"
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
            "source": f"WhatsApp {self.inbound.to_addr}",
            "gender": self.user.answers["state_gender"],
            "first_name": self.user.answers["state_first_name"],
            "last_name": self.user.answers["state_surname"],
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
        if id_type == self.ID_TYPES.rsa_id.name:
            data["id_number"] = self.user.answers["state_identification_number"]
        if id_type == self.ID_TYPES.asylum_seeker.name:
            data["asylum_seeker_number"] = self.user.answers[
                "state_identification_number"
            ]
        if id_type == self.ID_TYPES.refugee.name:
            data["refugee_number"] = self.user.answers["state_identification_number"]
        if id_type == self.ID_TYPES.passport.name:
            data["passport_number"] = self.user.answers["state_identification_number"]
            data["passport_country"] = self.user.answers["state_passport_country"]

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
            text="\n".join(
                [
                    "*VACCINE REGISTRATION SECURE CHAT* 🔐",
                    "",
                    "Congratulations! You successfully registered with the National "
                    "Department of Health to get a COVID-19 vaccine.",
                    "",
                    "Look out for messages from this number (060 012 3456) on WhatsApp "
                    "OR on SMS/email. We will update you with important information "
                    "about your appointment and what to expect.",
                ]
            ),
        )

    async def state_err(self):
        return EndState(
            self,
            text="Something went wrong with your registration session. Your "
            "registration was not able to be processed. Please try again later",
        )
