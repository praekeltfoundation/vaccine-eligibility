from vaccine.base_application import BaseApplication
from vaccine.states import Choice, MenuState


class Application(BaseApplication):
    START_STATE = "state_age_gate"

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
                Choice("state_under40_sms", "No"),
            ],
            error="Self registration is currently only available to those 40 years or "
            "older. Please tell us if you are 40 years of age or older?",
        )
