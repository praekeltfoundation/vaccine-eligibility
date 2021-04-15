from datetime import date
from enum import Enum

from vaccine.base_application import BaseApplication
from vaccine.states import (
    Choice,
    ChoiceState,
    EndState,
    ErrorMessage,
    FreeText,
    MenuState,
)
from vaccine.utils import luhn_checksum

MAX_AGE = 122


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
                    "Are you 40 years or older?",
                ]
            ),
            choices=[
                Choice("state_identification_type", "Yes"),
                Choice("state_under40_notification", "No"),
            ],
            error="Self-registration is currently only available to those 40 years of "
            "age or older. Please tell us if you are 40 or older?",
        )

    async def state_under40_notification(self):
        return ChoiceState(
            self,
            question="Self-registration is only available to people 40 years or older. "
            "Can we SMS you on this number when this changes?",
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
        idtype = self.ID_TYPES[self.user.answers["state_identification_type"]]
        idtype_label = idtype.value

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
            next="state_gender",
            check=validate_identification_number,
        )

    async def state_gender(self):
        return ChoiceState(
            self,
            question="What is your gender?",
            choices=[
                Choice("male", "Male"),
                Choice("female", "Female"),
                Choice("other", "Other"),
                Choice("unknown", "Unknown"),
            ],
            error="Please select your gender using one of the numbers below",
            next="state_dob_year",
        )

    async def state_dob_year(self):
        async def validate_dob_year(value):
            try:
                assert isinstance(value, str)
                assert value.isdigit()
                assert int(value) > date.today().year - MAX_AGE
                assert int(value) <= date.today().year
            except AssertionError:
                raise ErrorMessage(
                    "REQUIRED: Please TYPE the 4 digits of the year you were born "
                    "(Example: 1980)"
                )

        return FreeText(
            self,
            question="Date of birth: In which year were you born? (Please type just "
            "the year)",
            next="state_dob_month",
            check=validate_dob_year,
        )

    async def state_dob_month(self):
        return ChoiceState(
            self,
            question="Date of birth: In which month were you born?",
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
            error="REQUIRED: Choose your birthday month using the numbers below:",
        )

    async def state_dob_day(self):
        # TODO: stop <40 year olds from continuing
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
            question="Date of birth: On which day of the month were you born? (Please "
            "type just the day)",
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
        first_name = self.user.answers["state_first_name"][:38]
        surname = self.user.answers["state_surname"][:38]
        id_number = self.user.answers["state_identification_number"][:28]
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
        # TODO: Change this to use the EVDS UUIDs for province selection
        return ChoiceState(
            self,
            question="Select Your Province",
            choices=[
                Choice("ec", "Eastern Cape"),
                Choice("fs", "Free State"),
                Choice("gp", "Gauteng"),
                Choice("kzn", "Kwazulu Natal"),
                Choice("lp", "Limpopo"),
                Choice("mp", "Mpumalanga"),
                Choice("nw", "North West"),
                Choice("nc", "Northern Cape"),
                Choice("wc", "Western Cape"),
            ],
            error="Reply with a NUMBER:",
            next="state_suburb_search",
        )

    async def state_suburb_search(self):
        return FreeText(
            self,
            question="Please type the name of the SUBURB where you live.",
            next="state_suburb",
        )

    async def state_suburb(self):
        # TODO: Implement suburb search
        async def next_state(choice: Choice):
            if choice.value == "other":
                return "state_province"
            return "state_self_registration"

        return ChoiceState(
            self,
            question="Please choose the best match for your location:",
            choices=[
                Choice("suburb1", "Municipality, Suburb 1"),
                Choice("suburb2", "Municipality, Suburb 2"),
                Choice("suburb3", "Municipality, Suburb 3"),
                Choice("other", "Other"),
            ],
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
            question="Please type a CELL NUMBER we can send an SMS to with your "
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
            question="Do you belong to a Medical Aid Scheme?",
            choices=[Choice("yes", "Yes"), Choice("no", "No")],
            error="ERROR: Please try again. Do you belong to a Medical Aid Scheme?",
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
            choices=[Choice("state_success", "ACCEPT")],
            error="TYPE 1 to ACCEPT our terms and conditions",
        )

    async def state_success(self):
        # TODO: Submit to EVDS
        return EndState(
            self,
            text=":) You have SUCCESSFULLY registered to get vaccinated. Additional "
            "information and appointment details will be sent via SMS.",
            next=self.START_STATE,
        )
