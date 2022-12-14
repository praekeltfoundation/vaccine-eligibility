import asyncio
import logging

from vaccine.base_application import BaseApplication
from vaccine.states import (
    Choice,
    EndState,
    FreeText,
    WhatsAppButtonState,
    WhatsAppListState,
)
from yal import rapidpro, utils
from yal.assessments import Application as AssessmentApplication
from yal.utils import get_current_datetime, get_generic_error
from yal.validators import age_validator

logger = logging.getLogger(__name__)


class Application(BaseApplication):
    START_STATE = "state_persona_name"
    REMINDER_STATE = "state_handle_onboarding_reminder_response"

    async def update_last_onboarding_time(self):
        msisdn = utils.normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.lstrip(" + ")
        data = {
            "last_onboarding_time": get_current_datetime().isoformat(),
            "onboarding_reminder_type": "5 min",
        }

        return await rapidpro.update_profile(whatsapp_id, data, self.user.metadata)

    async def state_persona_name(self):
        await self.update_last_onboarding_time()
        return FreeText(
            self,
            question=self._(
                "\n".join(
                    [
                        "🙋🏾 PERSONALISE YOUR B-WISE BOT / *Give me a name*",
                        "---",
                        "",
                        "*What would you like to call me?*",
                        "It can be any name you like or one that reminds you of "
                        "someone you trust.",
                        "",
                        "Just type and send me your new bot name.",
                        "",
                        '_If you want to do this later, just click the "skip" button._',
                    ]
                )
            ),
            next="state_save_persona_name",
            buttons=[Choice("skip", self._("Skip"))],
        )

    async def state_save_persona_name(self):
        persona_name = self.user.answers.get("state_persona_name")
        if persona_name != "skip":
            self.save_metadata("persona_name", persona_name)
            msg = self._(
                "\n".join(
                    [
                        "Great - from now on you can call me [persona_name].",
                        "",
                        "_You can change this later from the main *MENU.*_",
                    ]
                )
            )
            await self.publish_message(msg)
            await asyncio.sleep(0.5)
            return await self.go_to_state("state_persona_emoji")

        return await self.go_to_state("state_age")

    async def state_persona_emoji(self):
        await self.update_last_onboarding_time()
        return FreeText(
            self,
            question=self._(
                "\n".join(
                    [
                        "🙋🏾 PERSONALISE YOUR B-WISE BOT / *Choose an emoji*",
                        "-----",
                        "",
                        "*Why not use an emoji to accompany my new name?* Send in the "
                        "emoji you'd like to use, now.",
                        "",
                        '_If you want to do this later, just click the "skip" button._',
                    ]
                )
            ),
            next="state_save_persona_emoji",
            buttons=[Choice("skip", self._("Skip"))],
        )

    async def state_save_persona_emoji(self):
        persona_emoji = self.user.answers.get("state_persona_emoji")
        if persona_emoji != "skip":
            self.save_metadata("persona_emoji", persona_emoji)

        return await self.go_to_state("state_profile_intro")

    async def state_profile_intro(self):
        msg = self._(
            "\n".join(
                [
                    "[persona_emoji] Great! I'm just going to ask you a few "
                    "quick questions now to get to know you better.",
                ]
            )
        )
        await self.publish_message(msg)
        await asyncio.sleep(0.5)
        return await self.go_to_state("state_age")

    async def state_age(self):
        await self.update_last_onboarding_time()
        return FreeText(
            self,
            question=self._(
                "\n".join(
                    [
                        "ABOUT YOU / 🍰*Age*",
                        "-----",
                        "",
                        "*What is your age?*",
                        "Type in the number only (e.g. 24)",
                    ]
                )
            ),
            next="state_gender",
            check=age_validator(
                self._(
                    "\n".join(
                        [
                            "Hmm, something looks a bit off to me. Can we try again? "
                            "Remember to *only use numbers*. 👍🏽",
                            "",
                            "For example just send in *17* if you are 17 years old.",
                        ]
                    )
                )
            ),
        )

    async def state_gender(self):
        await self.update_last_onboarding_time()
        gender_choices = [Choice(code, name) for code, name in utils.GENDERS.items()]

        question = self._(
            "\n".join(
                [
                    "ABOUT YOU / 🌈 *Your identity*",
                    "-----",
                    "",
                    "*Which gender do you most identify with?*",
                    "",
                    "_Tap the button and select the option you think best fits._",
                ]
            )
        )
        return WhatsAppListState(
            self,
            question=question,
            button="Gender",
            choices=gender_choices,
            next="state_rel_status",
            error=self._(get_generic_error()),
        )

    async def state_rel_status(self):
        await self.update_last_onboarding_time()
        rel_status_choices = [
            Choice("relationship", "Yes, seeing someone"),
            Choice("single", "No, I'm single"),
            Choice("complicated", "It's complicated"),
        ]

        question = self._(
            "\n".join(
                [
                    "ABOUT YOU / 👩🏾‍❤️‍💋‍👩🏽 *Relationship status*",
                    "-----",
                    "",
                    "*Awesome! One last thing "
                    "— are you seeing someone special right now?*",
                    "",
                    "_Tap the button and select the option that "
                    "best describes your situation.._",
                ]
            )
        )
        return WhatsAppListState(
            self,
            question=question,
            button="Relationship status",
            choices=rel_status_choices,
            next="state_submit_onboarding",
            error=self._(get_generic_error()),
        )

    async def state_submit_onboarding(self):
        msisdn = utils.normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.lstrip(" + ")
        persona_name = self.user.answers.get("state_persona_name", "")
        persona_emoji = self.user.answers.get("state_persona_emoji", "")

        data = {
            "opted_out": "FALSE",
            "onboarding_completed": "True",
            "persona_name": persona_name if persona_name != "skip" else "",
            "persona_emoji": persona_emoji if persona_emoji != "skip" else "",
            "age": self.user.answers.get("state_age"),
            "gender": self.user.answers.get("state_gender"),
            "relationship_status": self.user.answers.get("state_rel_status", ""),
            "onboarding_reminder_sent": "",
            "onboarding_reminder_type": "",
        }

        error = await rapidpro.update_profile(whatsapp_id, data, self.user.metadata)
        if error:
            return await self.go_to_state("state_error")

        return await self.go_to_state("state_onboarding_complete")

    async def state_onboarding_complete(self):
        msg = self._(
            "\n".join(
                [
                    "🙏🏾 Lekker! Your profile is all set up!",
                    "",
                    "Let's get you started!",
                ]
            )
        )

        await self.publish_message(msg)
        return await self.go_to_state("state_sexual_literacy_assessment_start")

    async def state_sexual_literacy_assessment_start(self):
        msg = self._(
            "\n".join(
                [
                    "*You and your sexual health*",
                    "-----",
                    "",
                    "[persona_emoji] I've got a tonne of answers and info about sex, "
                    "love and relationships.",
                    "",
                    "To point you in the right direction, "
                    "I want to quickly check what you already know.",
                ]
            )
        )
        await self.publish_message(msg)
        await asyncio.sleep(0.5)
        question = self._(
            "\n".join(
                [
                    "I'll ask a few questions. For each question "
                    "I just need you to choose the answer that feels right to you."
                ]
            )
        )

        self.save_metadata(
            "assessment_end_state", "state_sexual_literacy_assessment_end"
        )

        return WhatsAppButtonState(
            app=self,
            question=question,
            choices=[Choice("ok", "OK, let's start!")],
            error=get_generic_error(),
            next=AssessmentApplication.START_STATE,
        )

    async def state_sexual_literacy_assessment_end(self):
        msg = "\n".join(
            [
                "🏁 🎉",
                "",
                "*Awesome. That's all the questions for now!*",
                "",
                "🤦🏾‍♂️ Thanks for being so patient and honest 😌.",
            ]
        )
        return EndState(self, msg)

        # TODO: Go down different path depending on assessment outcome

    async def state_stop_onboarding_reminders(self):
        msisdn = utils.normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.lstrip(" + ")
        data = {
            "onboarding_reminder_sent": "",
            "onboarding_reminder_type": "",
        }  # Reset the fields

        error = await rapidpro.update_profile(whatsapp_id, data, self.user.metadata)
        if error:
            return await self.go_to_state("state_error")

        return FreeText(
            self,
            question=self._(
                "\n".join(
                    [
                        "Got it.",
                        "",
                        "*Remember* — you can update your info at any time.",
                        "You can change this later from the main *MENU*.",
                        "",
                        "*1* - OK, got it 👍",
                    ]
                )
            ),
            next=self.START_STATE,
            buttons=[Choice("ok", self._("OK, got it 👍"))],
        )

    async def state_reschedule_onboarding_reminders(self):
        msisdn = utils.normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.lstrip(" + ")
        data = {
            "onboarding_reminder_sent": "",  # Reset the field
            "onboarding_reminder_type": "2 hrs",
            "last_onboarding_time": get_current_datetime().isoformat(),
        }

        error = await rapidpro.update_profile(whatsapp_id, data, self.user.metadata)
        if error:
            return await self.go_to_state("state_error")

        return FreeText(
            self,
            question=self._(
                "\n".join(
                    [
                        "🙍🏾‍♀️Got it.",
                        "",
                        "👩🏾 *Remember* — you can update your info at any time. Just ",
                        "choose *UPDATE/CHANGE PERSONAL INFO* from the Main *MENU*.",
                        "",
                        "*1* - OK, got it 👍",
                    ]
                )
            ),
            next=self.START_STATE,
            buttons=[Choice("ok", self._("1 - OK, got it 👍"))],
        )

    async def state_handle_onboarding_reminder_response(self):
        inbound = utils.clean_inbound(self.inbound.content)
        if inbound == "continue":
            msisdn = utils.normalise_phonenumber(self.inbound.from_addr)
            whatsapp_id = msisdn.lstrip(" + ")
            data = {
                "onboarding_reminder_sent": "",  # Reset the field
            }

            error = await rapidpro.update_profile(whatsapp_id, data, self.user.metadata)
            if error:
                return await self.go_to_state("state_error")
            return await self.go_to_state("state_persona_name")

        if inbound == "no thanks" or inbound == "not interested":
            return await self.go_to_state("state_stop_onboarding_reminders")

        if inbound == "remind me later":
            return await self.go_to_state("state_reschedule_onboarding_reminders")
