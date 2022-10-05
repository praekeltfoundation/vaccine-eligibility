import asyncio
import logging
from datetime import timedelta

import aiohttp

from vaccine.base_application import BaseApplication
from vaccine.states import (
    Choice,
    EndState,
    FreeText,
    WhatsAppButtonState,
    WhatsAppListState,
)
from vaccine.utils import get_display_choices
from vaccine.validators import nonempty_validator
from yal import aaq_core, config, rapidpro
from yal.pleasecallme import Application as PleaseCallMeApplication
from yal.utils import (
    BACK_TO_MAIN,
    GET_HELP,
    clean_inbound,
    get_current_datetime,
    get_generic_error,
    normalise_phonenumber,
)

logger = logging.getLogger(__name__)


def get_aaq_api():
    return aiohttp.ClientSession(
        timeout=aiohttp.ClientTimeout(total=5),
        headers={
            "Authorization": f"BEARER {config.AAQ_TOKEN}",
            "Content-Type": "application/json",
        },
    )


class Application(BaseApplication):
    START_STATE = "state_aaq_start"
    TIMEOUT_RESPONSE_STATE = "state_handle_timeout_response"

    async def state_aaq_start(self):

        if not config.AAQ_URL:
            return await self.go_to_state("state_coming_soon")

        self.save_metadata("aaq_page", 0)

        question = self._(
            "\n".join(
                [
                    "🙋🏿‍♂️ QUESTIONS? / *Ask A Question*",
                    "-----",
                    "",
                    "[persona_emoji] *That's what I'm here for!*",
                    "*Just type your Q and hit send* 🙂",
                    "",
                    "e.g. _How do I know if I have an STI?_",
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
            next="state_set_aaq_timeout_1",
            check=nonempty_validator(question),
        )

    async def state_coming_soon(self):
        return EndState(
            self,
            self._("Coming soon..."),
            next=self.START_STATE,
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

        return await self.go_to_state("state_aaq_model_request")

    async def state_aaq_model_request(self):
        error, response_data = await aaq_core.inbound_check(
            self.user, self.inbound.message_id, self.user.answers["state_aaq_start"]
        )
        if error:
            return await self.go_to_state("state_error")

        for key, value in response_data.items():
            self.save_metadata(key, value)
        return await self.go_to_state("state_display_results")

    async def state_aaq_get_page(self):
        error, response_data = await aaq_core.get_page(self.user.metadata["page_url"])
        if error:
            return await self.go_to_state("state_error")

        for key, value in response_data.items():
            self.save_metadata(key, value)
        return await self.go_to_state("state_display_results")

    async def state_display_results(self):
        answers = self.user.metadata["model_answers"]
        page = self.user.metadata["aaq_page"]

        choices = []
        for title in answers.keys():
            choices.append(Choice(title, title))

        if page == 0:
            if self.user.metadata.get("next_page_url"):
                choices.append(Choice("more", "Show me more"))
            question = self._(
                "\n".join(
                    [
                        f"🙋🏿‍♂️ QUESTIONS? / Ask A Question / 1st {len(answers)} "
                        "matches",
                        "-----",
                        "",
                        "[persona_emoji] That's a really good question! I have a few "
                        "answers that could give you the info you need.",
                        "",
                        "*What would you like to read first?* Reply with the number "
                        "of the topic you're interested in.",
                        "",
                        get_display_choices(choices),
                        "",
                        "-----",
                        "*Or reply:*",
                        BACK_TO_MAIN,
                        GET_HELP,
                    ]
                )
            )
        else:
            choices.append(Choice("back", "Back to first list"))
            choices.append(Choice("callme", "Talk to a counsellor"))
            question = "\n".join(
                [
                    f"🙋🏿‍♂️ QUESTIONS? / Ask A Question / 2nd {len(answers)} "
                    "matches",
                    "-----",
                    "",
                    "[persona_emoji] Here are some more topics that might answer "
                    "your question.",
                    "",
                    "*Which of these would you like to explore?* To see the "
                    "answer, reply with the number of the topic you're interested "
                    "in.",
                    "",
                    get_display_choices(choices),
                    "",
                    "-----",
                    "*Or reply:*",
                    BACK_TO_MAIN,
                    GET_HELP,
                ]
            )

        return WhatsAppListState(
            self,
            question=question,
            button="Choose an option",
            choices=choices,
            next="state_set_aaq_timeout_2",
            error=self._(get_generic_error()),
        )

    async def state_set_aaq_timeout_2(self):
        chosen_answer = self.user.answers.get("state_display_results")

        inbound_id = self.user.metadata["inbound_id"]
        feedback_secret_key = self.user.metadata["feedback_secret_key"]

        if chosen_answer == "more":
            error = await aaq_core.add_feedback(
                feedback_secret_key, inbound_id, "negative", page="1"
            )
            if error:
                return await self.go_to_state("state_error")

            self.user.metadata["aaq_page"] = 1
            self.save_metadata("page_url", self.user.metadata["next_page_url"])
            return await self.go_to_state("state_aaq_get_page")

        if chosen_answer == "back":
            self.user.metadata["aaq_page"] = 0
            self.save_metadata("page_url", self.user.metadata["prev_page_url"])
            return await self.go_to_state("state_aaq_get_page")

        if chosen_answer == "callme":
            error = await aaq_core.add_feedback(
                feedback_secret_key, inbound_id, "negative", page="2"
            )
            if error:
                return await self.go_to_state("state_error")

            return await self.go_to_state(PleaseCallMeApplication.START_STATE)

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
        answers = self.user.metadata["model_answers"]
        chosen_answer = self.user.answers.get("state_display_results")

        question = "\n".join(
            [
                f"🙋🏿‍♂️ QUESTIONS? / *{chosen_answer}*",
                "-----",
                "",
                f"[persona_emoji] {answers[chosen_answer]}",
            ]
        )
        await self.worker.publish_message(self.inbound.reply(question))
        await asyncio.sleep(1.5)

        return await self.go_to_state("state_get_content_feedback")

    async def state_get_content_feedback(self):
        question = self._(
            "\n".join(
                [
                    "*Did I answer your question?*",
                    "",
                    "*Reply:*",
                    "*1* - Yes",
                    "*2* - No, go back to list",
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

        feedback_answer = self.user.answers.get("state_get_content_feedback", None)

        inbound_id = self.user.metadata["inbound_id"]
        feedback_secret_key = self.user.metadata["feedback_secret_key"]
        feedback_type = "positive" if feedback_answer == "yes" else "negative"
        # TODO: faq_id will come from the API like inbound_id and feedback_secret_key
        faq_id = "-1"
        error = await aaq_core.add_feedback(
            feedback_secret_key, inbound_id, feedback_type, faq_id
        )
        if error:
            return await self.go_to_state("state_error")

        if feedback_answer == "yes":
            return await self.go_to_state("state_yes_question_answered")

        return await self.go_to_state("state_display_results")

    async def state_yes_question_answered(self):
        return EndState(
            self,
            self._(
                "[persona_emoji] *So glad I could help! If you have another question, "
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
