from typing import List

from vaccine.models import Message, User
from vaccine.states import EndState


class Application:
    START_STATE = "state_start"

    def __init__(self, user: User):
        self.user = user

    async def process_message(self, message: Message) -> List[Message]:
        """
        Processes the message, and returns a list of messages to return to the user
        """
        if not self.user.state.name:
            self.user.state.name = self.START_STATE
        state_func = getattr(self, self.user.state.name)
        state = await state_func()
        if self.user.in_session:
            return await state.process_message(message)
        else:
            self.user.in_session = True
            return await state.display(message)

    async def state_start(self):
        return EndState(
            self, text="Welcome to the vaccine eligibility service.", next="state_start"
        )
