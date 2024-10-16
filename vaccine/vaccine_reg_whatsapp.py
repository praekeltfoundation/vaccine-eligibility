import logging
import random
import re
from datetime import date
from email.utils import parseaddr
from enum import Enum
from typing import List
from urllib.parse import urljoin

import aiohttp
import sentry_sdk

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
    LanguageState,
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
    get_today,
    normalise_phonenumber,
)
from vaccine.validators import name_validator, nonempty_validator

logger = logging.getLogger(__name__)

EXIT_KEYWORDS = {"menu", "0", "support"}


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
    START_STATE = "state_language"

    def __init__(self, user, worker=None):
        super().__init__(user, worker)

        class ID_TYPES(Enum):
            rsa_id = self._("RSA ID Number / RSA Birth Certificate")
            passport = self._("Passport Number")
            asylum_seeker = self._("Asylum Seeker Permit number")
            refugee = self._("Refugee Permit number")

        self.ID_TYPES = ID_TYPES

    async def process_message(self, message: Message) -> List[Message]:
        if message.session_event == Message.SESSION_EVENT.CLOSE:
            self.state_name = "state_timeout"
        if re.sub(r"\W+", " ", message.content or "").strip().lower() in EXIT_KEYWORDS:
            self.state_name = "state_exit"

        return await super().process_message(message)

    async def state_timeout(self):
        return EndState(
            self,
            text=self._(
                "*VACCINE REGISTRATION SECURE CHAT* 🔐\n"
                "\n"
                "We haven’t heard from you in a while!\n"
                "\n"
                "The registration session has timed out due to inactivity. You "
                "will need to start again. Just TYPE the word *REGISTER*.\n"
                "\n"
                "-----\n"
                "Reply *SUPPORT* for details on how to get help with your "
                "registration\n"
                "📌 Reply *0* to return to the main *MENU*"
            ),
        )

    async def state_exit(self):
        return EndState(self, "", helper_metadata={"automation_handle": True})

    async def state_language(self):
        self.user.answers = {}

        if random.random() < config.THROTTLE_PERCENTAGE / 100.0:
            return await self.go_to_state("state_throttle")

        return LanguageState(
            self,
            question="*VACCINE REGISTRATION SECURE CHAT* 🔐\n"
            "\n"
            "Welcome to the official COVID-19 Vaccination Self-registration service "
            "from the National Department of Health.\n"
            "\n"
            "If your language is not available, register by calling 0800 029 999, "
            "toll-free (Monday - Friday: 7am to 8pm OR Saturday, Sunday and public "
            "holidays: 8am to 6pm)\n"
            "\n"
            "To continue, select your language from the list:\n",
            error="*VACCINE REGISTRATION SECURE CHAT* 🔐\n"
            "\n"
            "Please choose your language from this list:\n"
            "\n",
            choices=[
                Choice("eng", "English"),
                Choice("zul", "isiZulu"),
                Choice("xho", "isiXhosa"),
                Choice("afr", "Afrikaans"),
                Choice("sot", "Sesotho"),
            ],
            next="state_age_gate",
        )

    async def state_age_gate(self):
        return ChoiceState(
            self,
            question=self._(
                "*VACCINE REGISTRATION SECURE CHAT* 🔐\n"
                "\n"
                "Welcome to the official COVID-19 Vaccination Registration Portal from "
                "the National Department of Health. Registration will take about 5 "
                "minutes. Please have your Birth Certificate, ID, Passport, Refugee "
                "Permit or Asylum Seeker Permit *Number* on hand. If you have Medical "
                "Aid, we will also ask for your Medical Aid Number.\n"
                "\n"
                "*Note:*\n"
                "- Vaccination is voluntary and no payment is required\n"
                "- No co-payment/levy will be required if you belong to a Medical Aid\n"
                "- Everyone who registers will be offered vaccination\n"
                "\n"
                "*Important*\n"
                "👉 *Self* registration is available to those aged 18 and over\n"
                "👉 For children aged 5-17, registration must be completed by someone "
                "who can legally make decisions on behalf of the child.\n"
                "\n"
            ),
            error=self._(
                "⚠️ This service works best when you use the numbered options "
                "available\n"
                "\n"
                "Please confirm the type of registration"
            ),
            error_footer=self._(
                "\n"
                "-----\n"
                "Or reply 📌 *0* to end this session and return to the main *MENU*"
            ),
            choices=[
                Choice("18+", self._("18+ Self registration")),
                Choice("5-17", self._("Register on behalf of a child aged 5-17")),
            ],
            next="state_terms_pdf",
        )

    async def state_throttle(self):
        return EndState(
            self,
            text=self._(
                "*VACCINE REGISTRATION SECURE CHAT* 🔐\n"
                "\n"
                "⚠️ We are currently experiencing high volumes of registrations.\n"
                "\n"
                "Your registration is important! Please try again in 15 minutes.\n"
                "\n"
                "-----\n"
                "Reply *SUPPORT* for details on how to get help with your "
                "registration\n"
                "📌 Reply *0* to return to the main *MENU*"
            ),
            next=self.START_STATE,
        )

    async def state_under_age_notification(self):
        return ChoiceState(
            self,
            question=self._(
                "Self-registration is only available to people {minimum_age} years or "
                "older.\n"
                "\n"
                "Can we contact you on this number when this changes?\n"
            ).format(minimum_age=config.ELIGIBILITY_AGE_GATE_MIN),
            choices=[Choice("yes", self._("Yes")), Choice("no", self._("No"))],
            footer=self._("\n" "REPLY with the NUMBER of the option you have chosen."),
            error=self._(
                "⚠️ This service works best when you use the numbered options "
                "available.\n"
                "\n"
                "Please let us know if we can notify you via Whatsapp on this "
                "number when updates about getting vaccinated become available?\n"
            ),
            error_footer=self._(
                "\n"
                "-----\n"
                "Reply *SUPPORT* for details on how to get help with your "
                "registration\n"
                "Reply 📌 *0* to end this session and return to the main *MENU*"
            ),
            next="state_confirm_notification",
        )

    async def state_confirm_notification(self):
        return EndState(self, text=self._("Thank you for confirming"))

    async def state_terms_pdf(self):
        self.messages.append(
            self.inbound.reply(
                None,
                helper_metadata={
                    "document": "https://healthcheck-images-rasa.s3.af-south-1.amazonaw"
                    "s.com/ELECTRONIC+VACCINATION+DATA+SYSTEM+(EVDS)+%E2%80%93+DATA+PRO"
                    "TECTION+%26+PRIVACY+POLICY+(WhatsApp)_Updated+20+April+2023.pdf"
                },
            )
        )
        return await self.go_to_state("state_terms_and_conditions")

    async def state_terms_and_conditions(self):
        question = self._(
            "*VACCINE REGISTRATION SECURE CHAT* 🔐\n"
            "\n"
            "Do you agree to the attached Electronic Vaccine Data System "
            "PRIVACY POLICY that explains how your data is used and protected?\n"
        )
        if self.user.answers.get("state_age_gate") == "5-17":
            question = self._(
                "*VACCINE REGISTRATION SECURE CHAT* 🔐\n"
                "\n"
                "If you are using this service on behalf of a child to register for a "
                "COVID-19 vaccination as a competent person, you need to confirm that "
                "you are sharing the child's information in line with the Electronic "
                "Vaccine Data System Privacy Policy.\n"
                "\n"
                "The POPI Act says that a competent person is someone who is legally "
                "competent to make decisions on behalf of a child.\n"
                "\n"
                "Please confirm that you consent to the attached Electronic Vaccine "
                "Data System PRIVACY POLICY that explains how all data is used and "
                "protected *on behalf of the child*?\n"
                "\n"
            )
        return MenuState(
            self,
            question=question,
            choices=[
                Choice("state_terms_and_conditions_summary", self._("Read summary")),
                Choice("state_identification_type", self._("Accept")),
            ],
            error=self._(
                "⚠️ This service works best when you reply with one of the numbers "
                "next to the options provided.\n"
            ),
            error_footer=self._(
                "\n"
                "Reply 1 to read a summary of the DATA PROTECTION & PRIVACY POLICY. "
                "Reply 2 to accept"
            ),
        )

    async def state_terms_and_conditions_summary(self):
        return MenuState(
            self,
            question=self._(
                "*VACCINE REGISTRATION SECURE CHAT* 🔐\n"
                "\n"
                "*Electronic Vaccine Data System DATA PROTECTION & PRIVACY POLICY "
                "(“EVDS Privacy Policy) SUMMARY*\n"
                "\n"
                "The EVDS Privacy Policy complies with the POPI Act.\n"
                "\n"
                "Your personal data including: contact, medical aid & vaccine "
                "protocol details are processed with your consent for the agreed "
                "purpose (to support the COVID-19 Vaccination roll out in South "
                "Africa) and remain confidential.\n"
                "\n"
                "EVDS uses your data to check your eligibility & inform you of the "
                "date & venue of your vaccination.\n"
                "\n"
                "Registration is voluntary & does not guarantee vaccination.\n"
                "\n"
                "All security measures have been taken to keep your information "
                "safe. No personal data will be transferred from EVDS without "
                "legislative authorisation in compliance with the Popi Act.\n"
                "\n"
                "Do you accept the EVDS Privacy Notice?\n"
            ),
            choices=[
                Choice("state_identification_type", self._("Yes, I accept")),
                Choice("state_no_terms", self._("No")),
            ],
            error=self._(
                "⚠️ This service works best when you reply with one of the numbers "
                "next to the options provided.\n"
                "\n"
                "Do you accept the EVDS Privacy Notice?\n"
            ),
            error_footer=self._(
                "\n"
                "------\n"
                "📌 Or reply *0* to end this session and return to the main *MENU*"
            ),
        )

    async def state_no_terms(self):
        return EndState(
            self,
            text=self._(
                "*VACCINE REGISTRATION SECURE CHAT* 🔐\n"
                "\n"
                "Thank you. If you change your mind, type *REGISTER* to restart "
                "your registration session"
            ),
        )

    async def state_province_id(self):
        return ChoiceState(
            self,
            question=self._(
                "*VACCINE REGISTRATION SECURE CHAT* 🔐\n"
                "\n"
                "We need your location to help us allocate you to an available "
                "vaccination site as close and as soon as possible\n"
                "\n"
                "Select your province"
            ),
            choices=[Choice(*province) for province in await suburbs.provinces()],
            error=self._("Reply with a NUMBER:"),
            next="state_suburb_search",
        )

    async def state_province_no_results(self):
        async def next_(choice: Choice):
            self.save_answer("state_province_id", choice.value)
            return "state_suburb_search"

        return ChoiceState(
            self,
            question=self._(
                "*VACCINE REGISTRATION SECURE CHAT* 🔐\n"
                "\n"
                "⚠️ Your suburb could not be found. Please try again by selecting your "
                "province. Reply *SUPPORT* anytime if you need help from the "
                "📞 Hotline Team\n"
                "\n"
                "Select your province"
            ),
            choices=[Choice(*province) for province in await suburbs.provinces()],
            error=self._("Reply with a NUMBER:"),
            next=next_,
        )

    async def state_suburb_search(self):
        return FreeText(
            self,
            question=self._(
                "*VACCINE REGISTRATION SECURE CHAT* 🔐\n"
                "\n"
                "Please TYPE the name of the SUBURB where you want to get "
                "vaccinated"
            ),
            next="state_municipality",
        )

    async def state_municipality(self):
        province = self.user.answers["state_province_id"]
        search = self.user.answers["state_suburb_search"] or ""
        required, results = await suburbs.search(province, search, m_limit=10)
        if not required:
            return await self.go_to_state("state_suburb")

        async def next_state(choice: Choice):
            if choice.value == "other":
                return "state_suburb_search"
            return "state_suburb"

        choices = [Choice(k, v[:200]) for k, v in results]
        choices = enforce_character_limit_in_choices(choices, 1000)
        choices.append(Choice("other", "Other"))

        return ChoiceState(
            self,
            question=self._(
                "*VACCINE REGISTRATION SECURE CHAT* 🔐\n"
                "\n"
                "Please confirm the MUNICIPALITY for the suburb you have given:\n"
            ),
            choices=choices,
            error=self._(
                "⚠️ This service works best when you reply with one of the numbers "
                "next to the options provided.\n"
                "\n"
                "Please REPLY with a NUMBER from the list below to confirm "
                "municipality of the suburb you have shared:\n"
            ),
            error_footer=self._(
                "\n"
                "------\n"
                "📌 Or reply *0* to end this session and return to the main *MENU*\n"
                "Reply *SUPPORT* anytime if you need help from the 📞 Hotline Team"
            ),
            next=next_state,
        )

    async def state_suburb(self):
        async def next_state(choice: Choice):
            if choice.value == "other":
                return "state_province_id"
            return "state_self_registration"

        province = self.user.answers["state_province_id"]
        search = self.user.answers["state_suburb_search"] or ""
        municipality = self.user.answers.get("state_municipality")
        _, results = await suburbs.search(province, search, municipality, m_limit=10)

        if len(results) == 0:
            return await self.go_to_state("state_province_no_results")

        choices = [Choice(suburb[0], suburb[1][:200]) for suburb in results]
        choices = enforce_character_limit_in_choices(choices, 1000)
        choices.append(Choice("other", "Other"))
        return ChoiceState(
            self,
            question=self._(
                "*VACCINE REGISTRATION SECURE CHAT* 🔐\n"
                "\n"
                "Please REPLY with a NUMBER to confirm your location:\n"
            ),
            choices=choices,
            error=self._(
                "⚠️ This service works best when you reply with one of the numbers "
                "next to the options provided.\n"
                "\n"
                "Please REPLY with a NUMBER from the list below to confirm the "
                "location you have shared:\n"
            ),
            error_footer=self._(
                "\n"
                "------\n"
                "📌 Or reply *0* to end this session and return to the main *MENU*\n"
                "Reply *SUPPORT* anytime if you need help from the 📞 Hotline Team"
            ),
            next=next_state,
        )

    async def state_identification_type(self):
        return ChoiceState(
            self,
            question=self._(
                "*VACCINE REGISTRATION SECURE CHAT* 🔐\n"
                "\n"
                "Which method would you like to use for identification?\n"
            ),
            choices=[Choice(i.name, i.value) for i in self.ID_TYPES],
            error=self._(
                "⚠️ This service works best when you reply with one of the numbers "
                "next to the options provided.\n"
                "\n"
                "Please choose the type of identification document you have from "
                "the list below?\n"
            ),
            error_footer=self._(
                "\n"
                "-------\n"
                "If you experiencing any problems with your registration, reply "
                "*SUPPORT* now to get help from the 📞 Hotline Team"
            ),
            next="state_identification_number",
        )

    async def state_identification_number(self):
        idtype = self.ID_TYPES[self.user.answers["state_identification_type"]]
        idtype_label = idtype.value

        async def validate_identification_number(value):
            error_msg = self._(
                "⚠️ Please enter a valid {id_type}\n"
                "\n"
                "📌 Or reply *0* to end this session and return to the main *MENU*\n"
                "Reply *SUPPORT* anytime if you need help from the 📞 Hotline Team"
            ).format(id_type=idtype_label)
            if idtype == self.ID_TYPES.rsa_id:
                try:
                    SAIDNumber(value)
                except ValueError as ve:
                    raise ErrorMessage(error_msg) from ve
            else:
                await nonempty_validator(error_msg)(value)

        return FreeText(
            self,
            question=self._(
                "*VACCINE REGISTRATION SECURE CHAT* 🔐\n"
                "\n"
                "Please TYPE in your {id_type}"
            ).format(id_type=idtype_label),
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
                        "*VACCINE REGISTRATION SECURE CHAT* 🔐\n"
                        "\n"
                        "The number you have entered appears to be a RSA ID Number/RSA "
                        "Birth Certificate ID Number. Is this correct?\n"
                    ),
                    choices=[
                        Choice("state_change_to_rsa_id", self._("Yes")),
                        Choice("state_identification_type", self._("No")),
                    ],
                    error=self._(
                        "Please try again\n"
                        "\n"
                        "Please confirm that the number you have entered is a RSA ID "
                        "Number/RSA Birth Certificate ID Number"
                    ),
                )
        except ValueError:
            pass

        if idtype == self.ID_TYPES.passport:
            next_state = "state_passport_country"
        else:
            next_state = "state_first_name"
        return await self.go_to_state(next_state)

    async def state_change_to_rsa_id(self):
        self.save_answer("state_identification_type", self.ID_TYPES.rsa_id.name)
        return await self.go_to_state("state_first_name")

    async def state_passport_country(self):
        return FreeText(
            self,
            question=self._(
                "*VACCINE REGISTRATION SECURE CHAT* 🔐\n"
                "\n"
                "Please TYPE in your passport's COUNTRY of origin.\n"
                "Example _Zimbabwe_"
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
        choices.append(Choice("other", self._("Other")))
        return ChoiceState(
            self,
            question=self._(
                "*VACCINE REGISTRATION SECURE CHAT* 🔐\n"
                "Please confirm your passport's COUNTRY of origin.\n"
                "\n"
                "REPLY with a NUMBER from the list below:"
            ),
            choices=choices,
            error=self._("Do any of these match your COUNTRY:"),
            next=next_state,
        )

    async def state_first_name(self):
        question = self._(
            "*VACCINE REGISTRATION SECURE CHAT* 🔐\n"
            "\n"
            "Please TYPE your FIRST NAME as it appears in your identification document."
        )

        error = self._(
            "⚠️ Please try again\n"
            "\n"
            "TYPE your FIRST NAME as it appears in your identification document.\n"
            "\n"
            "-------\n"
            "📌 Or reply *0* to end this session and return to the main *MENU*\n"
            "If you experiencing any problems with your registration, reply *SUPPORT* "
            "now to get help from the 📞 Hotline Team"
        )
        return FreeText(
            self, question=question, check=name_validator(error), next="state_surname"
        )

    async def state_surname(self):
        question = self._(
            "*VACCINE REGISTRATION SECURE CHAT* 🔐\n"
            "\n"
            "Please TYPE your SURNAME as it appears in your identification "
            "document."
        )
        error = self._(
            "⚠️ Please try again\n"
            "\n"
            "TYPE your SURNAME as it appears in your identification document.\n"
            "\n"
            "-------\n"
            "If you experiencing any problems with your registration, reply *SUPPORT* "
            "now to get help from the 📞 Hotline Team\n"
            "📌 Or reply *0* to end this session and return to the main *MENU*"
        )

        return FreeText(
            self,
            question=question,
            check=name_validator(error),
            next="state_confirm_profile",
        )

    async def state_confirm_profile(self):
        first_name = clean_name(self.user.answers["state_first_name"])[:200]
        surname = clean_name(self.user.answers["state_surname"])[:200]
        id_number = self.user.answers["state_identification_number"][:200]
        return MenuState(
            self,
            question=self._(
                "*VACCINE REGISTRATION SECURE CHAT* 🔐\n"
                "\n"
                "Please confirm the following:\n"
                "\n"
                "{first_name} {surname}\n"
                "{id_number}\n"
            ).format(first_name=first_name, surname=surname, id_number=id_number),
            choices=[
                Choice("state_dob_year", self._("Correct")),
                Choice("state_identification_type", self._("Wrong")),
            ],
            error=self._(
                "Is the information you shared correct?\n"
                "\n"
                "{first_name} {surname}\n"
                "{id_number}"
            ).format(first_name=first_name, surname=surname, id_number=id_number),
        )

    async def state_dob_year(self):
        idtype = self.ID_TYPES[self.user.answers["state_identification_type"]]
        if idtype == self.ID_TYPES.rsa_id:
            id_number = SAIDNumber(self.user.answers["state_identification_number"])
            if id_number.age > config.AMBIGUOUS_MAX_AGE - 100:
                self.save_answer("state_dob_year", str(id_number.date_of_birth.year))

        if self.user.answers.get("state_dob_year"):
            return await self.go_to_state("state_dob_month")

        async def validate_dob_year(value):
            try:
                assert isinstance(value, str)
                assert value.isdigit()
                assert int(value) > get_today().year - config.AMBIGUOUS_MAX_AGE
                assert int(value) <= get_today().year
            except AssertionError as e:
                raise ErrorMessage(
                    self._(
                        "⚠️  Please TYPE in only the YEAR you were born.\n"
                        "Example _1980_"
                    )
                ) from e

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
                "*VACCINE REGISTRATION SECURE CHAT* 🔐\n"
                "\n"
                "Please TYPE in the YEAR you were born?"
            ),
            next="state_dob_month",
            check=validate_dob_year,
        )

    async def state_dob_month(self):
        idtype = self.ID_TYPES[self.user.answers["state_identification_type"]]
        if idtype == self.ID_TYPES.rsa_id:
            id_number = SAIDNumber(self.user.answers["state_identification_number"])
            self.save_answer("state_dob_month", str(id_number.date_of_birth.month))

        if self.user.answers.get("state_dob_month"):
            return await self.go_to_state("state_dob_day")

        return ChoiceState(
            self,
            question=self._(
                "*VACCINE REGISTRATION SECURE CHAT* 🔐\n"
                "\n"
                "In which MONTH were you born?\n"
            ),
            choices=[
                Choice("1", self._("January")),
                Choice("2", self._("February")),
                Choice("3", self._("March")),
                Choice("4", self._("April")),
                Choice("5", self._("May")),
                Choice("6", self._("June")),
                Choice("7", self._("July")),
                Choice("8", self._("August")),
                Choice("9", self._("September")),
                Choice("10", self._("October")),
                Choice("11", self._("November")),
                Choice("12", self._("December")),
            ],
            next="state_dob_day",
            error=self._(
                "⚠️ This service works best when you reply with one of the numbers "
                "next to the options provided. Reply *SUPPORT* anytime if you need "
                "help from the 📞 Hotline Team\n"
                "\n"
                "In which MONTH were you born?\n"
            ),
            error_footer=self._("\n" "Reply with the number next to the month."),
        )

    async def state_dob_day(self):
        idtype = self.ID_TYPES[self.user.answers["state_identification_type"]]
        if idtype == self.ID_TYPES.rsa_id:
            id_number = SAIDNumber(self.user.answers["state_identification_number"])
            self.save_answer("state_dob_day", str(id_number.date_of_birth.day))

        if self.user.answers.get("state_dob_day"):
            return await self.go_to_state("state_gender")

        async def validate_dob_day(value):
            dob_year = int(self.user.answers["state_dob_year"])
            dob_month = int(self.user.answers["state_dob_month"])
            try:
                assert isinstance(value, str)
                assert value.isdigit()
                date(dob_year, dob_month, int(value))
            except (AssertionError, ValueError, OverflowError) as e:
                raise ErrorMessage(
                    self._(
                        "⚠️ Please enter a valid calendar DAY for your birth date. "
                        "Type in only the day.\n"
                        "\n"
                        "Example: If you were born on 20 May, type _20_\n"
                        "\n"
                        "-------\n"
                        "If you experiencing any problems with your registration, "
                        "reply *SUPPORT* now to get help from the 📞 Hotline Team\n"
                        "📌 Or reply *0* to end this session and return to the main "
                        "*MENU*"
                    )
                ) from e

        return FreeText(
            self,
            question=self._(
                "*VACCINE REGISTRATION SECURE CHAT* 🔐\n"
                "\n"
                "Please TYPE the DAY of your birth date.\n"
                "\n"
                "Example: If you were born on 31 May, type _31_"
            ),
            next="state_gender",
            check=validate_dob_day,
        )

    async def state_gender(self):
        idtype = self.ID_TYPES[self.user.answers["state_identification_type"]]
        if idtype == self.ID_TYPES.rsa_id:
            id_number = SAIDNumber(self.user.answers["state_identification_number"])
            self.save_answer("state_gender", id_number.sex.value)

        year = int(self.user.answers["state_dob_year"])
        month = int(self.user.answers["state_dob_month"])
        day = int(self.user.answers["state_dob_day"])
        age = calculate_age(date(year, month, day))
        if age < config.ELIGIBILITY_AGE_GATE_MIN:
            return await self.go_to_state("state_under_age_notification")

        if self.user.answers.get("state_gender"):
            return await self.go_to_state("state_province_id")

        return ChoiceState(
            self,
            question=self._(
                "*VACCINE REGISTRATION SECURE CHAT* 🔐\n" "\n" "What is your GENDER?\n"
            ),
            choices=[
                Choice("Male", self._("Male")),
                Choice("Female", self._("Female")),
                Choice("Other", self._("Other")),
            ],
            error=self._(
                "⚠️ This service works best when you reply with one of the numbers "
                "next to the options provided. If you experiencing any problems with "
                "your registration, reply *SUPPORT* now to get help from the "
                "📞 Hotline Team\n"
                "\n"
                "REPLY with the NUMBER next to your gender in the list below.\n"
            ),
            next="state_province_id",
        )

    async def state_self_registration(self):
        number = display_phonenumber(f"+{self.inbound.from_addr.lstrip('+')}")
        return MenuState(
            self,
            question=self._(
                "*VACCINE REGISTRATION SECURE CHAT* 🔐\n"
                "\n"
                "We will use your mobile phone number to send you notifications and "
                "updates via WhatsApp and/or SMS about getting vaccinated.\n"
                "\n"
                "Can we use {number}?"
            ).format(number=number),
            choices=[
                Choice("state_email_address", self._("Yes")),
                Choice("state_phone_number", self._("No")),
            ],
            error=self._(
                "⚠️ This service works best when you reply with one of the numbers "
                "next to the options provided.\n"
                "\n"
                "Please confirm that we can use {number} to contact you.\n"
            ).format(number=number),
        )

    async def state_phone_number(self):
        async def phone_number_validation(content):
            try:
                normalise_phonenumber(content)
            except ValueError as ve:
                raise ErrorMessage(
                    self._(
                        "⚠️ Please type a valid cell phone number.\n"
                        "Example _081234567_"
                    )
                ) from ve

        return FreeText(
            self,
            question=self._(
                "*VACCINE REGISTRATION SECURE CHAT* 🔐\n"
                "\n"
                "Please TYPE the MOBILE PHONE NUMBER we can contact you on."
            ),
            next="state_email_address",
            check=phone_number_validation,
        )

    async def state_email_address(self):
        async def email_validation(content):
            if content and content.lower() == "skip":
                return

            realname, email_address = parseaddr(content)
            if (realname, email_address) == ("", "") or "@" not in email_address:
                raise ErrorMessage(
                    self._(
                        "⚠️ Please TYPE a valid EMAIL address. (Or type SKIP if you "
                        "are unable to share an email address.)"
                    )
                )

        return FreeText(
            self,
            question=self._(
                "*VACCINE REGISTRATION SECURE CHAT* 🔐\n"
                "\n"
                "Please TYPE your EMAIL address. (Or type SKIP if you are unable "
                "to share an email address.)"
            ),
            check=email_validation,
            next="state_medical_aid",
        )

    async def state_medical_aid(self):
        return MenuState(
            self,
            question=self._(
                "*VACCINE REGISTRATION SECURE CHAT* 🔐\n"
                "\n"
                "Note: If you belong to a Medical Aid, your day-to-day savings and/or "
                "benefits won't be affected.\n"
                "\n"
                "Do you belong to a South African Medical Aid?\n"
            ),
            choices=[
                Choice("state_medical_aid_search", self._("Yes")),
                Choice("state_vaccination_time", self._("No")),
            ],
            error=self._(
                "⚠️ This service works best when you reply with one of the numbers "
                "next to the options provided.\n"
                "\n"
                "Please confirm if you belong to a Medical Aid.\n"
            ),
        )

    async def state_medical_aid_search(self):
        return FreeText(
            self,
            question=self._(
                "*VACCINE REGISTRATION SECURE CHAT* 🔐\n"
                "\n"
                "Please TYPE the name of your Medical Aid PROVIDER."
            ),
            next="state_medical_aid_list",
        )

    async def state_medical_aid_list(self):
        async def next_state(choice: Choice):
            if choice.value == "other":
                return "state_medical_aid"
            return "state_medical_aid_number"

        search = self.user.answers["state_medical_aid_search"] or ""
        choices = [
            Choice(medical_aid[0], medical_aid[1][:100])
            for medical_aid in await medical_aids.search_for_scheme(search)
        ]
        choices.append(Choice("other", self._("None of these")))
        return ChoiceState(
            self,
            question=self._(
                "*VACCINE REGISTRATION SECURE CHAT* 🔐\n"
                "\n"
                "Please confirm your Medical Aid Provider. REPLY with a NUMBER "
                "from the list below:\n"
            ),
            choices=choices,
            error=self._(
                "⚠️ This service works best when you reply with one of the numbers "
                "next to the options provided. Reply *SUPPORT* anytime if you need "
                "help from the 📞 Hotline Team"
                "\n"
                "REPLY with the NUMBER next to the name of your Medical Aid Provider:\n"
            ),
            error_footer=self._(
                "\n" "📌 Or reply *0* to end this session and return to the main *MENU*"
            ),
            next=next_state,
        )

    async def state_medical_aid_number(self):
        question = self._(
            "*VACCINE REGISTRATION SECURE CHAT* 🔐\n"
            "\n"
            "Please TYPE your Medical Aid NUMBER."
        )
        error = self._(
            "⚠️ Please try again\n"
            "\n"
            "Reply with your Medical Aid NUMBER\n"
            "\n"
            "📌 Or reply *0* to end this session and return to the main *MENU*"
        )

        return FreeText(
            self,
            question=question,
            check=nonempty_validator(error),
            next="state_vaccination_time",
        )

    async def state_vaccination_time(self):
        return ChoiceState(
            self,
            question=self._(
                "*VACCINE REGISTRATION SECURE CHAT* 🔐\n"
                "\n"
                "Note: We will try to allocate you an appointment based on your "
                "preference.\n"
                "Which option do you prefer for your vaccination appointment?\n"
            ),
            choices=[
                Choice("weekday_morning", self._("Weekday Morning")),
                Choice("weekday_afternoon", self._("Weekday Afternoon")),
                Choice("weekend_morning", self._("Weekend Morning")),
            ],
            error=self._(
                "⚠️ This service works best when you reply with one of the numbers "
                "next to the options provided.\n"
                "\n"
                "When would you be available for a vaccination appointment?\n"
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
            "state_phone_number", f"+{self.inbound.from_addr.lstrip('+')}"
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
            "medicalAidMember": self.user.answers["state_medical_aid"]
            == "state_medical_aid_search",
            "sourceId": "aeb8444d-cfa4-4c52-bfaf-eed1495124b7",
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
            "state_phone_number", f"+{self.inbound.from_addr.lstrip('+')}"
        )

        data = {
            "msisdn": normalise_phonenumber(phonenumber),
            "source": f"WhatsApp {self.inbound.to_addr}",
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
            data["passport_country"] = self.user.answers["state_passport_country_list"]

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
                "*VACCINE REGISTRATION SECURE CHAT* 🔐\n"
                "\n"
                "Congratulations! You successfully registered with the National "
                "Department of Health to get a COVID-19 vaccine.\n"
                "\n"
                "Look out for messages from this number (060 012 3456) on WhatsApp "
                "OR on SMS/email. We will update you with important information "
                "about your appointment and what to expect.\n"
                "\n"
                "-----\n"
                "📌 Reply *0* to return to the main *MENU*"
            ),
        )

    async def state_err(self):
        return EndState(
            self,
            text=self._(
                "*VACCINE REGISTRATION SECURE CHAT* 🔐\n"
                "\n"
                "⚠️ Our portal is currently down.\n"
                "\n"
                "Your registration is important! Please try again in 1 hour.\n"
                "\n"
                "-----\n"
                "📌 Reply *0* to return to the main *MENU*"
            ),
        )
