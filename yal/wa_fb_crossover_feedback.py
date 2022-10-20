import logging

from vaccine.base_application import BaseApplication
from vaccine.states import Choice, FreeText, WhatsAppButtonState, WhatsAppListState
from vaccine.utils import get_display_choices
from yal import rapidpro, utils
from yal.utils import get_generic_error

logger = logging.getLogger(__name__)


class Application(BaseApplication):
    START_STATE = "state_wa_fb_crossover_feedback"

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
            "engaged_on_facebook": True,
        }
        error = await rapidpro.update_profile(whatsapp_id, data)
        if error:
            return await self.go_to_state("state_error")

        choices = [
            Choice(1, "1 - It was helpful"),
            Choice(2, "2 - Learnt something new"),
            Choice(3, "3 - I enjoy the comments"),
            Choice(4, "4 - Other"),
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
                "other": "",
            },
            error=self._(get_generic_error()),
        )

    async def state_not_saw_recent_facebook(self):
        msisdn = utils.normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.lstrip(" + ")
        data = {
            "engaged_on_facebook": False,
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

        await self.worker.publish_message(self.inbound.reply(msg))
        return await self.go_to_state("state_suggested_content")

    async def state_fb_hot_topic_helpful(self):
        msg = self._(
            "\n".join(
                [
                    "I'm so happy to hear that.",
                    "",
                    "👉🏾 Remember, if you're looking for advice or"
                    "someone to talk to, just request a call back from our"
                    "loveLife counsellors at any time.",
                    "",
                    "--",
                    "",
                    utils.BACK_TO_MAIN,
                    utils.GET_HELP,
                ]
            )
        )
        await self.worker.publish_message(self.inbound.reply(msg))
        return await self.go_to_state("state_suggested_content")

    async def state_fb_hot_topic_enjoyed_comments(self):
        msg = self._(
            "\n".join(
                [
                    "That's also ok. 👌🏾 You choose how much"
                    "you want to get involved - no pressure.",
                    "",
                    "👉🏾 Remember, if you're looking for advice or"
                    "someone to talk to, just request a call back from our"
                    "loveLife counsellors at any time.",
                    "",
                    "--",
                    "",
                    utils.BACK_TO_MAIN,
                    utils.GET_HELP,
                ]
            )
        )
        await self.worker.publish_message(self.inbound.reply(msg))
        return await self.go_to_state("state_suggested_content")

    async def state_fb_hot_topic_other(self):
        msg = self._(
            "\n".join(
                [
                    "I'd love to hear what you think of the topic. "
                    "Please share your thoughts!",
                    "",
                    "_Just type and send your reply_",
                    "",
                    "--",
                    "",
                    utils.BACK_TO_MAIN,
                    utils.GET_HELP,
                ]
            )
        )
        return FreeText(
            app=self,
            question=msg,
            next="state_fb_hot_topic_thanks_for_feedback",
        )

    async def state_fb_hot_topic_thanks_for_feedback(self):
        msg = self._(
            "\n".join(
                [
                    "Thank you so much for sharing your thoughts."
                    "I'll make sure to keep this in mind 🤔",
                    "",
                    "👉🏾 Remember, if you're looking for advice or"
                    "someone to talk to, just request a call back from our"
                    "loveLife counsellors at any time.",
                    "",
                    "--",
                    "",
                    utils.BACK_TO_MAIN,
                    utils.GET_HELP,
                ]
            )
        )
        await self.worker.publish_message(self.inbound.reply(msg))
        return await self.go_to_state("state_suggested_content")

    async def state_suggested_content(self):
        msisdn = utils.normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.lstrip(" + ")
        data = {"last_mainmenu_time": str(utils.get_current_datetime())}

        error = await rapidpro.update_profile(whatsapp_id, data)
        if error:
            return await self.go_to_state("state_error")
        return
