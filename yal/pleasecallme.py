import asyncio
import logging
from datetime import timedelta
from subprocess import call
from time import strftime
from urllib.parse import urljoin

import aiohttp

from vaccine.base_application import BaseApplication
from vaccine.states import Choice, EndState, FreeText, WhatsAppButtonState
from vaccine.utils import HTTP_EXCEPTIONS
from vaccine.validators import phone_number_validator
from yal import config, rapidpro, contentrepo
from yal.utils import GENERIC_ERROR, get_current_datetime, normalise_phonenumber, clean_inbound

logger = logging.getLogger(__name__)


def get_lovelife_api():
    return aiohttp.ClientSession(
        timeout=aiohttp.ClientTimeout(total=5),
        headers={
            "Ocp-Apim-Subscription-Key": config.LOVELIFE_TOKEN or "",
            "Content-Type": "application/json",
        },
    )


class Application(BaseApplication):
    START_STATE = "state_please_call_start"
    CALLBACK_RESPONSE_STATE = "state_handle_callback_check_response"

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
                    f"🚨If you are, please call {config.EMERGENCY_NUMBER} now!",
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

        call_time = get_current_datetime() + timedelta(hours=2)

        data = {
            "callback_check_time": call_time.isoformat(),
        }

        error = await rapidpro.update_profile(whatsapp_id, data)
        if error:
            return await self.go_to_state("state_error")

        return await self.go_to_state("state_callback_confirmation")

    async def state_callback_confirmation(self):
        question = self._(
            "\n".join(
                [
                    "🆘HELP!",
                    "*Please call me*",
                    "-----",
                    "",
                    "👩🏾 *Great! I've successfully arranged for a loveLife counsellor to"
                    " call you back.* ✅",
                    "",
                    "It should take around 3 minutes or so. Hang in there.",
                    "",
                    "*1* - OK",
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
                "ok": "state_callme_done",
                "help": "state_out_of_hours",
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
                "no": "state_submit_callback",
            },
        )

    async def state_save_emergency_contact(self):
        msisdn = normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.lstrip(" + ")
        data = {
            "emergency_contact": self.user.answers.get("state_specify_msisdn"),
        }

        error = await rapidpro.update_profile(whatsapp_id, data)
        if error:
            return await self.go_to_state("state_error")
        return await self.go_to_state("state_submit_callback")

    async def state_handle_callback_check_response(self):
        msisdn = normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.lstrip(" + ")
        data = {
            "callback_check_sent": "",
        }

        error = await rapidpro.update_profile(whatsapp_id, data)
        if error:
            return await self.go_to_state("state_error")

        inbound = clean_inbound(self.inbound.content)

        if inbound == "yes i got a callback":
            return await self.go_to_state("state_mainmenu")
        if inbound == "yes but i missed it":
            return await self.go_to_state("state_ask_to_call_again")
        if inbound == "no i m still waiting":
            return await self.go_to_state("state_no_callback_received")

    async def state_no_callback_received(self):
        msg = self._(
            "\n".join(
                [
                    "👩🏾 *Eish! Sorry about that!*",
                    "",
                    "Something must have gone wrong on our side. Apologies for that.",
                ]
            )
        )
        await self.worker.publish_message(self.inbound.reply(msg))
        await asyncio.sleep(0.5)
        return await self.go_to_state("state_ask_to_call_again")

    async def state_ask_to_call_again(self):
        question = self._(
            "\n".join(
                [
                    "🆘HELP!",
                    "*Please call me*",
                    "-----",
                    "",
                    "👩🏾 *Want me to try again?*",
                    "I can try and contact one of my colleagues at loveLife again",
                    " to call you back.",
                    "",
                    "*1* - OK",
                    "*2* - Get help another way",
                    "*3* - No, thanks",
                    "",
                    "----",
                    "*Or reply:*",
                    "*0* - 🏠 Back to Main MENU",
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
            error=self._(GENERIC_ERROR),
            next={
                "ok": "state_retry_callback_choose_number",
                "another way": "state_contact_bwise",
                "no": "state_help_no_longer_needed"
            },
        )

    async def state_retry_callback_choose_number(self):
        question = self._(
            "\n".join(
                [
                    "🆘HELP!",
                    "*Please call me*",
                    "-----",
                    "",
                    "👩🏾 *Which number should we use?*",
                    "",
                    "*1* - My Whatsapp number",
                    "*2* - The previously saved number",
                    "*3* - Another number",
                    "",
                    "----",
                    "*Or reply:*",
                    "*0* - 🏠 Back to Main MENU",
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
            error=self._(GENERIC_ERROR),
            next={
                "whatsapp": "state_submit_callback",
                "previously saved": "state_offer_saved_emergency_contact",
                "another": "state_specify_msisdn"
            },
        )

    async def state_offer_saved_emergency_contact(self):
        msisdn = normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.lstrip(" + ")

        error, fields = await rapidpro.get_profile(whatsapp_id)
        if error:
            return await self.go_to_state("state_error")
        msisdn = fields.get("emergency_contact")
        if msisdn:
            self.save_answer("state_specify_msisdn", msisdn)

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
                    "yes": "state_submit_callback",
                    "no": "state_specify_msisdn",
                },
            )
        else:
            question = self._(
                "\n".join(
                    [
                        "🆘HELP!",
                        "*Please call me*",
                        "-----",
                        "",
                        "*👩🏾 Whoops! I don't have another number saved for you.*",
                        "*Which number should we use?*",
                        "",
                        "*1* - My Whatsapp number",
                        "*2* - Another number",
                        "",
                        "----",
                        "*Or reply:*",
                        "*0* - 🏠 Back to Main MENU",
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
                error=self._(GENERIC_ERROR),
                next={
                    "whatsapp": "state_submit_callback",
                    "another": "state_specify_msisdn"
                },
            )

    async def state_help_no_longer_needed(self):
        question = self._(
            "\n".join(
                [
                    "🆘HELP!",
                    "*Please call me*",
                    "-----",
                    "",
                    "👩🏾 *Are you sure you no longer need help?*",
                    "",
                    "*1* - Yes, I got help",
                    "*2* - This way is too long",
                    "*3* - I've changed my mind",
                    "",
                    "----",
                    "*Or reply:*",
                    "*0* - 🏠 Back to Main MENU",
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
            error=self._(GENERIC_ERROR),
            next={
                "yes": "state_got_help",
                "long": "state_too_long",
                "changed mind": "state_changed_mind"
            },
        )

    async def state_got_help(self):
        msisdn = normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.lstrip(" + ")
        data = {
            "callback_abandon_reason": "got help",
        }

        error = await rapidpro.update_profile(whatsapp_id, data)
        if error:
            return await self.go_to_state("state_error")

        question = self._(
            "\n".join(
                [
                    "🆘HELP!",
                    "*Please call me*",
                    "-----",
                    "",
                    "👩🏾*I'm glad you got the help you needed.*",
                    "",
                    "If you need help again, just reply *HELP* at anytime and ",
                    "one of our loveLife counsellors can call you back.",
                    "",
                    "----",
                    "*0* - 🏠 Back to Main MENU",
                ]
            )
        )
        return WhatsAppButtonState(
            self,
            question=question,
            choices=[
                Choice("menu", "Main Menu"),
            ],
            error=self._(GENERIC_ERROR),
            next={
                "menu": "state_mainmenu",
            },
        )

    async def state_too_long(self):
        msisdn = normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.lstrip(" + ")
        data = {
            "callback_abandon_reason": "too long",
        }

        error = await rapidpro.update_profile(whatsapp_id, data)
        if error:
            return await self.go_to_state("state_error")
        question = self._(
            "\n".join(
                [
                    "🆘HELP!",
                    "*Please call me*",
                    "-----",
                    "",
                    "👩🏾 *Thank you for that feedback, we'll work on it.*",
                    "",
                    "If you need help again, just reply *HELP* at anytime and ",
                    "one of our loveLife counsellors can call you back.",
                    "",
                    "*What do you want to do next?*",
                    "",
                    "*1* - Get help another way"
                    "----",
                    "*Or reply:*",
                    "*0* - 🏠 Back to Main MENU",
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
            error=self._(GENERIC_ERROR),
            next={
                "another way": "state_contact_bwise",
                "menu": "state_mainmenu",
            },
        )

    async def state_changed_mind(self):
        msisdn = normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.lstrip(" + ")
        data = {
            "callback_abandon_reason": "changed mind",
        }

        error = await rapidpro.update_profile(whatsapp_id, data)
        if error:
            return await self.go_to_state("state_error")
        question = self._(
            "\n".join(
                [
                    "🆘HELP!",
                    "*Please call me*",
                    "-----",
                    "",
                    "👩🏾 *No problem. I hope you're no longer in trouble.*",
                    "",
                    "If you need help again, just reply *HELP* at anytime and ",
                    "one of our loveLife counsellors can call you back.",
                    "",
                    "*What do you want to do next?*",
                    "",
                    "*1* - Get help another way"
                    "----",
                    "*Or reply:*",
                    "*0* - 🏠 Back to Main MENU",
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
            error=self._(GENERIC_ERROR),
            next={
                "another way": "state_contact_bwise",
                "menu": "state_mainmenu",
            },
        )

    async def state_contact_bwise(self):
        question = self._(
            "\n".join(
                [
                    "🆘HELP!",
                    "*Get in touch with B-Wise*",
                    "-----",
                    "",
                    "🙍🏾‍♀️*Don't stress. My team at B-Wise have got your back too.* 👊🏾",
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
                    "*0* - 🏠 Back to Main MENU",
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
            error=self._(GENERIC_ERROR),
            next={
                "facebook": "state_facebook_page",
                "twitter": "state_twitter_page",
                "website": "state_website"
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
                    "non-judgmental information on your sexual and reproductive health.",
                    "",
                    "----",
                    "*Or reply:*",
                    "*0* - 🏠 Back to Main MENU",
                ]
            )
        )
        return WhatsAppButtonState(
            self,
            question=question,
            # TODO: Add image to content repo
            # helper_metadata={"image": contentrepo.get_image_url("Screenshot 2022-06-07 at 09.29.20.png")},
            choices=[
                Choice("menu", "Main Menu"),
            ],
            error=self._(GENERIC_ERROR),
            next={
                "menu": "state_mainmenu",
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
                    "non-judgmental information on your sexual and reproductive health.",
                    "",
                    "----",
                    "*Or reply:*",
                    "*0* - 🏠 Back to Main MENU",
                ]
            )
        )
        return WhatsAppButtonState(
            self,
            question=question,
            # TODO: Add image to content repo
            # helper_metadata={"image": contentrepo.get_image_url("Screenshot 2022-06-07 at 09.56.48.png")},
            choices=[
                Choice("menu", "Main Menu"),
            ],
            error=self._(GENERIC_ERROR),
            next={
                "menu": "state_mainmenu",
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
                    "*0* - 🏠 Back to Main MENU",
                ]
            )
        )
        return WhatsAppButtonState(
            self,
            question=question,
            # TODO: Add image to content repo
            # helper_metadata={"image": contentrepo.get_image_url("Screenshot 2022-06-06 at 15.02.53.png")},
            choices=[
                Choice("menu", "Main Menu"),
            ],
            error=self._(GENERIC_ERROR),
            next={
                "menu": "state_mainmenu",
            },
        )
