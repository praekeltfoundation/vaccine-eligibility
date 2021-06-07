from dataclasses import dataclass
from inspect import iscoroutinefunction
from typing import TYPE_CHECKING, Awaitable, Callable, List, Optional, Union

from vaccine.models import Message
from vaccine.utils import get_display_choices

if TYPE_CHECKING:  # pragma: no cover
    from vaccine.base_application import BaseApplication


class EndState:
    def __init__(
        self,
        app: "BaseApplication",
        text: str,
        next: Optional[str] = None,
        clear_state: bool = True,
        helper_metadata: Optional[dict] = None,
    ):
        self.app = app
        self.text = text
        self.next = next
        self.clear_state = clear_state
        self.helper_metadata = helper_metadata

    async def process_message(self, message: Message) -> List[Message]:
        self.app.user.session_id = None
        self.app.state_name = self.next
        if self.clear_state:
            self.app.user.answers = {}
        kwargs = {"content": self.text, "continue_session": False}
        if self.helper_metadata is not None:
            kwargs["helper_metadata"] = self.helper_metadata
        return self.app.send_message(**kwargs)

    async def display(self, message: Message) -> List[Message]:
        return await self.process_message(message)


@dataclass
class Choice:
    value: str
    label: str


class ChoiceState:
    def __init__(
        self,
        app: "BaseApplication",
        question: str,
        choices: List[Choice],
        error: str,
        next: Union[str, Callable],
        accept_labels: bool = True,
        footer: Optional[str] = None,
    ):
        self.app = app
        self.question = question
        self.choices = choices
        self.error = error
        self.accept_labels = accept_labels
        self.next = next
        self.footer = footer

    def _get_choice(self, content: Optional[str]) -> Optional[Choice]:
        content = (content or "").strip()
        try:
            choice_num = int(content)
            if choice_num > 0 and choice_num <= len(self.choices):
                return self.choices[choice_num - 1]
        except ValueError:
            pass

        if self.accept_labels:
            for choice in self.choices:
                if content.lower() == choice.label.strip().lower():
                    return choice
        return None

    @property
    def _display_choices(self) -> str:
        return get_display_choices(self.choices)

    async def _get_next(self, choice):
        if iscoroutinefunction(self.next):
            return await self.next(choice)
        return self.next

    async def process_message(self, message: Message):
        choice = self._get_choice(message.content)
        if choice is None:
            return self.app.send_message(f"{self.error}\n{self._display_choices}")
        else:
            self.app.save_answer(self.app.state_name, choice.value)
            self.app.state_name = await self._get_next(choice)
            state = await self.app.get_current_state()
            return await state.display(message)

    async def display(self, message: Message):
        text = f"{self.question}\n{self._display_choices}"
        if self.footer is not None:
            text = f"{text}\n{self.footer}"
        return self.app.send_message(text)


class MenuState(ChoiceState):
    def __init__(
        self,
        app: "BaseApplication",
        question: str,
        choices: List[Choice],
        error: str,
        accept_labels: bool = True,
        footer: Optional[str] = None,
    ):
        self.app = app
        self.question = question
        self.choices = choices
        self.error = error
        self.accept_labels = accept_labels
        self.footer = footer

    async def _next(self, choice: Choice):
        return choice.value

    next = _next


class ErrorMessage(Exception):
    def __init__(self, message):
        self.message = message


class FreeText:
    def __init__(
        self,
        app: "BaseApplication",
        question: str,
        next: str,
        check: Optional[Callable[[Optional[str]], Awaitable]] = None,
    ):
        self.app = app
        self.question = question
        self.next = next
        self.check = check

    async def process_message(self, message: Message):
        if self.check is not None:
            try:
                await self.check(message.content)
            except ErrorMessage as e:
                return self.app.send_message(e.message)
        self.app.save_answer(self.app.state_name, message.content or "")
        self.app.state_name = self.next
        state = await self.app.get_current_state()
        return await state.display(message)

    async def display(self, message: Message):
        return self.app.send_message(self.question)
