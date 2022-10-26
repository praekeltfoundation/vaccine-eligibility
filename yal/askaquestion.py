import asyncio
import logging
from datetime import timedelta

import aiohttp

from vaccine.base_application import BaseApplication
from vaccine.models import Message
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
from yal.servicefinder import Application as ServiceFinderApplication
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
    AAQ_FEEDBACK_TRIGGER_KEYWORDS = {
        "1",
        "yes ask again",
        "yes",
        "2",
        "no i m good",
        "nope",
        "3",
        "no go back to list",
    }

    async def state_aaq_start(self, question=None, buttons=None):

        if not config.AAQ_URL:
            return await self.go_to_state("state_coming_soon")

        self.save_metadata("aaq_page", 0)

        if not question:
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
                        GET_HELP,
                    ]
                )
            )
        return FreeText(
            self,
            question=question,
            next="state_set_aaq_timeout_1",
            check=nonempty_validator(question),
            buttons=buttons,
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
        self.save_metadata("feedback_timestamp", timeout_time.isoformat())
        data = {
            "feedback_timestamp": timeout_time.isoformat(),
            "feedback_type": "ask_a_question",
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
            question_list = [
                f"🙋🏿‍♂️ QUESTIONS? / Ask A Question / *1st {len(answers)} matches*",
                "-----",
                "",
                "[persona_emoji] That's a really good question! I have a few "
                "answers that could give you the info you need.",
                "",
                "*What would you like to read first?* Reply with the number "
                "of the topic you're interested in.",
                "",
                get_display_choices(choices, bold_numbers=True),
                "",
            ]
            # Add next page option if there is one
            if self.user.metadata.get("next_page_url"):
                question_list.extend(
                    ["or", f"*{len(choices)+1}*. See more options", ""]
                )
                choices.append(Choice("more", "See more options"))
            # Add footer options
            question_list.extend(["-----", "*Or reply:*", BACK_TO_MAIN, GET_HELP])

            question = self._("\n".join(question_list))
        else:
            question = "\n".join(
                [
                    f"🙋🏿‍♂️ QUESTIONS? / Ask A Question / *2nd {len(answers)} "
                    "matches*",
                    "-----",
                    "",
                    "[persona_emoji] Here are some more topics that might answer "
                    "your question.",
                    "",
                    "*Which of these would you like to explore?* To see the "
                    "answer, reply with the number of the topic you're interested "
                    "in.",
                    "",
                    get_display_choices(choices, bold_numbers=True),
                    "",
                    "or",
                    f"*{len(choices)+1}*. Back to first list",
                    f"*{len(choices)+2}*. Talk to a counsellor",
                    "",
                    "-----",
                    "*Or reply:*",
                    BACK_TO_MAIN,
                    GET_HELP,
                ]
            )
            choices.append(Choice("back", "Back to first list"))
            choices.append(Choice("callme", "Talk to a counsellor"))

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
        self.save_metadata("feedback_timestamp", timeout_time.isoformat())
        data = {
            "feedback_timestamp": timeout_time.isoformat(),
            "feedback_type": "ask_a_question_2",
        }

        error = await rapidpro.update_profile(whatsapp_id, data)
        if error:
            return await self.go_to_state("state_error")

        return await self.go_to_state("state_display_content")

    async def state_display_content(self):
        answers = self.user.metadata["model_answers"]
        chosen_answer = self.user.answers.get("state_display_results")
        self.save_metadata("faq_id", answers[chosen_answer]["id"])
        content = answers[chosen_answer]["body"]
        question = "\n".join(
            [
                f"🙋🏿‍♂️ QUESTIONS? / *{chosen_answer}*",
                "-----",
                "",
                f"[persona_emoji] {content}",
            ]
        )
        await self.publish_message(question)
        await asyncio.sleep(1.5)

        return await self.go_to_state("state_get_content_feedback")

    async def state_get_content_feedback(self):
        choices = [
            Choice("yes", self._("Yes")),
            Choice("back to list", self._("No, go back to list")),
            Choice("no", self._("Nope...")),
        ]
        question = self._(
            "\n".join(
                [
                    "[persona_emoji] *Did I answer your question?*",
                    "",
                    "*Reply:*",
                    get_display_choices(choices, bold_numbers=True),
                ]
            )
        )
        return WhatsAppButtonState(
            self,
            question=question,
            choices=choices,
            error=self._(get_generic_error()),
            next="state_is_question_answered",
        )

    async def state_is_question_answered(self):
        msisdn = normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.lstrip(" + ")

        data = {
            "feedback_type": "",
        }

        error = await rapidpro.update_profile(whatsapp_id, data)
        if error:
            return await self.go_to_state("state_error")

        feedback_answer = self.user.answers.get("state_get_content_feedback", None)

        inbound_id = self.user.metadata["inbound_id"]
        feedback_secret_key = self.user.metadata["feedback_secret_key"]
        faq_id = self.user.metadata["faq_id"]
        feedback_type = "positive" if feedback_answer == "yes" else "negative"
        error = await aaq_core.add_feedback(
            feedback_secret_key, inbound_id, feedback_type, faq_id
        )
        if error:
            return await self.go_to_state("state_error")

        if feedback_answer == "yes":
            return await self.go_to_state("state_yes_question_answered")
        if feedback_answer == "back to list":
            return await self.go_to_state("state_display_results")
        if feedback_answer == "no":
            return await self.go_to_state("state_no_question_not_answered")

        return await self.go_to_state("state_display_results")

    async def state_yes_question_answered(self):
        choices = [
            Choice("no", self._("No changes")),
            Choice("yes", self._("Yes, I have a change")),
        ]
        question = self._(
            "\n".join(
                [
                    "*That's great - I'm so happy I could help.* 😊 ",
                    "",
                    "Is there anything that you would change about my answer?",
                    "",
                    "*Reply:*",
                    get_display_choices(choices),
                    "",
                    "-----",
                    "*Or reply:*",
                    BACK_TO_MAIN,
                    GET_HELP,
                ]
            )
        )

        return WhatsAppButtonState(
            self,
            question=question,
            choices=choices,
            next={
                "no": "state_yes_question_answered_no_changes",
                "yes": "state_yes_question_answered_changes",
            },
            error=self._(get_generic_error()),
        )

    async def state_yes_question_answered_no_changes(self):
        choices = [
            Choice("aaq", self._("Ask another question")),
            Choice("counsellor", self._("Talk to a counsellor")),
        ]
        question = self._(
            "\n".join(
                [
                    "Thank you so much for your feedback.",
                    "",
                    "[persona_emoji] *If you have another question, "
                    "you know what to do!* 😉 ",
                    "",
                    "*What would you like to do now?*",
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
        return WhatsAppButtonState(
            self,
            question=question,
            choices=choices,
            next={
                "aaq": "state_aaq_start",
                "counsellor": PleaseCallMeApplication.START_STATE,
            },
            error=self._(get_generic_error()),
        )

    async def state_yes_question_answered_changes(self):

        question = self._(
            "\n".join(
                [
                    "Please tell me what was missing or "
                    "what you would have changed in my answer.",
                    "",
                    "_Just type and send it now._",
                    "",
                    "-----",
                    "*Or reply:*",
                    BACK_TO_MAIN,
                    GET_HELP,
                ]
            )
        )
        return FreeText(
            self,
            question=question,
            next="state_no_question_not_answered_thank_you",
        )

    async def state_no_question_not_answered(self):
        question = self._(
            "\n".join(
                [
                    "*I'm sorry I couldn't find what you were looking for this time.* ",
                    "",
                    "Please tell me what you're looking for again. "
                    "I'll try make sure I have the right information "
                    "for you next time.",
                    "",
                    "_Just type and send your question again, now._" "",
                    "-----",
                    "*Or reply:*",
                    BACK_TO_MAIN,
                    GET_HELP,
                ]
            )
        )
        return FreeText(
            self,
            question=question,
            next="state_no_question_not_answered_thank_you",
        )

    async def state_no_question_not_answered_thank_you(self):
        choices = [
            Choice("clinic", self._("Find a clinic")),
            Choice("counsellor", self._("Talk to a counsellor")),
        ]
        question = self._(
            "\n".join(
                [
                    "Ok got it. I'll start working on this right away 👍🏾",
                    "",
                    "Thank you for the feedback, you're helping this service improve.",
                    "",
                    "What would you like to do now?",
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
        return WhatsAppButtonState(
            self,
            question=question,
            choices=choices,
            error=self._(get_generic_error()),
            next={
                "clinic": ServiceFinderApplication.START_STATE,
                "counsellor": PleaseCallMeApplication.START_STATE,
            },
        )

    async def state_handle_list_timeout(self):
        choices = [
            Choice("yes", self._("Yes, ask again")),
            Choice("no", self._("No, I'm good")),
        ]
        question = self._(
            "\n".join(
                [
                    "[persona_emoji] *Me again!*",
                    "",
                    "Doesn't look like you found an answer to the question you asked "
                    "me recently...",
                    "",
                    "*Would you like to ask again or try a different Q?*",
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
        return WhatsAppButtonState(
            self,
            question=question,
            choices=choices,
            error=self._(get_generic_error()),
            next={
                "yes": "state_aaq_start",
                "no": "state_pre_mainmenu",
            },
        )

    async def state_handle_timeout_response(self):
        msisdn = normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.lstrip(" + ")

        error, fields = await rapidpro.get_profile(whatsapp_id)
        if error:
            return await self.go_to_state("state_error")
        self.save_metadata("feedback_timestamp", "")
        data = {"feedback_survey_sent": "", "feedback_timestamp": ""}
        error = await rapidpro.update_profile(whatsapp_id, data)
        if error:
            return await self.go_to_state("state_error")

        timeout_type_sent = fields.get("feedback_type")
        self.save_metadata("feedback_type", timeout_type_sent)

        keyword = clean_inbound(self.inbound.content)
        if keyword in self.AAQ_FEEDBACK_TRIGGER_KEYWORDS:
            if timeout_type_sent == "ask_a_question":
                return await self.go_to_state("state_handle_list_timeout")
            if timeout_type_sent == "ask_a_question_2":
                return await self.go_to_state("state_get_content_feedback")
        else:
            # Get it to display the message, instead of having this state try to
            # match it to a keyword
            self.inbound.session_event = Message.SESSION_EVENT.NEW
            return await self.go_to_state("state_aaq_timeout_unrecognised_option")

    async def state_aaq_timeout_unrecognised_option(self):
        choices = [
            Choice("feedback", self._("Reply to last text")),
            Choice("mainmenu", self._("Go to the Main Menu")),
            Choice("aaq", self._("Ask a question")),
        ]
        question = "\n".join(
            [
                "*[persona_emoji] Hmm, looks like you've run out of time to respond to "
                "that message.*",
                "",
                "*What would you like to do now? Here are some options.*",
                "",
                get_display_choices(choices),
            ]
        )
        timeout_type_sent = self.user.metadata.get("feedback_type")
        if timeout_type_sent == "ask_a_question":
            feedback_state = "state_handle_list_timeout"
        if timeout_type_sent == "ask_a_question_2":
            feedback_state = "state_get_content_feedback"
        return WhatsAppButtonState(
            self,
            question=question,
            choices=choices,
            error=get_generic_error(),
            next={
                "feedback": feedback_state,
                # hardcode to prevent circular import
                "mainmenu": "state_pre_mainmenu",
                "aaq": "state_aaq_start",
            },
        )
