import asyncio
import logging

from vaccine.base_application import BaseApplication
from vaccine.states import Choice, EndState, FreeText, WhatsAppButtonState
from vaccine.validators import phone_number_validator
from yal.config import EMERGENCY_NUMBER
from yal.utils import GENERIC_ERROR, get_current_datetime

logger = logging.getLogger(__name__)


class Application(BaseApplication):
    START_STATE = "state_please_call_start"

    async def state_please_call_start(self):
        current_datetime = get_current_datetime()

        min_hour = 9
        max_hour = 18
        if current_datetime.weekday() >= 4:
            min_hour = 12
            max_hour = 16

        if current_datetime.hour >= min_hour and current_datetime.hour <= max_hour:
            return await self.go_to_state("state_in_hours_greeting")
        return await self.go_to_state("state_out_of_hours")

    async def state_out_of_hours(self):
        question = self._(
            "\n".join(
                [
                    "🆘HELP! / Please call me",
                    "*Emergency*",
                    "-----",
                    "",
                    "*👩🏾 Are you in trouble?*",
                    "",
                    f"🚨If you are, please call {EMERGENCY_NUMBER} now!",
                    "",
                    "*1* - See opening hours",
                    "",
                    "-----",
                    "*Or reply:*",
                    "*0* - 🏠Back to Main *MENU*",
                ]
            )
        )
        return WhatsAppButtonState(
            self,
            question=question,
            choices=[Choice("see", "See Opening Hours")],
            error=self._(GENERIC_ERROR),
            next="state_open_hours",
        )

    async def state_open_hours(self):
        question = self._(
            "\n".join(
                [
                    "🆘HELP! / Please call me",
                    "*Opening hours*",
                    "-----",
                    "",
                    "🙍🏾‍♀️ *Here's when you can chat with one of our (human) loveLife "
                    "counsellors:*",
                    "",
                    "🗓 *Mon-Fri:* 9 - 7pm",
                    "🗓 *Weekends:* 12 - 5pm",
                    "",
                    "There's usually about a *5 - 7 minutes* waiting time for a "
                    "callback.",
                    "",
                    "*1* - Ok",
                    "*2* - Set a reminder",
                ]
            )
        )
        return WhatsAppButtonState(
            self,
            question=question,
            choices=[
                Choice("ok", "Ok"),
                Choice("reminder", "Set a reminder"),
            ],
            error=self._(GENERIC_ERROR),
            next={
                "ok": "state_mainmenu",
                "reminder": "state_set_reminder",
            },
        )

    async def state_set_reminder(self):
        return EndState(
            self,
            self._("TODO: set reminder"),
            next=self.START_STATE,
        )

    async def state_in_hours_greeting(self):
        await self.worker.publish_message(
            self.inbound.reply(
                self._("👩🏾 *Say no more—I'm on it!*\n☝🏾 Hold tight just a sec..."),
            )
        )
        await asyncio.sleep(0.5)
        return await self.go_to_state("state_in_hours")

    async def state_in_hours(self):
        question = self._(
            "\n".join(
                [
                    "🆘HELP!",
                    "*Please call me*",
                    "-----",
                    "",
                    "👩🏾 *Should we call you on the WhatsApp number you are using to "
                    "chat?*",
                    "",
                    "*1* - Yes, use this number",
                    "*2* - Call me on another number",
                    "",
                    "-----",
                    "Or reply:",
                    "0 - 🏠 Back to Main MENU",
                ]
            )
        )

        return WhatsAppButtonState(
            self,
            question=question,
            choices=[
                Choice("yes", "Use this number"),
                Choice("specify", "Use another number"),
            ],
            error=self._(GENERIC_ERROR),
            next={
                "yes": "state_get_wait_time",
                "specify": "state_specify_msisdn",
            },
        )

    async def state_get_wait_time(self):
        # TODO: Add API call to get this
        self.save_metadata("callback_wait", "5 - 7 min")
        return await self.go_to_state("state_callback_confirmation")

    async def state_callback_confirmation(self):
        wait_time = self.user.metadata["callback_wait"]
        question = self._(
            "\n".join(
                [
                    "🆘HELP!",
                    "*Please call me*",
                    "-----",
                    "",
                    "👩🏾 *Hold tight... I'm getting one of our loveLife counsellors to "
                    "call you back ASAP, OK?*",
                    "",
                    f"It should take around *{wait_time}* minutes or so. Hang in "
                    "there.",
                    "",
                    "*1* - Ok",
                    "*2* - I need help now",
                    "*3* - loveLife OPENING HOURS",
                    "",
                    "-----",
                    "*Or Reply:*",
                    "*0* - 🏠 Back to Main *MENU*",
                ]
            )
        )
        return WhatsAppButtonState(
            self,
            question=question,
            choices=[
                Choice("ok", "Ok"),
                Choice("help", "I need help now"),
                Choice("hours", "Opening hours"),
            ],
            error=self._(GENERIC_ERROR),
            next={
                "ok": "state_submit_callback",
                "help": "state_out_of_hours",
                "hours": "state_open_hours",
            },
        )

    async def state_submit_callback(self):
        return EndState(
            self,
            self._("Done"),
            next=self.START_STATE,
        )

    async def state_specify_msisdn(self):
        question = self._(
            "\n".join(
                [
                    "🆘HELP!",
                    "*Please call me*",
                    "-----",
                    "",
                    "👩🏾*No problem. What number should we use?*",
                    "",
                    "Reply by sending the number.",
                    "",
                    "-----",
                    "*Or reply:*",
                    "*0* - 🏠Back to Main *MENU*",
                ]
            )
        )
        return FreeText(
            self,
            question=question,
            next="state_confirm_specified_msisdn",
            check=phone_number_validator(
                self._(
                    "⚠️ Please type a valid cell phone number.\n" "Example _081234567_"
                )
            ),
        )

    async def state_confirm_specified_msisdn(self):
        msisdn = self.user.answers["state_specify_msisdn"]
        question = self._(
            "\n".join(
                [
                    "🆘HELP!",
                    "*Please call me*",
                    "-----",
                    "",
                    "*👩🏾Is this the right number?*",
                    "",
                    msisdn,
                    "",
                    "*1* - Yes, that's it",
                    "*2* - No, it's wrong",
                    "",
                    "-----",
                    "*Or reply:*",
                    "*0* - 🏠Back to Main *MENU*",
                ]
            )
        )
        return WhatsAppButtonState(
            self,
            question=question,
            choices=[
                Choice("yes", "Yes, that's it"),
                Choice("no", "No, it's wrong"),
            ],
            error=self._(GENERIC_ERROR),
            next={
                "yes": "state_ask_to_save_emergency_number",
                "no": "state_specify_msisdn",
            },
        )

    async def state_ask_to_save_emergency_number(self):
        question = self._(
            "\n".join(
                [
                    "🆘HELP!",
                    "*Please call me*",
                    "-----",
                    "",
                    "*👩🏾Would you like us to save this number for next time?*",
                    "",
                    "*1* - Yes, please",
                    "*2* - No thanks",
                    "-----",
                    "*Or reply:*",
                    "*0* - 🏠Back to Main *MENU*",
                ]
            )
        )
        return WhatsAppButtonState(
            self,
            question=question,
            choices=[
                Choice("yes", "Yes, please"),
                Choice("no", "No thanks"),
            ],
            error=self._(GENERIC_ERROR),
            next={
                "yes": "state_save_emergency_contact",
                "no": "state_get_wait_time",
            },
        )

    async def state_save_emergency_contact(self):
        # TODO: save emergency contact details
        return await self.go_to_state("state_get_wait_time")
