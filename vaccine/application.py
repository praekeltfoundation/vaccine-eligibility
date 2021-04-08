from typing import Optional

from vaccine.base_application import BaseApplication
from vaccine.states import Choice, ChoiceState, EndState, ErrorMessage, FreeText


class Application(BaseApplication):
    START_STATE = "state_start"

    async def state_start(self):
        self.send_message(
            "Thank you for your interest in the getting the COVID-19 vaccine. The "
            "South African national vaccine rollout is being done over 3 phases. "
            "Answer these questions to find out which phase you are in:"
        )
        return await self.go_to_state("state_occupation")

    async def state_occupation(self):
        return ChoiceState(
            self,
            question="\n".join(
                [
                    "Welcome to the vaccine eligibility service.",
                    "Please answer a few questions so that we can determine your "
                    "eligibility.",
                    "",
                    "What is your current occupation?",
                ]
            ),
            choices=[
                Choice("unemployed", "Unemployed"),
                Choice("retired", "Retired"),
                Choice("healthcare", "Healthcare"),
                Choice("essential", "Essential"),
                Choice("software", "Software Engineer"),
                Choice("other", "Other"),
            ],
            error="\n".join(
                [
                    "Sorry we don't understand your response, please try again.",
                    "",
                    "What is your current occupation?",
                ]
            ),
            next="state_age",
        )

    async def state_age(self):
        async def check_age(content: Optional[str]):
            try:
                age = int(content or "")
                assert age >= 0
            except (ValueError, TypeError, AssertionError):
                raise ErrorMessage(
                    "Sorry, we don't understand your response. "
                    "Please type the number that represents your age in years"
                )

        return FreeText(
            self,
            question="What is your current age, in years?",
            next="state_end",
            check=check_age,
        )

    async def state_end(self):
        return EndState(
            self,
            text="\n".join(
                [
                    "Thank you for answering those questions.",
                    "You are not currently eligible for a vaccine, but we will send "
                    "you a message notifying you when you are eligible.",
                    "",
                    "Type *MENU* to go back to the main menu, or *VACCINE* for more "
                    "information around vaccines",
                ]
            ),
            next="state_occupation",
        )
