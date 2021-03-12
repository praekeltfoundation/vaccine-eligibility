from dataclasses import dataclass
from typing import Awaitable, Callable, List, Optional

from vaccine.models import Message


class EndState:
    def __init__(self, app, text: str, next: str):
        self.app = app
        self.text = text
        self.next = next

    async def process_message(self, message: Message) -> List[Message]:
        self.app.user.in_session = False
        self.app.state_name = self.next
        return [message.reply(self.text, continue_session=False)]

    async def display(self, message: Message) -> List[Message]:
        return await self.process_message(message)


@dataclass
class Choice:
    value: str
    label: str


class ChoiceState:
    def __init__(
        self,
        app,
        question: str,
        choices: List[Choice],
        error: str,
        next: str,
        accept_labels: bool = True,
    ):
        self.app = app
        self.question = question
        self.choices = choices
        self.error = error
        self.accept_labels = accept_labels
        self.next = next

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
        return "\n".join(f"{i + 1}. {c.label}" for i, c in enumerate(self.choices))

    async def process_message(self, message: Message) -> List[Message]:
        self.app.user.in_session = True
        choice = self._get_choice(message.content)
        if choice is None:
            return [message.reply(f"{self.error}\n{self._display_choices}")]
        else:
            self.app.user.answers[self.app.state] = choice.value
            self.app.state_name = self.next
            state = await self.app.get_current_state()
            return await state.display(message)

    async def display(self, message: Message) -> List[Message]:
        return [message.reply(f"{self.question}\n{self._display_choices}")]


class ErrorMessage(Exception):
    def __init__(self, message):
        self.message = message


class FreeText:
    def __init__(
        self, app, question: str, next: str, check: Callable[[Optional[str]], Awaitable]
    ):
        self.app = app
        self.question = question
        self.next = next
        self.check = check

    async def process_message(self, message: Message) -> List[Message]:
        self.app.user.in_session = True
        if self.check is not None:
            try:
                await self.check(message.content)
            except ErrorMessage as e:
                return [message.reply(f"{e.message}")]
        self.app.user.answers[self.app.state] = message.content
        self.app.state_name = self.next
        state = await self.app.get_current_state()
        return await state.display(message)

    async def display(self, message: Message) -> List[Message]:
        return [message.reply(f"{self.question}")]
