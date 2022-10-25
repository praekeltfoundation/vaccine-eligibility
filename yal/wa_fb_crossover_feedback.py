import logging

from vaccine.base_application import BaseApplication
from vaccine.states import (
    Choice,
    EndState,
    FreeText,
    WhatsAppButtonState,
    WhatsAppListState,
)
from vaccine.utils import get_display_choices
from yal import rapidpro, utils
from yal.askaquestion import Application as AskaQuestionApplication
from yal.pleasecallme import Application as PleaseCallMeApplication
from yal.utils import get_generic_error

logger = logging.getLogger(__name__)


class Application(BaseApplication):
    START_STATE = "state_crossover_feedback_survey_start"

    async def state_crossover_feedback_survey_start(self):
        msisdn = utils.normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.lstrip("+")
        # Reset this, so that we only get the survey once after a push
        await rapidpro.update_profile(whatsapp_id, {"feedback_survey_sent": ""})
        return await self.go_to_state("state_wa_fb_crossover_feedback")

    async def state_wa_fb_crossover_feedback(self):
        choices = [
            Choice("yes", self._("Yes, I did")),
            Choice("no", self._("No, I didn't")),
        ]
        question = self._(
            "\n".join(
                [
                    "[persona_emoji] Did you see the last "
                    "HOT TOPIC on our Facebook channel?🔥",
                    "",
                    get_display_choices(choices),
                    "",
                    "-----",
                    utils.BACK_TO_MAIN,
                    utils.GET_HELP,
                ]
            )
        )
        return WhatsAppButtonState(
            self,
            question=question,
            choices=choices,
            error=self._(get_generic_error()),
            next={
                "yes": "state_saw_recent_facebook",
                "no": "state_not_saw_recent_facebook",
            },
        )

    async def state_saw_recent_facebook(self):
        msisdn = utils.normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.lstrip(" + ")
        data = {
            "engaged_on_facebook": "TRUE",
            "last_mainmenu_time": utils.get_current_datetime().isoformat(),
        }
        error = await rapidpro.update_profile(whatsapp_id, data)
        if error:
            return await self.go_to_state("state_error")

        choices = [
            Choice("helpful", self._("It was helpful")),
            Choice("learnt new", self._("Learnt something new")),
            Choice("enjoyed comments", self._("I enjoy the comments")),
            Choice("other", self._("Other")),
        ]

        question = self._(
            "\n".join(
                [
                    "I thought it was so interesting 💡",
                    "",
                    "What did you think?",
                    "",
                    "_Click on the button below and choose an option_",
                    "",
                    get_display_choices(choices),
                    "",
                    "--",
                    "",
                    utils.BACK_TO_MAIN,
                    utils.GET_HELP,
                ]
            )
        )
        return WhatsAppListState(
            self,
            question=question,
            button="Feedback",
            choices=choices,
            next={
                "helpful": "state_fb_hot_topic_helpful",
                "learnt new": "state_fb_hot_topic_helpful",
                "enjoyed comments": "state_fb_hot_topic_enjoyed_comments",
                "other": "state_fb_hot_topic_other",
            },
            error=self._(get_generic_error()),
        )

    async def state_not_saw_recent_facebook(self):
        msisdn = utils.normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.lstrip(" + ")
        data = {
            "engaged_on_facebook": "FALSE",
        }
        error = await rapidpro.update_profile(whatsapp_id, data)
        if error:
            return await self.go_to_state("state_error")

        msg = self._(
            "\n".join(
                [
                    "*You should check it out! 👀There's always* "
                    "*an interesting conversation to get involved in.*",
                    "",
                    "You can check out the latest Hot Topic on Facebook, now! "
                    "Just click the link below, and *get involved.*",
                    "",
                    "FB Link: https://www.facebook.com/BWiseHealth/",
                    "--",
                    "",
                    utils.BACK_TO_MAIN,
                    utils.GET_HELP,
                ]
            )
        )

        return EndState(
            self,
            text=msg,
        )

    async def state_fb_hot_topic_helpful(self):
        choices = [
            Choice("counsellor", self._("Talk to a counsellor")),
            Choice("question", self._("Ask a question")),
        ]

        question = self._(
            "\n".join(
                [
                    "I'm so happy to hear that.",
                    "",
                    "👉🏾 Remember, if you're looking for advice or "
                    "someone to talk to, just request a call back from our "
                    "*loveLife counsellors* at any time.",
                    "",
                    "*What would you like to do now?*",
                    get_display_choices(choices),
                    "",
                    "--",
                    "*Or reply*",
                    utils.BACK_TO_MAIN,
                    utils.GET_HELP,
                ]
            )
        )
        return WhatsAppButtonState(
            self,
            question=question,
            choices=choices,
            error=self._(get_generic_error()),
            next={
                "counsellor": PleaseCallMeApplication.START_STATE,
                "question": AskaQuestionApplication.START_STATE,
            },
        )

    async def state_fb_hot_topic_enjoyed_comments(self):
        choices = [
            Choice("counsellor", self._("Talk to a counsellor")),
            Choice("question", self._("Ask a question")),
        ]

        question = self._(
            "\n".join(
                [
                    "That's also ok. 👌🏾 You choose how much "
                    "you want to get involved - no pressure.",
                    "",
                    "👉🏾 Remember, if you're looking for advice or "
                    "someone to talk to, just request a call back from our "
                    "*loveLife counsellors* at any time.",
                    "",
                    "*What would you like to do now?*",
                    get_display_choices(choices),
                    "",
                    "--",
                    "*Or reply*",
                    utils.BACK_TO_MAIN,
                    utils.GET_HELP,
                ]
            )
        )
        return WhatsAppButtonState(
            self,
            question=question,
            choices=choices,
            error=self._(get_generic_error()),
            next={
                "counsellor": PleaseCallMeApplication.START_STATE,
                "question": AskaQuestionApplication.START_STATE,
            },
        )

    async def state_fb_hot_topic_other(self):
        question = self._(
            "\n".join(
                [
                    "I'd love to hear what you think of the topic. "
                    "Please share your thoughts!",
                    "",
                    "_Just type and send your reply_",
                    "",
                    "--",
                    "*Or reply*",
                    utils.BACK_TO_MAIN,
                    utils.GET_HELP,
                ]
            )
        )
        return FreeText(
            app=self,
            question=question,
            next="state_fb_hot_topic_thanks_for_feedback",
        )

    async def state_fb_hot_topic_thanks_for_feedback(self):
        choices = [
            Choice("counsellor", self._("Talk to a counsellor")),
            Choice("question", self._("Ask a question")),
        ]

        question = self._(
            "\n".join(
                [
                    "Thank you so much for sharing your thoughts. "
                    "I'll make sure to keep this in mind 🤔",
                    "",
                    "👉🏾 Remember, if you're looking for advice or "
                    "someone to talk to, just request a call back from our "
                    "*loveLife counsellors* at any time.",
                    "",
                    "*What would you like to do now?*",
                    get_display_choices(choices),
                    "",
                    "--",
                    "*Or reply*",
                    utils.BACK_TO_MAIN,
                    utils.GET_HELP,
                ]
            )
        )
        return WhatsAppButtonState(
            self,
            question=question,
            choices=choices,
            error=self._(get_generic_error()),
            next={
                "counsellor": PleaseCallMeApplication.START_STATE,
                "question": AskaQuestionApplication.START_STATE,
            },
        )
