import asyncio
import logging
from datetime import datetime, timedelta
from urllib.parse import urljoin

import aiohttp

from vaccine.base_application import BaseApplication
from vaccine.states import Choice, EndState, FreeText, WhatsAppButtonState
from vaccine.utils import HTTP_EXCEPTIONS, get_display_choices
from yal import config, rapidpro
from yal.change_preferences import Application as ChangePreferencesApplication
from yal.utils import (
    BACK_TO_MAIN,
    GET_HELP,
    get_current_datetime,
    get_generic_error,
    normalise_phonenumber,
)
from yal.validators import phone_number_validator

logger = logging.getLogger(__name__)


async def on_request_start(session, context, params):
    context.request_start = asyncio.get_event_loop().time()


async def on_request_end(session, context, params):
    elapsed_time = round(
        (asyncio.get_event_loop().time() - context.request_start) * 1000
    )
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    msisdn = context.trace_request_ctx["msisdn"]
    logger.info(
        f"[{now}] Lovelife request (msisdn:{msisdn}) - {elapsed_time}ms <{params.url}>"
    )


def get_lovelife_api():
    trace_config = aiohttp.TraceConfig()
    trace_config.on_request_start.append(on_request_start)
    trace_config.on_request_end.append(on_request_end)

    return aiohttp.ClientSession(
        timeout=aiohttp.ClientTimeout(total=5),
        headers={
            "Ocp-Apim-Subscription-Key": config.LOVELIFE_TOKEN or "",
            "Content-Type": "application/json",
        },
        trace_configs=[trace_config],
    )


