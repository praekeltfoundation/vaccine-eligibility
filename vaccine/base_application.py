from typing import List, Optional

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
        self.messages: List[Message] = []
        self.inbound: Optional[Message] = None

    async def get_current_state(self):
        if not self.state_name:
            self.state_name = self.START_STATE
        state_func = getattr(self, self.state_name)
        return await state_func()

    async def go_to_state(self, name):
        """
        Go to another state and have it process the user message instead
        """
        self.state_name = name
        return await self.get_current_state()

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
        self.inbound = message
        state = await self.get_current_state()
        if self.user.session_id is not None:
            await state.process_message(message)
        else:
            self.user.session_id = random_id()
            await state.display(message)
        return self.messages

    def save_answer(self, name: str, value: str):
        """
        Saves an answer from the user
        """
        self.user.answers[name] = value
        self.answer_events.append(
            Answer(
                question=name,
                response=value,
                address=self.user.addr,
                session_id=self.user.session_id or random_id(),
            )
        )

    def send_message(self, content, continue_session=True, **kw):
        """
        Sends a reply to the user
        """
        self.messages.append(self.inbound.reply(content, continue_session, **kw))
