from typing import List

from prometheus_client import Counter

from vaccine.models import Answer, Message, User
from vaccine.utils import random_id

STATE_CHANGE = Counter(
    "state_change", "Whenever a user's state gets changed", ("from_state", "to_state")
)


class BaseApplication:
    def __init__(self, user: User):
        self.user = user
        self.answer_events: List[Answer] = []

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
            self.user.session_id = None
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
        if self.user.session_id is not None:
            return await state.process_message(message)
        else:
            self.user.session_id = random_id()
            return await state.display(message)

    def save_answer(self, name: str, value: str):
        self.user.answers[name] = value
        self.answer_events.append(
            Answer(
                question=name,
                response=value,
                address=self.user.addr,
                session_id=self.user.session_id or random_id(),
            )
        )
