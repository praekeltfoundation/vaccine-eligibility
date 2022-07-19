import asyncio
import logging
from datetime import timedelta

from vaccine.base_application import BaseApplication
from vaccine.states import (
    Choice,
    EndState,
    FreeText,
    WhatsAppButtonState,
    WhatsAppListState,
)
from yal import rapidpro
from yal.utils import (
    GENERIC_ERROR,
    clean_inbound,
    get_current_datetime,
    normalise_phonenumber,
)

logger = logging.getLogger(__name__)


class Application(BaseApplication):
    START_STATE = "state_aaq_start"
    TIMEOUT_RESPONSE_STATE = "state_handle_timeout_response"

    async def state_aaq_start(self):
        question = self._(
            "\n".join(
                [
                    "🙋🏿‍♂️ *QUESTIONS?*",
                    "Ask A Question",
                    "-----",
                    "",
                    "🙍🏾‍♀️*That's what I'm here for!*",
                    "*Just type your Q and hit send* .🙂.",
                    "",
                    "e.g. _How do I know if I have an STI?_",
                    "",
                    "-----",
                    "*Or reply:*",
                    "*0* - 🏠 Back to Main *MENU*",
                ]
            )
        )
        return FreeText(
            self,
            question=question,
            next="state_set_aaq_timeout_1",  # TODO send question to api
            # TODO add validator
        )

    async def state_set_aaq_timeout_1(self):
        msisdn = normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.lstrip(" + ")

        timeout_time = get_current_datetime() + timedelta(minutes=5)
        data = {
            "next_aaq_timeout_time": timeout_time.isoformat(),
            "aaq_timeout_type": "1",
        }

        error = await rapidpro.update_profile(whatsapp_id, data)
        if error:
            return await self.go_to_state("state_error")

        return await self.go_to_state("state_display_results")

    async def state_display_results(self):
        question = self._(
            "\n".join(
                [
                    "🙋🏿‍♂️ QUESTIONS?",
                    "*Ask A Question*",
                    "-----",
                    "",
                    "🙍🏾‍♀️Here are some FAQs that might answer your question." "",
                    "*To see the answer, reply with the number of the FAQ "
                    "you're interested in:*",
                    "",
                    "*1* - {{AAQ Title #1}}",
                    "*2* - {{AAQ Title #2}}",
                    "*3* - {{AAQ Title #3}}",
                    "*4* - None of these answer my question",
                    "",
                    "-----",
                    "*Or reply:*",
                    "*0* - 🏠 Back to Main *MENU*",
                    "# - 🆘 Get HELP",
                ]
            )
        )
        return WhatsAppListState(
            self,
            question=question,
            button="Choose an option",
            choices=[
                Choice("title_1", self._("AAQ Title #1")),
                Choice("title_2", self._("AAQ Title #2")),
                Choice("title_3", self._("AAQ Title #3")),
                Choice("no match", self._("None of these help")),
            ],
            next="state_set_aaq_timeout_2",
            error=self._(GENERIC_ERROR),
        )

    async def state_set_aaq_timeout_2(self):
        chosen_answer = self.user.answers.get("state_display_results")

        if chosen_answer == "no match":
            return await self.go_to_state("state_is_question_answered")

        msisdn = normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.lstrip(" + ")

        timeout_time = get_current_datetime() + timedelta(minutes=5)
        data = {
            "next_aaq_timeout_time": timeout_time.isoformat(),
            "aaq_timeout_type": "2",
        }

        error = await rapidpro.update_profile(whatsapp_id, data)
        if error:
            return await self.go_to_state("state_error")

        return await self.go_to_state("state_display_content")

    async def state_display_content(self):
        msg = self._(
            "\n".join(
                [
                    "TODO: display chosen answer",
                ]
            )
        )
        await self.worker.publish_message(
            self.inbound.reply(
                msg,
            )
        )
        await asyncio.sleep(1.5)
        question = self._(
            "\n".join(
                [
                    "*Did we answer your question?*",
                    "",
                    "*Reply:*",
                    "*1* - Yes 👍",
                    "*2* - No 👎",
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
            error=self._(GENERIC_ERROR),
            next="state_is_question_answered",
        )

    async def state_is_question_answered(self):
        msisdn = normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.lstrip(" + ")

        data = {
            "aaq_timeout_type": "",
        }

        error = await rapidpro.update_profile(whatsapp_id, data)
        if error:
            return await self.go_to_state("state_error")

        if self.user.answers.get("state_display_content", None) == "yes":
            return await self.go_to_state("state_yes_question_answered")
        return await self.go_to_state("state_no_question_not_answered")

    async def state_yes_question_answered(self):
        return EndState(
            self,
            self._(
                "🙍🏾‍♀️*So glad I could help! If you have another question, "
                "you know what to do!* 😉"
            ),
            next=self.START_STATE,
        )

    async def state_no_question_not_answered(self):
        return EndState(
            self,
            self._("TODO: Handle question not answered"),
            next=self.START_STATE,
        )

    async def state_handle_timeout_response(self):
        msisdn = normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.lstrip(" + ")

        error, fields = await rapidpro.get_profile(whatsapp_id)
        if error:
            return await self.go_to_state("state_error")

        data = {
            "aaq_timeout_sent": "",
            "aaq_timeout_type": "",
        }
        error = await rapidpro.update_profile(whatsapp_id, data)
        if error:
            return await self.go_to_state("state_error")

        timeout_type_sent = fields.get("aaq_timeout_type")
        inbound = clean_inbound(self.inbound.content)

        if timeout_type_sent == "1":
            if inbound == "yes ask again":
                return await self.go_to_state("state_aaq_start")
            return EndState(
                self,
                self._("Ok"),
                next=self.START_STATE,
            )
        if timeout_type_sent == "2":
            if inbound == "yes":
                return await self.go_to_state("state_yes_question_answered")
            return await self.go_to_state("state_no_question_not_answered")
