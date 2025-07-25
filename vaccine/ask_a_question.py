import json
import logging
import re
from typing import Optional
from urllib.parse import urljoin

import aiohttp
import sentry_sdk

from vaccine import ask_a_question_config as config
from vaccine.base_application import BaseApplication
from vaccine.models import Message
from vaccine.states import Choice, ChoiceState, EndState, FreeText, WhatsAppButtonState
from vaccine.utils import HTTP_EXCEPTIONS
from vaccine.validators import nonempty_validator

logger = logging.getLogger(__name__)


def get_model():
    # TODO: Cache the session globally. Things that don't work:
    # - Declaring the session at the top of the file
    #   You get a `Timeout context manager should be used inside a task` error
    # - Declaring it here but caching it in a global variable for reuse
    #   You get a `Event loop is closed` error
    return aiohttp.ClientSession(
        timeout=aiohttp.ClientTimeout(total=5),
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "vaccine-registration-ussd",
            "Authorization": f"Bearer {config.MODEL_API_TOKEN}",
        },
    )


class RedirectChoiceState(ChoiceState):
    async def process_message(self, message: Message):
        choice = self._get_choice(message.content)
        if choice is None:
            state = await self.app.go_to_state("state_question")
            return await state.process_message(message)
        else:
            return await super().process_message(message)


class WhatsAppRedirectButtonState(WhatsAppButtonState):
    async def process_message(self, message: Message):
        choice = self._get_choice(message.content)
        if choice is None:
            state = await self.app.go_to_state("state_question")
            return await state.process_message(message)
        else:
            return await super().process_message(message)


