from typing import List

from vaccine.models import Message, User
from vaccine.states import EndState, ChoiceState, Choice


class Application:
    START_STATE = "state_occupation"

    def __init__(self, user: User):
        self.user = user

    async def get_current_state(self):
        if not self.user.state.name:
            self.user.state.name = self.START_STATE
        state_func = getattr(self, self.user.state.name)
        return await state_func()

    async def process_message(self, message: Message) -> List[Message]:
        """
        Processes the message, and returns a list of messages to return to the user
        """
        state = await self.get_current_state()
        if self.user.in_session:
            return await state.process_message(message)
        else:
            self.user.in_session = True
            return await state.display(message)

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
            next="state_end",
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
