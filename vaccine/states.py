from collections.abc import Awaitable, Sequence
from dataclasses import dataclass, field
from inspect import iscoroutinefunction, isfunction
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Optional,
    Union,
)

import emoji

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

    async def process_message(self, message: Message) -> list[Message]:
        self.app.user.session_id = None
        self.app.state_name = self.next
        if self.clear_state:
            self.app.user.answers = {}
        kwargs = {"content": self.text, "continue_session": False}
        if self.helper_metadata is not None:
            kwargs["helper_metadata"] = self.helper_metadata
        return self.app.send_message(**kwargs)

    async def display(self, message: Message) -> list[Message]:
        return await self.process_message(message)


@dataclass
class Choice:
    value: str
    label: str
    additional_keywords: list[str] = field(default_factory=list)


class ChoiceState:
    def __init__(
        self,
        app: "BaseApplication",
        question: str,
        choices: list[Choice],
        error: str,
        next: Union[str, Callable, dict[str, str]],
        accept_labels: bool = True,
        footer: Optional[str] = None,
        error_footer: Optional[str] = None,
        header: Optional[str] = None,
        error_header: Optional[str] = None,
        buttons: Optional[list[Choice]] = None,
        helper_metadata: Optional[dict] = None,
        override_answer_name: Optional[str] = None,
    ):
        self.app = app
        self.question = question
        self.choices = choices
        self.error = error
        self.accept_labels = accept_labels
        self.next = next
        self.footer = footer
        self.error_footer = error_footer
        self.header = header
        self.error_header = error_header
        self.buttons = buttons
        self.helper_metadata = helper_metadata
        self.override_answer_name = override_answer_name

    def _normalise_text(self, text: Optional[str]) -> str:
        text = (text or "").strip().lower()
        if emoji.is_emoji(text):
            return text[0]
        return text

    def _get_choice(self, content: Optional[str]) -> Optional[Choice]:
        content = self._normalise_text(content)

        if self.buttons:
            for button in self.buttons:
                if content == button.value:
                    return button

        for i, choice in enumerate(self.choices):
            if content == str(i + 1):
                return choice
            if self.accept_labels and content == self._normalise_text(choice.label):
                return choice
            for keyword in choice.additional_keywords:
                if content == self._normalise_text(keyword):
                    return choice
        return None

    @property
    def _display_choices(self) -> str:
        return get_display_choices(self.choices)

    async def _get_next(self, choice):
        if iscoroutinefunction(self.next):
            return await self.next(choice)
        if isfunction(self.next):
            return self.next(choice)
        if isinstance(self.next, dict):
            return self.next[choice.value]
        return self.next

    async def process_message(self, message: Message):
        choice = self._get_choice(message.content)
        if choice is None:
            return await self.display_error(message)
        else:
            self.app.save_answer(
                self.override_answer_name or self.app.state_name, choice.value
            )
            self.app.state_name = await self._get_next(choice)
            state = await self.app.get_current_state()
            return await state.display(message)

    async def display_error(self, message: Message):
        text = f"{self.error}\n{self._display_choices}"
        if self.error_footer:
            text = f"{text}\n{self.error_footer}"
        if self.error_header:
            text = f"{self.error_header}\n{text}"
        return self.app.send_message(text)

    async def display(self, message: Message):
        helper_metadata: dict[str, Any] = self.helper_metadata or {}
        if self.buttons:
            helper_metadata["buttons"] = [choice.label for choice in self.buttons]
        text = f"{self.question}\n{self._display_choices}"
        if self.footer is not None:
            text = f"{text}\n{self.footer}"
        if self.header is not None:
            text = f"{self.header}\n{text}"
        return self.app.send_message(text, helper_metadata=helper_metadata)


class LanguageState(ChoiceState):
    async def _get_next(self, choice: Choice):
        self.app.set_language(choice.value)
        return await super()._get_next(choice)