class Application(BaseApplication):
    START_STATE = "state_question"

    async def process_message(self, message: Message) -> list[Message]:
        if message.session_event == Message.SESSION_EVENT.CLOSE:
            self.state_name = "state_timeout"
        keyword = re.sub(r"\W+", " ", message.content or "").strip().lower()
        # Restart keywords
        if keyword in ("ask",):
            self.user.session_id = None
            self.state_name = self.START_STATE
        # Exit keywords
        if keyword in (
            "menu",
            "0",
            "cases",
            "news",
            "vaccine",
            "check",
            "register",
        ):
            self.state_name = "state_exit"

        return await super().process_message(message)

    async def state_timeout(self):
        return EndState(
            self,
            text=self._(
                "❓ *YOUR VACCINE QUESTIONS*\n"
                "\n"
                "We haven’t heard from you in a while!\n"
                "\n"
                "The question session has timed out due to inactivity. You "
                "will need to start again. Just TYPE the word ASK.\n"
                "\n"
                "-----\n"
                "📌 Reply *0* to return to the main *MENU*"
            ),
        )

    async def state_exit(self):
        return EndState(self, "", helper_metadata={"automation_handle": True})

    async def state_question(self):
        question = self._(
            "❓ *ASK*  your questions about vaccines\n"
            "\n"
            "Try *typing your own question* or sharing/forwarding a '*rumour*' that's "
            "going around to get the facts!\n"
            "\n"
            '[💡Tip: Reply with a question like: _"Are vaccines safe?"_ ]'
        )
        return FreeText(
            self,
            question=question,
            check=nonempty_validator(question),
            next="state_call_model",
        )

    async def state_call_model(self):
        model = get_model()
        data = {
            "text_to_match": self.user.answers["state_question"],
            "metadata": {
                "whatsapp_id": self.user.addr,
                "message_id": self.inbound.message_id,
            },
        }
        async with model as session:
            for i in range(3):
                try:
                    response = await session.post(
                        url=urljoin(config.MODEL_API_URL, "/inbound/check"), json=data
                    )
                    response_data = await response.json()
                    sentry_sdk.set_context(
                        "model", {"request_data": data, "response_data": response_data}
                    )
                    response.raise_for_status()
                    break
                except HTTP_EXCEPTIONS as e:
                    if i == 2:
                        logger.exception(e)
                        return await self.go_to_state("state_error")
                    else:
                        continue
        if response_data.get("top_responses"):
            self.save_answer("model_response", json.dumps(response_data))
            return await self.go_to_state("state_display_response_choices")
        else:
            return await self.go_to_state("state_no_responses")

    async def state_no_responses(self):
        question = self._(
            "*No Results Found*\n"
            "\n"
            "[💡Tip: Try typing your question again using different words or reply "
            "*MENU* to browse topics]"
        )

        async def check(text: Optional[str]):
            await nonempty_validator(question)(text)
            # overwite state_question with this new question
            self.save_answer("state_question", text)

        return FreeText(self, question=question, check=check, next="state_call_model")

    async def state_display_response_choices(self):
        responses = json.loads(self.user.answers["model_response"])["top_responses"]
        return RedirectChoiceState(
            self,
            question=self._("🔎 *Top Search Results*\n"),
            choices=[Choice(title, title) for title, _ in responses],
            error="",  # Errors now redirect to `state_question`
            next="state_submit_user_choice",
            footer=self._(
                "\n[💡Tip: If you don't see what you're looking for, try typing your "
                "question again using different words or reply *MENU* to browse topics]"
            ),
        )

    async def state_submit_user_choice(self):
        model = get_model()
        model_response = json.loads(self.user.answers["model_response"])
        data = {
            "inbound_id": model_response["inbound_id"],
            "feedback_secret_key": model_response["feedback_secret_key"],
            "feedback": {
                "choice": self.user.answers["state_display_response_choices"],
            },
        }
        async with model as session:
            for i in range(3):
                try:
                    response = await session.post(
                        url=urljoin(config.MODEL_API_URL, "/inbound/feedback"),
                        json=data,
                    )
                    response_data = await response.text()
                    sentry_sdk.set_context(
                        "model", {"request_data": data, "response_data": response_data}
                    )
                    response.raise_for_status()
                    break
                except HTTP_EXCEPTIONS as e:
                    if i == 2:
                        logger.exception(e)
                        return await self.go_to_state("state_error")
                    else:
                        continue
        return await self.go_to_state("state_display_selected_choice")

    async def state_display_selected_choice(self):
        responses = json.loads(self.user.answers["model_response"])["top_responses"]
        choice = self.user.answers["state_display_response_choices"]
        for title, _content in responses:
            if choice == title:
                break
        return WhatsAppRedirectButtonState(
            self,
            question=_content,
            choices=[
                Choice("yes", self._("👍"), ["yes"]),
                Choice("no", self._("👎︎."), ["no"]),
            ],
            error="",  # Errors redirect to `state_question`
            header=title,
            footer=self._("Was this helpful?"),
            next="state_submit_user_feedback",
        )

    async def state_submit_user_feedback(self):
        model = get_model()
        model_response = json.loads(self.user.answers["model_response"])
        data = {
            "inbound_id": model_response["inbound_id"],
            "feedback_secret_key": model_response["feedback_secret_key"],
            "feedback": {
                "choice": self.user.answers["state_display_response_choices"],
                "feedback": self.user.answers["state_display_selected_choice"],
            },
        }
        async with model as session:
            for i in range(3):
                try:
                    response = await session.post(
                        url=urljoin(config.MODEL_API_URL, "/inbound/feedback"),
                        json=data,
                    )
                    response_data = await response.text()
                    sentry_sdk.set_context(
                        "model", {"request_data": data, "response_data": response_data}
                    )
                    response.raise_for_status()
                    break
                except HTTP_EXCEPTIONS as e:
                    if i == 2:
                        logger.exception(e)
                        return await self.go_to_state("state_error")
                    else:
                        continue
        return await self.go_to_state("state_end")

    async def state_end(self):
        if self.user.answers["state_display_selected_choice"] == "no":
            return await self.go_to_state("state_another_result")
        text = self._(
            "Thank you for confirming.\n"
            "\n"
            "-----\n"
            "Reply:\n"
            "❓ *ASK* to ask more vaccine questions\n"
            "📌 *0* for the main *MENU*"
        )
        return EndState(self, text=text)

    async def state_another_result(self):
        responses = json.loads(self.user.answers["model_response"])["top_responses"]
        question = self._("Thank you for confirming.\n\nTry a different result?")

        async def next_state(choice: Choice):
            self.save_answer("state_display_response_choices", choice.label)
            return "state_display_selected_choice"

        return RedirectChoiceState(
            self,
            question=question,
            choices=[Choice(title, title) for title, _ in responses],
            error="",  # Errors redirect to `state_question`
            next=next_state,
            footer=self._(
                "\n"
                "-----\n"
                "Reply:\n"
                "❓ *ASK* to ask more vaccine questions\n"
                "📌 *0* for the main *MENU*"
            ),
        )

    async def state_error(self):
        return EndState(
            self,
            text=self._(
                "Something went wrong, your question was not able to be processed. "
                "Please try again later"
            ),
        )
