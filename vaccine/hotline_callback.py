import logging
import re
from datetime import datetime, timezone
from typing import List
from urllib.parse import urljoin

import aiohttp
import holidays
import sentry_sdk

from vaccine import hotline_callback_config as config
from vaccine.base_application import BaseApplication
from vaccine.models import Message
from vaccine.states import Choice, EndState, FreeText, WhatsAppButtonState
from vaccine.utils import (
    HTTP_EXCEPTIONS,
    TZ_SAST,
    display_phonenumber,
    get_today,
    normalise_phonenumber,
)
from vaccine.validators import nonempty_validator, phone_number_validator

logger = logging.getLogger(__name__)
za_holidays = holidays.SouthAfrica()


class WhatsAppExitButtonState(WhatsAppButtonState):
    async def process_message(self, message: Message):
        choice = self._get_choice(message.content)
        if choice is None:
            state = await self.app.go_to_state("state_exit")
            return await state.process_message(message)
        else:
            return await super().process_message(message)


def get_callback_api():
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
            "User-Agent": "contactndoh-hotline-callback",
        },
    )


def get_turn_api():
    # TODO: Cache the session globally. Things that don't work:
    # - Declaring the session at the top of the file
    #   You get a `Timeout context manager should be used inside a task` error
    # - Declaring it here but caching it in a global variable for reuse
    #   You get a `Event loop is closed` error
    return aiohttp.ClientSession(
        timeout=aiohttp.ClientTimeout(total=5),
        headers={
            "Content-Type": "application/json",
            "Accept": "application/vnd.v1+json",
            "User-Agent": "contactndoh-hotline-callback",
            "Authorization": f"Bearer {config.TURN_TOKEN}",
        },
    )


def get_current_datetime() -> datetime:
    """
    Returns the current datetime in SAST
    """
    return datetime.now(tz=TZ_SAST)


def in_office_hours() -> bool:
    """
    Office hours are:
    Monday to Friday 7am-8pm
    Saturdays, Sundays, and Public Holidays 8am-6pm
    """
    now = get_current_datetime()
    if now.date() in za_holidays or now.weekday() >= 5:
        return now.hour >= 8 and now.hour < 18
    else:
        return now.hour >= 7 and now.hour < 20