class MenuState(ChoiceState):
    def __init__(
        self,
        app: "BaseApplication",
        question: str,
        choices: list[Choice],
        error: str,
        accept_labels: bool = True,
        footer: Optional[str] = None,
        error_footer: Optional[str] = None,
        header: Optional[str] = None,
        error_header: Optional[str] = None,
    ):
        self.app = app
        self.question = question
        self.choices = choices
        self.error = error
        self.accept_labels = accept_labels
        self.footer = footer
        self.error_footer = error_footer
        self.header = header
        self.error_header = error_header
        self.buttons = None
        self.helper_metadata = None
        self.override_answer_name = None

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
        check: Union[
            Callable[[Optional[str]], Awaitable],
            list[Callable[[Optional[str]], Awaitable]],
            None,
        ] = None,
        buttons: Optional[list[Choice]] = None,
        override_answer_name: Optional[str] = None,
        footer: Optional[str] = None,
        header: Optional[str] = None,
    ):
        self.app = app
        self.question = question
        self.next = next
        self.check = check
        self.buttons = buttons
        self.override_answer_name = override_answer_name
        self.footer = footer
        self.header = header

    async def process_message(self, message: Message):
        if self.check is not None:
            if not isinstance(self.check, list):
                self.check = [self.check]
            for validator in self.check:
                try:
                    await validator(message.content)
                except ErrorMessage as e:
                    return self.app.send_message(e.message)
        self.app.save_answer(
            self.override_answer_name or self.app.state_name, message.content or ""
        )
        self.app.state_name = self.next
        state = await self.app.get_current_state()
        return await state.display(message)

    async def display(self, message: Message):
        helper_metadata: dict[str, Any] = {}
        if self.buttons:
            helper_metadata["buttons"] = [choice.label for choice in self.buttons]
        text = self.question
        if self.footer is not None:
            text = f"{text}\n{self.footer}"
        if self.header is not None:
            text = f"{self.header}\n{text}"
        return self.app.send_message(text, helper_metadata=helper_metadata)


class WhatsAppTextOnlyFreetext(FreeText):
    def __init__(
        self,
        *args,
        text_only_error: Optional[str] = None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.text_only_error = text_only_error

    async def process_message(self, message: Message):
        if (
            self.text_only_error is not None
            and message.transport_metadata
            and message.transport_metadata.get("message", {}).get("type") != "text"
        ):
            return self.app.send_message(self.text_only_error)
        return await super().process_message(message)


class BaseWhatsAppChoiceState(ChoiceState):
    """
    Base class for all whatsapp choice states.

    Takes into account that buttons and list options will be truncated at 20 characters
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for choice in self.choices:
            if len(choice.label) > 20:
                choice.additional_keywords.append(choice.label[:20])


class WhatsAppButtonState(BaseWhatsAppChoiceState):
    async def display(self, message: Message):
        helper_metadata: dict[str, Any] = {
            "buttons": [choice.label for choice in self.choices]
        }
        if self.header:
            helper_metadata["header"] = self.header
        if self.footer:
            helper_metadata["footer"] = self.footer
        return self.app.send_message(self.question, helper_metadata=helper_metadata)

    async def display_error(self, message: Message):
        helper_metadata: dict[str, Any] = {
            "buttons": [choice.label for choice in self.choices]
        }
        if self.error_header:
            helper_metadata["header"] = self.error_header
        if self.error_footer:
            helper_metadata["footer"] = self.error_footer
        return self.app.send_message(self.error, helper_metadata=helper_metadata)


class WhatsAppListState(BaseWhatsAppChoiceState):
    def __init__(self, *args, button: str, **kwargs):
        super().__init__(*args, **kwargs)
        self.button = button

    async def display(self, message: Message):
        return self.app.send_message(
            self.question,
            helper_metadata={
                "button": self.button,
                "sections": [
                    {
                        "rows": [
                            {"id": c.label[:20], "title": c.label[:20]}
                            for c in self.choices
                        ]
                    }
                ],
            },
        )


class SectionedChoiceState(ChoiceState):
    def __init__(
        self,
        *args,
        sections: Sequence[tuple[str, Sequence[Choice]]],
        separator: Optional[str] = None,
        **kwargs,
    ):
        choices: list[Choice] = []
        for section_choices in sections:
            choices.extend(section_choices[1])

        kwargs["choices"] = choices

        super().__init__(*args, **kwargs)
        self.sections = sections
        self.separator = separator

    @property
    def _display_choices(self) -> str:
        lines = []

        i = 1
        for section_name, section_choices in self.sections:
            lines.append(section_name)

            for choice in section_choices:
                lines.append(f"{i}. {choice.label}")
                i += 1

            if self.separator is not None:
                lines.append(self.separator)

        return "\n".join(lines)


class CustomChoiceState(BaseWhatsAppChoiceState):
    def __init__(
        self,
        *args,
        button: Optional[str] = None,
        additional_messages: Optional[list[str]] = None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.additional_messages = additional_messages or []
        self.button = button

    @property
    def _helper_metadata(self):
        helper_metadata = self.helper_metadata or {}
        if self.buttons:
            if len(self.buttons) <= 3:
                helper_metadata["buttons"] = [choice.label for choice in self.buttons]
            elif len(self.buttons) <= 10:
                helper_metadata["button"] = self.button
                helper_metadata["sections"] = [
                    {
                        "rows": [
                            {"id": c.label[:20], "title": c.label[:20]}
                            for c in self.buttons
                        ]
                    }
                ]
        return helper_metadata

    async def display(self, message):
        self.app.send_message(self.question, helper_metadata=self._helper_metadata)
        for content in self.additional_messages:
            self.app.send_message(content)

    async def display_error(self, message):
        return self.app.send_message(self.error, helper_metadata=self._helper_metadata)
