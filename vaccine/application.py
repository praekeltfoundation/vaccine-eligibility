from typing import List, Optional

from prometheus_client import Counter

from vaccine.models import Message, User
from vaccine.states import Choice, ChoiceState, EndState, ErrorMessage, FreeText

STATE_CHANGE = Counter(
    "state_change", "Whenever a user's state gets changed", ("from_state", "to_state")
)


class Application:
    START_STATE = "state_occupation"

    def __init__(self, user: User):
        self.user = user

    async def get_current_state(self):
        if not self.state_name:
            self.state_name = self.START_STATE
        state_func = getattr(self, self.state_name)
        return await state_func()

    @property
    def state_name(self):
        return self.user.state.name

    @state_name.setter
    def state_name(self, state):
        STATE_CHANGE.labels(self.state_name, state).inc()
        self.user.state.name = state

    async def process_message(self, message: Message) -> List[Message]:
        """
        Processes the message, and returns a list of messages to return to the user
        """
        if message.session_event == Message.SESSION_EVENT.CLOSE:
            self.user.in_session = False
            return [
                message.reply(
                    content="\n".join(
                        [
                            "We're sorry, but you've taken too long to reply and your "
                            "session has expired.",
                            "If you would like to continue, you can at anytime by "
                            "typing the word *VACCINE*.",
                            "",
                            "Reply *MENU* to return to the main menu",
                        ]
                    ),
                    continue_session=False,
                )
            ]
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
