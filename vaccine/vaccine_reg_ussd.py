from vaccine.base_application import BaseApplication
from vaccine.states import Choice, MenuState, ChoiceState, EndState


class Application(BaseApplication):
    START_STATE = "state_age_gate"

    ID_TYPES = {
        "rsa_id": "RSA ID Number",
        "passport": "Passport Number",
        "asylum_seeker": "Asylum Seeker Permit number",
        "refugee": "Refugee Number Permit number",
    }

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
            choices=[Choice(k, v) for k, v in self.ID_TYPES.items()],
            error="Please choose 1 of the following ways to register",
            next="state_identification_number",
        )
