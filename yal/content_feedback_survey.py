from vaccine.base_application import BaseApplication
from vaccine.states import Choice, EndState, FreeText, WhatsAppButtonState
from vaccine.utils import get_display_choices
from yal import rapidpro, utils
from yal.askaquestion import Application as AAQApplication


class ContentFeedbackSurveyApplication(BaseApplication):
    START_STATE = "state_content_feedback_survey_start"

    async def state_content_feedback_survey_start(self):
        msisdn = utils.normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.lstrip("+")
        # Reset this, so that we only get the survey once after a push
        await rapidpro.update_profile(whatsapp_id, {"feedback_survey_sent": ""})

        keyword = utils.clean_inbound(self.inbound.content)
        if keyword in {"1", "yes", "yes thanks"}:
            return await self.go_to_state("state_positive_feedback")
        else:
            return await self.go_to_state("state_negative_feedback")

    async def state_positive_feedback(self):
        choices = [
            Choice("no", self._("No changes")),
            Choice("yes", self._("Yes, I have a change!")),
        ]
        question = self._(
            "\n".join(
                [
                    "*That's great - I'm so happy I could help.* 😊",
                    "",
                    "If there is anything or any info that you think needs to be "
                    "changed or added, please let me know.",
                    "",
                    "Reply:",
                    get_display_choices(choices),
                    "",
                    "--",
                    utils.BACK_TO_MAIN,
                    utils.GET_HELP,
                ]
            )
        )
        return WhatsAppButtonState(
            self,
            question=question,
            choices=choices,
            error=self._(utils.get_generic_error()),
            next={"no": "state_no_feedback", "yes": "state_get_feedback"},
        )

    async def state_no_feedback(self):
        question = self._(
            "\n".join(
                [
                    "Thanks for letting us know!",
                    "",
                    "Check you later 👋🏾",
                    "",
                    "-----",
                    "*Or reply:*",
                    utils.BACK_TO_MAIN,
                    utils.GET_HELP,
                ]
            )
        )
        return EndState(self, question)

    async def state_get_feedback(self):
        question = self._(
            "\n".join(
                [
                    "Please tell me what was missing or what you'd like to change.",
                    "",
                    "_Just type and send your feedback now._",
                    "",
                    "-----",
                    "*Or reply:*",
                    utils.BACK_TO_MAIN,
                    utils.GET_HELP,
                ]
            )
        )
        return FreeText(self, question, next="state_confirm_feedback")

    async def state_confirm_feedback(self):
        question = self._(
            "\n".join(
                [
                    "Ok got it 👍🏾",
                    "",
                    "Thank you for the feedback - I'm working on it already.",
                    "",
                    "Chat again soon 👋🏾",
                    "",
                    "-----",
                    "*Or reply:*",
                    utils.BACK_TO_MAIN,
                    utils.GET_HELP,
                ]
            )
        )
        return EndState(self, question)

    async def state_negative_feedback(self):
        choices = [
            Choice("yes", self._("Yes, please")),
            Choice("no", self._("Maybe later")),
        ]
        question = self._(
            "\n".join(
                [
                    "I'm sorry I couldn't find what you were looking for this time... "
                    "maybe I can help you find it if you *ask me a question?*",
                    "",
                    "*Would you like to ask me a question now?*",
                    "",
                    get_display_choices(choices, bold_numbers=True),
                    "",
                    "-----",
                    "*Or reply:*",
                    utils.BACK_TO_MAIN,
                    utils.GET_HELP,
                ]
            )
        )
        return WhatsAppButtonState(
            self,
            question=question,
            choices=choices,
            next={
                "yes": AAQApplication.START_STATE,
                "no": "state_no_negative_feedback",
            },
            error=self._(utils.get_generic_error()),
        )

    async def state_no_negative_feedback(self):
        question = self._(
            "\n".join(
                [
                    "Cool. 👍🏾",
                    "",
                    'If you change your mind, just go back to "ask a question" on the '
                    "main menu.",
                    "",
                    "-----",
                    "*Reply:*",
                    utils.BACK_TO_MAIN,
                    utils.GET_HELP,
                ]
            )
        )
        return EndState(self, question)
