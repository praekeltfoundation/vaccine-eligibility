import gettext
import logging
from typing import Any, List, Optional

from prometheus_client import Counter

from vaccine.models import Answer, Message, User
from vaccine.states import EndState
from vaccine.utils import random_id
from vaccine.worker import Worker

STATE_CHANGE = Counter(
    "state_change", "Whenever a user's state gets changed", ("from_state", "to_state")
)

logger = logging.getLogger(__name__)


class BaseApplication:
    START_STATE = "state_start"
    ERROR_STATE = "state_error"

    # TODO: transition all tests over to new test helper to make worker manditory
    def __init__(self, user: User, worker: Optional[Worker] = None):
        self.user = user
        self.worker = worker
        self.answer_events: List[Answer] = []
        self.messages: List[Message] = []
        self.inbound: Optional[Message] = None
        self.set_language(self.user.lang)

    def set_language(self, language):
        self.user.lang = language
        self.translation = gettext.translation(
            "messages",
            localedir="locales",
            languages=[self.user.lang or ""],
            fallback=True,
        )
        self._ = self.translation.gettext

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

    async def go_to_state_with_kwargs(self, name, **kw):
        """
        Go to another state and have it process the user message instead
        """
        self.state_name = name
        if not self.state_name:
            self.state_name = self.START_STATE
        state_func = getattr(self, self.state_name)
        return await state_func(**kw)

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
        try:
            self.inbound = message
            if message.content == "!reset":
                self.state_name = self.START_STATE
                self.user.answers = {}
                self.user.session_id = None
            state = await self.get_current_state()
            if (
                message.session_event == Message.SESSION_EVENT.NEW
                or self.user.session_id is None
            ):
                self.user.session_id = random_id()
                await state.display(message)
            else:
                await state.process_message(message)
        except Exception:
            logger.exception("Application error")
            self.state_name = self.ERROR_STATE
            state = await self.get_current_state()
            await state.process_message(message)
        return self.messages

    def save_answer(self, name: str, value: Any):
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

    def save_metadata(self, name: str, value: Any):
        """
        Saves metadata on the user
        """
        self.user.metadata[name] = value

    def send_message(self, content, continue_session=True, **kw):
        """
        Sends a reply to the user
        """
        self.messages.append(self.inbound.reply(content, continue_session, **kw))

    async def state_error(self):
        return EndState(
            self, text=self._("Something went wrong. Please try again later.")
        )