class Application(BaseApplication):
    START_STATE = "state_menu"

    async def process_message(self, message: Message) -> List[Message]:
        keyword = re.sub(r"\W+", " ", message.content or "").strip().lower()
        # Exit keywords
        if keyword in (
            "menu",
            "0",
            "main menu",
            "cases",
            "vaccine",
            "vaccines",
            "latest",
        ):
            self.state_name = "state_exit"

        return await super().process_message(message)

    async def state_exit(self):
        return EndState(self, "", helper_metadata={"automation_handle": True})

    async def state_menu(self):
        question = self._(
            "The toll-free hotline is available for all your vaccination questions!\n"
            "Call 0800 029 999\n"
            "\n"
            "⏰ Operating hours for *Registration and appointment queries*\n"
            "Monday to Friday\n"
            "7am-8pm\n"
            "Saturdays, Sundays and Public Holidays\n"
            "8am-6pm\n"
            "\n"
            "---------------------\n"
            "\n"
            "The toll-free hotline is also available for you to call *24 hours a day*, "
            "every day for *Emergencies, health advice and post vaccination queries*\n"
            "\n"
            "---------------------\n"
            "📌 Reply  *0* to return to the main *MENU*"
        )
        return WhatsAppExitButtonState(
            self,
            question=question,
            header=self._("💉 VACCINE SUPPORT"),
            choices=[Choice("call_me_back", self._("Call me back"))],
            # Goes to state_exit for error handling
            error="",
            next="state_full_name",
        )

    async def state_full_name(self):
        question = self._(
            "Please type your NAME\n"
            "(This will be given to the hotline team to use when they call you back)"
        )
        error = self._(
            "Please type your NAME\n"
            "\n"
            "------\n"
            "OR 📌 Reply  *0* to return to the main *MENU*"
        )
        return FreeText(
            self,
            question=question,
            next="state_select_number",
            check=nonempty_validator(error),
        )

    async def state_select_number(self):
        question = self._("Can the hotline team call you back on {number}?").format(
            number=display_phonenumber(self.user.addr)
        )
        return WhatsAppExitButtonState(
            self,
            question=question,
            choices=[
                Choice("this_number", self._("Use this number")),
                Choice("different_number", self._("Use another number")),
            ],
            # Goes back state_exit for error handling
            error="",
            next="state_enter_number",
        )

    async def state_enter_number(self):
        if self.user.answers["state_select_number"] == "this_number":
            self.save_answer("state_enter_number", f"+{self.user.addr.lstrip('+')}")
            return await self.go_to_state("state_get_message_history")

        return FreeText(
            self,
            question=self._("Please TYPE the CELL PHONE NUMBER we can contact you on."),
            next="state_get_message_history",
            check=phone_number_validator(
                self._(
                    "⚠️ Please type a valid cell phone number.\n" "Example _081234567_"
                )
            ),
        )

    async def state_get_message_history(self):
        turn_api = get_turn_api()
        url = urljoin(
            config.TURN_URL, f"v1/contacts/{self.user.addr.lstrip('+')}/messages"
        )

        async with turn_api as session:
            for i in range(3):
                try:
                    response = await session.get(url=url)
                    response_data = await response.json()
                    sentry_sdk.set_context("turn_api", {"response_data": response_data})
                    response.raise_for_status()
                    break
                except HTTP_EXCEPTIONS as e:
                    if i == 2:
                        logger.exception(e)
                        return await self.go_to_state("state_error")
                    else:
                        continue

        def format_message(message: dict) -> str:
            timestamp = datetime.fromtimestamp(
                float(message["timestamp"]), tz=timezone.utc
            )
            timestamp = timestamp.astimezone(TZ_SAST)
            formatted_ts = timestamp.strftime("%Y-%m-%d %H:%M")
            if message["type"] == "text":
                body = message["text"]["body"][:200]
            else:
                body = f"<{message['type']}>"
            direction = message["_vnd"]["v1"]["direction"]
            direction = ">>" if direction == "inbound" else "<<"
            return f"{formatted_ts} {direction}\n {body}"

        length = 0
        formatted_messages = []
        for message in response_data["messages"]:
            formatted_message = format_message(message)
            if length + len(formatted_message) + 1 < 1000:
                formatted_messages.append(formatted_message)
                length += len(formatted_message) + 1
            else:
                break
        self.message_history = "\n".join(formatted_messages)
        return await self.go_to_state("state_submit_request")

    async def state_submit_request(self):
        callback_api = get_callback_api()
        url = urljoin(
            config.CALLBACK_API_URL,
            "/NDoHIncomingWhatsApp/api/CCISecure/SubmitWhatsAppChat",
        )
        try:
            phonenumber = normalise_phonenumber(self.user.answers["state_enter_number"])
        except ValueError:
            phonenumber = re.sub(r"[^\d+]", "", self.user.answers["state_enter_number"])
        data = {
            "DateTimeOfRequest": get_today().isoformat(),
            "CLI": phonenumber,
            "Name": self.user.answers["state_full_name"],
            "Language": "English",
            "ChatHistory": self.message_history,
        }

        async with callback_api as session:
            for i in range(3):
                try:
                    response = await session.post(url=url, json=data)
                    response_text = await response.text()
                    sentry_sdk.set_context(
                        "callback_api",
                        {"request_data": data, "response_text": response_text},
                    )
                    response.raise_for_status()
                    break
                except HTTP_EXCEPTIONS as e:
                    if i == 2:
                        logger.exception(e)
                        return await self.go_to_state("state_error")
                    else:
                        continue
        return await self.go_to_state("state_success")

    async def state_success(self):
        if in_office_hours():
            text = self._(
                "Thank you for confirming. The Hotline team have been informed and "
                "will call you back as soon as possible. Look out for an incoming call "
                "from +27315838817\n"
                "\n"
                "------\n"
                "📌 Reply  *0* to return to the main *MENU*"
            )
        else:
            text = self._(
                "Thank you for confirming. The Hotline team have been informed and "
                "will call you back during their operating hours. Look out for an "
                "incoming call from +27315838817\n"
                "\n"
                "------\n"
                "📌 Reply  *0* to return to the main *MENU*"
            )
        return EndState(self, text)
