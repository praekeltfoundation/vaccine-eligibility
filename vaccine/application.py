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
        not_sure = "\n".join(
            [
                "*Health Care Workers* include doctors, nurses, dentists, pharmacists, "
                "medical specialists and all people involved in providing health "
                "services such as cleaning, security, medical waste disposal and "
                "administrative work.",
                "",
                "*Essential Workers* include police officers, miners, teachers, people "
                "working in security, retail, food, funeral, banking and essential "
                "muncipal and home affairs, border control and port health services.",
            ]
        )

        async def next_state(choice: Choice):
            if choice.value == "not_sure":
                self.send_message(not_sure)
                return "state_occupation"
            return "state_age"

        return ChoiceState(
            self,
            question="\n".join(
                [
                    "◼️◻️◻️◻️◻️",
                    "",
                    "Which of these positions or job titles describes your current "
                    "employment:",
                    "",
                ]
            ),
            choices=[
                Choice("hcw", "Health Care Worker"),
                Choice("essential", "Essential Worker"),
                Choice("other", "Other"),
                Choice("not_sure", "Not Sure"),
            ],
            error="⚠️ This service works best when you use the numbered options "
            "available\n",
            next=next_state,
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
