from datetime import date
from vaccine.base_application import BaseApplication
from vaccine.states import (
    Choice,
    MenuState,
    ChoiceState,
    EndState,
    FreeText,
    ErrorMessage,
)
from enum import Enum
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
                    "The SA Department of Health thanks you for helping to defeat the "
                    "coronavirus!",
                    "",
                    "Are you 40 years or older?",
                ]
            ),
            choices=[
                Choice("state_identification_type", "Yes"),
                Choice("state_under40_notification", "No"),
            ],
            error="Self registration is currently only available to those 40 years or "
            "older. Please tell us if you are 40 years of age or older?",
        )

    async def state_under40_notification(self):
        return ChoiceState(
            self,
            question="Self registration is only available to those 40 years or older. "
            "Can we notifify you by SMS on this number when this changes?",
            choices=[Choice("yes", "Yes"), Choice("no", "No")],
            error="Can we notifify you via SMS to let you know when you can register?",
            next="state_confirm_notification",
        )

    async def state_confirm_notification(self):
        return EndState(self, text="Thank you for confirming", next=self.START_STATE)

    async def state_identification_type(self):
        return ChoiceState(
            self,
            question="How would you like to register?",
            choices=[Choice(i.name, i.value) for i in self.ID_TYPES],
            error="Please choose 1 of the following ways to register",
            next="state_identification_number",
        )

    async def state_identification_number(self):
        idtype = self.ID_TYPES[self.user.answers["state_identification_type"]]
        idtype_label = idtype.value

        async def validate_identification_number(value):
            value = value.strip()
            if idtype == self.ID_TYPES.rsa_id or idtype == self.ID_TYPES.refugee:
                try:
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
                assert value.isdigit()
                assert int(value) > date.today().year - MAX_AGE
                assert int(value) <= date.today().year
            except AssertionError:
                raise ErrorMessage(
                    "REQUIRED: Please TYPE the 4 digits of the year you were born in "
                    "(Example: 1980)"
                )

        return FreeText(
            self,
            question="DOB: In what year were you born? (Please type)",
            next="state_dob_month",
            check=validate_dob_year,
        )

    async def state_dob_month(self):
        return ChoiceState(
            self,
            question="DOB: Select your month",
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
            error="REQUIRED: In which month were you born?",
        )

    async def state_dob_day(self):
        async def validate_dob_day(value):
            dob_year = int(self.user.answers["state_dob_year"])
            dob_month = int(self.user.answers["state_dob_month"])
            try:
                assert value.isdigit()
                date(dob_year, dob_month, int(value))
            except (AssertionError, ValueError):
                raise ErrorMessage(
                    "ERROR: Please reply with DAY of your birthday Example: 20"
                )

        return FreeText(
            self,
            question="DOB: Which day of the month were you born on",
            next="state_first_name",
            check=validate_dob_day,
        )

    async def state_first_name(self):
        return FreeText(
            self, question="Please enter your FIRST name", next="state_surname"
        )

    async def state_surname(self):
        return FreeText(
            self, question="Please enter your SURNAME", next="state_confirm_profile"
        )

    async def state_confirm_profile(self):
        first_name = self.user.answers["state_first_name"][:27]
        surname = self.user.answers["state_surname"][:27]
        id_type = self.ID_TYPES[self.user.answers["state_identification_type"]].value
        id_number = self.user.answers["state_identification_number"][:20]
        return MenuState(
            self,
            question="\n".join(
                [
                    "Confirm the following:",
                    "",
                    f"{first_name} {surname}",
                    id_type,
                    id_number,
                ]
            ),
            choices=[
                Choice("state_province", "Yes"),
                Choice("state_identification_type", "No"),
            ],
            error="\n".join(
                [
                    "Is the information you shared correct?",
                    "",
                    f"{first_name} {surname}",
                    id_type,
                    id_number,
                ]
            ),
        )