class Application(BaseApplication):
    START_STATE = "state_please_call_start"
    CALLBACK_RESPONSE_STATE = "state_handle_callback_check_response"
    CONFIRM_REDIRECT = "state_confirm_redirect_please_call_me"

    async def state_please_call_start(self):
        current_datetime = get_current_datetime()

        min_hour = 9
        max_hour = 18
        if current_datetime.weekday() >= 4:
            min_hour = 12
            max_hour = 16

        if current_datetime.hour >= min_hour and current_datetime.hour <= max_hour:
            return await self.go_to_state("state_in_hours_greeting")

        if current_datetime.hour < min_hour:
            next_available = current_datetime.replace(hour=min_hour, minute=0, second=0)
        if current_datetime.hour > max_hour:
            next_available = current_datetime + timedelta(days=1)
            if current_datetime.weekday() in [4, 5]:
                next_available = next_available.replace(hour=12, minute=0, second=0)
            else:
                next_available = next_available.replace(hour=9, minute=0, second=0)
        self.save_metadata("next_available", next_available.isoformat())
        return await self.go_to_state("state_out_of_hours")

    async def state_out_of_hours(self):
        next_available = self.user.metadata.get("next_available")
        next_avail_time = datetime.fromisoformat(next_available)
        next_avail_str = next_avail_time.strftime("%H:00")
        if next_avail_time.date() != get_current_datetime().date():
            next_avail_str = f"{next_avail_str} tomorrow"
        question = self._(
            "\n".join(
                [
                    "NEED HELP? / *Talk to a counsellor*",
                    "-----",
                    "",
                    "[persona_emoji] *Eish! Our loveLife counsellors are all offline "
                    "right now...*",
                    "",
                    f"A loveLife counsellor will be available from {next_avail_str}",
                    "",
                    "*1* - 🚨I need help now!",
                    "*2* - See opening hours",
                    "",
                    "-----",
                    "*Or reply:*",
                    BACK_TO_MAIN,
                ]
            )
        )
        return WhatsAppButtonState(
            self,
            question=question,
            choices=[
                Choice("help now", "I need help now!"),
                Choice("opening hours", "See opening hours"),
            ],
            error=self._(get_generic_error()),
            next={
                "help now": "state_emergency",
                "opening hours": "state_open_hours",
            },
        )

    async def state_emergency(self):
        question = self._(
            "\n".join(
                [
                    "NEED HELP? / Talk to a counsellor / *Emergency*",
                    "-----",
                    "",
                    "[persona_emoji] *Are you in trouble?*",
                    "",
                    f"🚨If you are, please call {config.EMERGENCY_NUMBER} now!",
                    "",
                    "*1* - See opening hours",
                    "",
                    "-----",
                    "*Or reply:*",
                    BACK_TO_MAIN,
                ]
            )
        )
        return WhatsAppButtonState(
            self,
            question=question,
            choices=[Choice("see", "See Opening Hours")],
            error=self._(get_generic_error()),
            next="state_open_hours",
        )

    async def state_open_hours(self):
        question = self._(
            "\n".join(
                [
                    "NEED HELP? / Talk to a counsellor / *Opening hours*",
                    "-----",
                    "",
                    "[persona_emoji] *Here's when you can chat with one of our (human) "
                    "loveLife counsellors:*",
                    "",
                    "🗓 *Mon-Fri:* 9 - 7pm",
                    "🗓 *Weekends:* 12 - 5pm",
                    "",
                    "There's usually about a *5 - 7 minutes* waiting time for a "
                    "callback.",
                    "",
                    "*1* - Ok",
                    "*2* - Call me when you open",
                ]
            )
        )
        return WhatsAppButtonState(
            self,
            question=question,
            choices=[
                Choice("ok", "Ok"),
                Choice("callback in hours", "Call me when you open"),
            ],
            error=self._(get_generic_error()),
            next={
                "ok": "state_pre_mainmenu",
                "callback in hours": "state_in_hours_greeting",
            },
        )

    async def state_in_hours_greeting(self):
        await self.publish_message(
            self._(
                "[persona_emoji] *Say no more—I'm on it!*\n☝🏾 Hold tight just a sec..."
            ),
        )
        await asyncio.sleep(0.5)
        await self.publish_message(
            self._(
                "\n".join(
                    [
                        "📞 A trained loveLife counsellor will call you back.",
                        "",
                        "They'll be able to talk to you about any sex, relationship"
                        " and mental health questions you may have or issues you"
                        " may be facing.",
                    ]
                )
            )
        )
        await asyncio.sleep(0.5)
        return await self.go_to_state("state_in_hours")

    async def state_in_hours(self):
        question = self._(
            "\n".join(
                [
                    "NEED HELP? / *Talk to a counsellor*",
                    "-----",
                    "",
                    "[persona_emoji] *Should a counsellor call you on the WhatsApp "
                    "number you are using to chat?*",
                    "",
                    "*1* - Yes, use this number",
                    "*2* - Call me on another number",
                    "",
                    "-----",
                    "Or reply:",
                    BACK_TO_MAIN,
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
            error=self._(get_generic_error()),
            next={
                "yes": "state_submit_callback",
                "specify": "state_specify_msisdn",
            },
        )

    async def state_submit_callback(self):
        answers = self.user.answers
        msisdn = normalise_phonenumber(
            answers.get("state_specify_msisdn", self.inbound.from_addr)
        )
        async with get_lovelife_api() as session:
            for i in range(3):
                try:
                    response = await session.post(
                        url=urljoin(config.LOVELIFE_URL, "/lovelife/v1/queuemessage"),
                        json={
                            "PhoneNumber": msisdn,
                            "SourceSystem": "Bwise by Young Africa live WhatsApp bot",
                        },
                        trace_request_ctx={"msisdn": f"*{msisdn[-4:]}"},
                    )
                    response.raise_for_status()
                    break
                except HTTP_EXCEPTIONS as e:
                    if i == 2:
                        logger.exception(e)
                        return await self.go_to_state("state_error")
                    else:
                        continue

        return await self.go_to_state("state_save_time_for_callback_check")

    async def state_save_time_for_callback_check(self):
        msisdn = normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.lstrip(" + ")

        meta = self.user.metadata
        next_available = meta.get("next_available", get_current_datetime())
        if type(next_available) == str:
            next_available = datetime.fromisoformat(next_available)
        call_time = next_available + timedelta(hours=2)

        data = {
            "callback_check_time": call_time.isoformat(),
        }

        error = await rapidpro.update_profile(whatsapp_id, data, self.user.metadata)
        if error:
            return await self.go_to_state("state_error")

        return await self.go_to_state("state_callback_confirmation")

    async def state_callback_confirmation(self):
        question = self._(
            "\n".join(
                [
                    "NEED HELP? / *Talk to a counsellor*",
                    "-----",
                    "",
                    "[persona_emoji] *Great! I've successfully arranged for a loveLife "
                    "counsellor to call you back.* ✅",
                    "",
                    "It should take around 3 minutes or so. Hang in there.",
                    "",
                    "*1* - OK",
                    "*2* - I need help now",
                    "*3* - loveLife OPENING HOURS",
                    "",
                    "-----",
                    "*Or Reply:*",
                    BACK_TO_MAIN,
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
            error=self._(get_generic_error()),
            next={
                "ok": "state_callme_done",
                "help": "state_emergency",
                "hours": "state_open_hours",
            },
        )

    async def state_callme_done(self):
        return EndState(
            self,
            self._("Done"),
            next=self.START_STATE,
        )

    async def state_specify_msisdn(self):
        question = self._(
            "\n".join(
                [
                    "NEED HELP? / *Talk to a counsellor*",
                    "-----",
                    "",
                    "[persona_emoji] *No problem. What number should we use?*",
                    "",
                    "Reply by sending the number.",
                    "",
                    "-----",
                    "*Or reply:*",
                    BACK_TO_MAIN,
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
                    "NEED HELP? / *Talk to a counsellor*",
                    "-----",
                    "",
                    "[persona_emoji] *Is this the right number?*",
                    "",
                    msisdn,
                    "",
                    "*1* - Yes, that's it",
                    "*2* - No, it's wrong",
                    "",
                    "-----",
                    "*Or reply:*",
                    BACK_TO_MAIN,
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
            error=self._(get_generic_error()),
            next={
                "yes": "state_ask_to_save_emergency_number",
                "no": "state_specify_msisdn",
            },
        )

    async def state_ask_to_save_emergency_number(self):
        question = self._(
            "\n".join(
                [
                    "NEED HELP? / *Talk to a counsellor*",
                    "-----",
                    "",
                    "[persona_emoji] *Would you like us to save this number for next "
                    "time?*",
                    "",
                    "*1* - Yes, please",
                    "*2* - No thanks",
                    "-----",
                    "*Or reply:*",
                    BACK_TO_MAIN,
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
            error=self._(get_generic_error()),
            next={
                "yes": "state_save_emergency_contact",
                "no": "state_submit_callback",
            },
        )

    async def state_save_emergency_contact(self):
        msisdn = normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.lstrip(" + ")
        data = {
            "emergency_contact": self.user.answers.get("state_specify_msisdn"),
        }

        error = await rapidpro.update_profile(whatsapp_id, data, self.user.metadata)
        if error:
            return await self.go_to_state("state_error")
        return await self.go_to_state("state_submit_callback")

    async def state_handle_callback_check_response(self):
        question = self._(
            "\n".join(
                [
                    "*1* - 😌 Yes, I got a callback",
                    "*2* - 😬 Yes, but I missed it",
                    "*3* - 😠 No I'm still waiting",
                ]
            )
        )
        return WhatsAppButtonState(
            self,
            question=question,
            choices=[
                Choice("yes", "I got the call"),
                Choice("missed", "I missed the call"),
                Choice("no", "No call yet"),
            ],
            error=self._(get_generic_error()),
            next={
                "yes": "state_collect_call_feedback",
                "missed": "state_ask_to_call_again",
                "no": "state_no_callback_received",
            },
        )

    async def state_collect_call_feedback(self):
        msisdn = normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.lstrip(" + ")
        data = {
            "last_mainmenu_time": get_current_datetime().isoformat(),
        }
        error = await rapidpro.update_profile(whatsapp_id, data, self.user.metadata)
        if error:
            return await self.go_to_state("state_error")

        question = self._(
            "\n".join(
                [
                    "I'm glad you got a chance to talk to someone.",
                    "",
                    "Did you find the call helpful?",
                    "",
                    "*1* - Yes, very helpful",
                    "*2* - No, not really",
                    "-----",
                    "*Or reply:*",
                    BACK_TO_MAIN,
                ]
            )
        )
        return WhatsAppButtonState(
            self,
            question=question,
            choices=[
                Choice("yes", "Yes, very helpful"),
                Choice("no", "No, not really"),
            ],
            error=self._(get_generic_error()),
            next={
                "yes": "state_call_helpful",
                "no": "state_call_not_helpful_feedback",
            },
        )

    async def state_call_helpful(self):
        choices = [
            Choice("question", self._("Ask a question")),
            Choice("update", self._("Update your info")),
            Choice("counsellor", self._("Talk to a counsellor")),
        ]

        question = self._(
            "\n".join(
                [
                    "I'm so happy to hear that.",
                    "",
                    "Remember, if you need help from a loveLife counsellor, just "
                    "request a call back any time.",
                    "",
                    "*What would you like to do now?*",
                    "1. Ask a question",
                    "2. Update your information",
                    "3. Talk to a counsellor",
                    "",
                    "--",
                    "*Or reply*",
                    BACK_TO_MAIN,
                ]
            )
        )
        return WhatsAppButtonState(
            self,
            question=question,
            choices=choices,
            error=self._(get_generic_error()),
            next={
                "question": "state_aaq_start",
                "update": ChangePreferencesApplication.START_STATE,
                "counsellor": self.START_STATE,
            },
        )

    async def state_call_not_helpful_feedback(self):
        question = self._(
            "\n".join(
                [
                    "I'm sorry to hear that your call was not very helpful 👎🏾",
                    "",
                    "Please tell me about your experience. What went wrong?",
                    "",
                    "_Just type and send your answer_",
                    "",
                    "-----",
                    "*Or reply*",
                    BACK_TO_MAIN,
                ]
            )
        )
        return FreeText(
            self,
            question=question,
            next="state_call_not_helpful_try_again",
        )

    async def state_call_not_helpful_try_again(self):
        choices = [
            Choice("yes", self._("Yes, It might help")),
            Choice("no", self._("No, thanks")),
        ]

        question = self._(
            "\n".join(
                [
                    "Thank you so much for sharing your feedback with me, I'll see "
                    "what I can do about it.",
                    "",
                    "*Would you like to try speaking to a loveLife counsellor again "
                    "about this?*",
                    "",
                    get_display_choices(choices),
                    "",
                    "--",
                    "*Or reply*",
                    BACK_TO_MAIN,
                ]
            )
        )
        return WhatsAppButtonState(
            self,
            question=question,
            choices=choices,
            error=self._(get_generic_error()),
            next={
                "yes": "state_please_call_start",
                "no": "state_call_not_helpful_try_again_declined",
            },
        )

    async def state_call_not_helpful_try_again_declined(self):
        choices = [
            Choice("question", self._("Ask a question")),
            Choice("update", self._("Update your info")),
        ]

        question = self._(
            "\n".join(
                [
                    "No problem.",
                    "",
                    "*What would you like to do now?*",
                    "",
                    "1. Ask a question",
                    "2. Update your information",
                    "3. Talk to a counsellor",
                    "",
                    "--",
                    "*Or reply*",
                    BACK_TO_MAIN,
                    GET_HELP,
                ]
            )
        )
        return WhatsAppButtonState(
            self,
            question=question,
            choices=choices,
            error=self._(get_generic_error()),
            next={
                "question": "state_aaq_start",
                "update": ChangePreferencesApplication.START_STATE,
            },
        )

    async def state_no_callback_received(self):
        msg = self._(
            "\n".join(
                [
                    "[persona_emoji] *Eish! Sorry about that!*",
                    "",
                    "Something must have gone wrong on our side. Apologies for that.",
                ]
            )
        )
        await self.publish_message(msg)
        await asyncio.sleep(0.5)
        return await self.go_to_state("state_ask_to_call_again")

    async def state_ask_to_call_again(self):
        question = self._(
            "\n".join(
                [
                    "NEED HELP? / *Talk to a counsellor*",
                    "-----",
                    "",
                    "[persona_emoji] *Want me to try again?*",
                    "I can try and contact one of my colleagues at loveLife again",
                    " to call you back.",
                    "",
                    "*1* - OK",
                    "*2* - Get help another way",
                    "*3* - No, thanks",
                    "",
                    "----",
                    "*Or reply:*",
                    BACK_TO_MAIN,
                ]
            )
        )
        return WhatsAppButtonState(
            self,
            question=question,
            choices=[
                Choice("ok", "OK"),
                Choice("another way", "Get help another way"),
                Choice("no", "No, thanks"),
            ],
            error=self._(get_generic_error()),
            next={
                "ok": "state_retry_callback_choose_number",
                "another way": "state_contact_bwise",
                "no": "state_help_no_longer_needed",
            },
        )

    async def state_retry_callback_choose_number(self):
        question = self._(
            "\n".join(
                [
                    "NEED HELP? / *Talk to a counsellor*",
                    "-----",
                    "",
                    "[persona_emoji] *Which number should we use?*",
                    "",
                    "*1* - My Whatsapp number",
                    "*2* - The previously saved number",
                    "*3* - Another number",
                    "",
                    "----",
                    "*Or reply:*",
                    BACK_TO_MAIN,
                ]
            )
        )
        return WhatsAppButtonState(
            self,
            question=question,
            choices=[
                Choice("whatsapp", "Whatsapp number"),
                Choice("previously saved", "Previously saved"),
                Choice("another", "Another number"),
            ],
            error=self._(get_generic_error()),
            next={
                "whatsapp": "state_submit_callback",
                "previously saved": "state_offer_saved_emergency_contact",
                "another": "state_specify_msisdn",
            },
        )

    async def state_offer_saved_emergency_contact(self):
        msisdn = self.user.metadata.get("emergency_contact")
        if msisdn:
            self.save_answer("state_specify_msisdn", msisdn)

            question = self._(
                "\n".join(
                    [
                        "NEED HELP? / *Talk to a counsellor*",
                        "-----",
                        "",
                        "[persona_emoji] *Is this the right number?*",
                        "",
                        msisdn,
                        "",
                        "*1* - Yes, that's it",
                        "*2* - No, it's wrong",
                        "",
                        "-----",
                        "*Or reply:*",
                        BACK_TO_MAIN,
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
                error=self._(get_generic_error()),
                next={
                    "yes": "state_submit_callback",
                    "no": "state_specify_msisdn",
                },
            )
        else:
            question = self._(
                "\n".join(
                    [
                        "NEED HELP? / *Talk to a counsellor*",
                        "-----",
                        "",
                        "[persona_emoji] *Whoops! I don't have another number saved "
                        "for you.*",
                        "*Which number should we use?*",
                        "",
                        "*1* - My Whatsapp number",
                        "*2* - Another number",
                        "",
                        "----",
                        "*Or reply:*",
                        BACK_TO_MAIN,
                    ]
                )
            )
            return WhatsAppButtonState(
                self,
                question=question,
                choices=[
                    Choice("whatsapp", "Whatsapp number"),
                    Choice("another", "Another number"),
                ],
                error=self._(get_generic_error()),
                next={
                    "whatsapp": "state_submit_callback",
                    "another": "state_specify_msisdn",
                },
            )

    async def state_help_no_longer_needed(self):
        question = self._(
            "\n".join(
                [
                    "NEED HELP? / *Talk to a counsellor*",
                    "-----",
                    "",
                    "[persona_emoji] *Are you sure you no longer need help?*",
                    "",
                    "*1* - Yes, I got help",
                    "*2* - This way is too long",
                    "*3* - I've changed my mind",
                    "",
                    "----",
                    "*Or reply:*",
                    BACK_TO_MAIN,
                ]
            )
        )
        return WhatsAppButtonState(
            self,
            question=question,
            choices=[
                Choice("yes", "Yes, I got help"),
                Choice("long", "This way is too long"),
                Choice("changed mind", "I've changed my mind"),
            ],
            error=self._(get_generic_error()),
            next={
                "yes": "state_got_help",
                "long": "state_too_long",
                "changed mind": "state_changed_mind",
            },
        )

    async def state_got_help(self):
        msisdn = normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.lstrip(" + ")
        data = {
            "callback_abandon_reason": "got help",
        }

        error = await rapidpro.update_profile(whatsapp_id, data, self.user.metadata)
        if error:
            return await self.go_to_state("state_error")

        question = self._(
            "\n".join(
                [
                    "NEED HELP? / *Talk to a counsellor*",
                    "-----",
                    "",
                    "[persona_emoji] *I'm glad you got the help you needed.*",
                    "",
                    "If you need help again, just reply *HELP* at anytime and ",
                    "one of our loveLife counsellors can call you back.",
                    "",
                    "----",
                    BACK_TO_MAIN,
                ]
            )
        )
        return WhatsAppButtonState(
            self,
            question=question,
            choices=[
                Choice("menu", "Main Menu"),
            ],
            error=self._(get_generic_error()),
            next={
                "menu": "state_pre_mainmenu",
            },
        )

    async def state_too_long(self):
        msisdn = normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.lstrip(" + ")
        data = {
            "callback_abandon_reason": "too long",
        }

        error = await rapidpro.update_profile(whatsapp_id, data, self.user.metadata)
        if error:
            return await self.go_to_state("state_error")
        question = self._(
            "\n".join(
                [
                    "NEED HELP? / *Talk to a counsellor*",
                    "-----",
                    "",
                    "[persona_emoji] *Thank you for that feedback, we'll work on it.*",
                    "",
                    "If you need help again, just reply *HELP* at anytime and ",
                    "one of our loveLife counsellors can call you back.",
                    "",
                    "*What do you want to do next?*",
                    "",
                    "*1* - Get help another way" "----",
                    "*Or reply:*",
                    BACK_TO_MAIN,
                ]
            )
        )
        return WhatsAppButtonState(
            self,
            question=question,
            choices=[
                Choice("another way", "Get help another way"),
                Choice("menu", "Main Menu"),
            ],
            error=self._(get_generic_error()),
            next={
                "another way": "state_contact_bwise",
                "menu": "state_pre_mainmenu",
            },
        )

    async def state_changed_mind(self):
        msisdn = normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.lstrip(" + ")
        data = {
            "callback_abandon_reason": "changed mind",
        }

        error = await rapidpro.update_profile(whatsapp_id, data, self.user.metadata)
        if error:
            return await self.go_to_state("state_error")
        question = self._(
            "\n".join(
                [
                    "NEED HELP? / *Talk to a counsellor*",
                    "-----",
                    "",
                    "[persona_emoji] *No problem. I hope you're no longer in trouble.*",
                    "",
                    "If you need help again, just reply *HELP* at anytime and ",
                    "one of our loveLife counsellors can call you back.",
                    "",
                    "*What do you want to do next?*",
                    "",
                    "*1* - Get help another way" "----",
                    "*Or reply:*",
                    BACK_TO_MAIN,
                ]
            )
        )
        return WhatsAppButtonState(
            self,
            question=question,
            choices=[
                Choice("another way", "Get help another way"),
                Choice("menu", "Main Menu"),
            ],
            error=self._(get_generic_error()),
            next={
                "another way": "state_contact_bwise",
                "menu": "state_pre_mainmenu",
            },
        )

    async def state_contact_bwise(self):
        question = self._(
            "\n".join(
                [
                    "NEED HELP? / *Talk to a counsellor*",
                    "-----",
                    "",
                    "[persona_emoji] *Don't stress. My team at B-Wise have got your "
                    "back too.* 👊🏾",
                    "",
                    "You can get in touch with one of my them via social media now.",
                    "",
                    "*How would you like to connect with B-Wise?*",
                    "",
                    "*1* - Facebook",
                    "*2* - Twitter",
                    "*3* - Website",
                    "",
                    "----",
                    "*Or reply:*",
                    BACK_TO_MAIN,
                ]
            )
        )
        return WhatsAppButtonState(
            self,
            question=question,
            choices=[
                Choice("facebook", "Facebook"),
                Choice("twitter", "Twitter"),
                Choice("website", "Website"),
            ],
            error=self._(get_generic_error()),
            next={
                "facebook": "state_facebook_page",
                "twitter": "state_twitter_page",
                "website": "state_website",
            },
        )

    async def state_facebook_page(self):
        question = self._(
            "\n".join(
                [
                    "*B-Wise by Young Africa Live on Facebook*",
                    "",
                    "www.facebook.com/BWiseHealth/👆🏾",
                    "",
                    "We are here to help you find sex-positive, youth-friendly, and ",
                    "non-judgmental information on your sexual and reproductive "
                    "health.",
                    "",
                    "----",
                    "*Or reply:*",
                    BACK_TO_MAIN,
                ]
            )
        )
        return WhatsAppButtonState(
            self,
            question=question,
            # TODO: Add image to content repo
            # helper_metadata={"image": contentrepo.get_image_url(
            #   "Screenshot 2022-06-07 at 09.29.20.png")},
            choices=[
                Choice("menu", "Main Menu"),
            ],
            error=self._(get_generic_error()),
            next={
                "menu": "state_pre_mainmenu",
            },
        )

    async def state_twitter_page(self):
        question = self._(
            "\n".join(
                [
                    "*@BWiseHealth (B-Wise by Young Africa Live) · Twitter*",
                    "",
                    "https://twitter.com/BWiseHealth👆🏾",
                    "",
                    "We are here to help you find sex-positive, youth-friendly, and ",
                    "non-judgmental information on your sexual and reproductive "
                    "health.",
                    "",
                    "----",
                    "*Or reply:*",
                    BACK_TO_MAIN,
                ]
            )
        )
        return WhatsAppButtonState(
            self,
            question=question,
            # TODO: Add image to content repo
            # helper_metadata={"image": contentrepo.get_image_url(
            #   "Screenshot 2022-06-07 at 09.56.48.png")},
            choices=[
                Choice("menu", "Main Menu"),
            ],
            error=self._(get_generic_error()),
            next={
                "menu": "state_pre_mainmenu",
            },
        )

    async def state_website(self):
        question = self._(
            "\n".join(
                [
                    "*Need quick answers?*",
                    "*Check out B-Wise online!*",
                    "",
                    "https://bwisehealth.com/👆🏾",
                    "",
                    "You'll find loads of sex, relationships and health info there. ",
                    "It's also my other virtual office.",
                    "",
                    "Feel free to drop me a virtual _howzit_ there too!",
                    "",
                    "----",
                    "*Or reply:*",
                    BACK_TO_MAIN,
                ]
            )
        )
        return WhatsAppButtonState(
            self,
            question=question,
            # TODO: Add image to content repo
            # helper_metadata={"image": contentrepo.get_image_url(
            #   "Screenshot 2022-06-06 at 15.02.53.png")},
            choices=[
                Choice("menu", "Main Menu"),
            ],
            error=self._(get_generic_error()),
            next={
                "menu": "state_pre_mainmenu",
            },
        )

    async def state_confirm_redirect_please_call_me(self):
        user_input = self.inbound.content
        question = self._(
            "\n".join(
                [
                    f'Hi, would you like to talk to someone about "{user_input}"?',
                    "",
                    "----",
                    "*Or reply:*",
                    BACK_TO_MAIN,
                ]
            )
        )
        return WhatsAppButtonState(
            self,
            question=question,
            choices=[
                Choice("yes", "Yes"),
                Choice("no", "No"),
            ],
            error=self._(get_generic_error()),
            next={
                "yes": "state_please_call_start",
                "no": self.user.metadata["emergency_keyword_previous_state"],
            },
        )
