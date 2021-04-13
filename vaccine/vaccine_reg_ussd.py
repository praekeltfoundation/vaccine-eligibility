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
