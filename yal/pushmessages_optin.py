import asyncio
import logging

from vaccine.base_application import BaseApplication
from vaccine.states import Choice, WhatsAppButtonState
from vaccine.utils import get_display_choices
from yal import contentrepo, rapidpro, utils
from yal.askaquestion import Application as AaqApplication
from yal.mainmenu import Application as MainMenuApplication
from yal.surveys.baseline import Application as BaselineSurveyApplication
from yal.utils import get_generic_error, normalise_phonenumber

logger = logging.getLogger(__name__)


class Application(BaseApplication):
    START_STATE = "state_start_pushmessage_optin"

    async def state_start_pushmessage_optin(self):
        choices = [
            Choice("yes", "Yes, please!"),
            Choice("no", "No thanks"),
        ]
        question = self._(
            "\n".join(
                [
                    "If you'd like, I can send you notifications once a day with "
                    "relevant info that I've put together just for you.",
                    "",
                    "*Would you like to get notifications?*",
                    "",
                    get_display_choices(choices),
                    "",
                    "_💡You can turn the notifications off at any time, just reply "
                    '"STOP" or go to your profile._',
                ]
            )
        )
        return WhatsAppButtonState(
            self,
            question=question,
            choices=choices,
            error=self._(get_generic_error()),
            next={
                "yes": "state_pushmessage_optin_yes_submit",
                "no": "state_pushmessage_optin_no_submit",
            },
        )

    async def state_pushmessage_optin_no_submit(self):
        msisdn = normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.lstrip(" + ")
        data = {
            "push_message_opt_in": "False",
        }
        error = await rapidpro.update_profile(whatsapp_id, data, self.user.metadata)
        if error:
            return await self.go_to_state("state_error")
        return await self.go_to_state("state_pushmessage_optin_no")

    async def state_pushmessage_optin_no(self):
        msg = self._(
            "\n".join(
                [
                    "[persona_emoji] Not a problem!",
                    "",
                    "If you change your mind and want to turn on notifications, "
                    "just choose the ⚙️*Chat Settings* option from the *main menu*. 😉",
                ]
            )
        )
        await self.publish_message(msg)
        return await self.go_to_state("state_pushmessage_optin_final")

    async def state_pushmessage_optin_yes_submit(self):
        msisdn = normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.lstrip(" + ")
        data = {
            "push_message_opt_in": "True",
        }
        error = await rapidpro.update_profile(whatsapp_id, data, self.user.metadata)
        if error:
            return await self.go_to_state("state_error")

        is_baseline_survey_active = await utils.check_if_baseline_active()
        is_in_south_africa = self.user.metadata.get("country") == "south africa"
        is_in_age_range = None
        if self.user.metadata.get("age"):
            is_in_age_range = 18 <= int(self.user.metadata.get("age")) <= 24
        not_used_bot_before = self.user.metadata.get("used_bot_before") == "no"

        if (
            is_baseline_survey_active
            and is_in_south_africa
            and is_in_age_range
            and not_used_bot_before
        ):
            self.save_answer("state_is_eligible_for_study", "true")
            return await self.go_to_state("state_study_invitation")

        self.save_answer("state_is_eligible_for_study", "false")
        return await self.go_to_state("state_pushmessage_optin_yes")

    async def state_pushmessage_optin_yes(self):
        msg = self._(
            "\n".join(
                [
                    "[persona_emoji] *Lekker! I've set up notifications.*",
                    "",
                    "🔔 I'll ping you once a day with info I think might ",
                    "be interesting or helpful for you — and sometimes just to "
                    "share something a bit more fun.",
                ]
            )
        )
        await self.publish_message(msg)
        await asyncio.sleep(1)
        return await self.go_to_state("state_pushmessage_optin_final")

    async def state_pushmessage_optin_final(self):
        choices = [
            Choice("menu", "Go to the menu"),
            Choice("aaq", "Ask a question"),
        ]
        question = self._(
            "\n".join(
                [
                    "*What would you like to do now?*",
                    get_display_choices(choices, bold_numbers=True),
                ]
            )
        )
        return WhatsAppButtonState(
            self,
            question=question,
            choices=choices,
            error=self._(get_generic_error()),
            next={
                "menu": MainMenuApplication.START_STATE,
                "aaq": AaqApplication.START_STATE,
            },
        )

    async def state_study_invitation(self):
        choices = [
            Choice("yes", "Yes I want to answer"),
            Choice("no", "I'm not interested"),
        ]
        question = self._(
            "\n".join(
                [
                    "Congrats! You qualify to earn *R30 airtime* 🤑 All you need to "
                    "do is answer some questions.",
                    "",
                    "The answers will help us learn more about you. Then we can make "
                    "sure you get information that is most relevant to you. And it "
                    "will also help us improve!",
                    "",
                    "This will take about 10-15 minutes.",
                    "",
                    "*Ready to answer and earn R30?* 🚀",
                ]
            )
        )
        return WhatsAppButtonState(
            self,
            question=question,
            choices=choices,
            error=self._(get_generic_error()),
            next={
                "yes": "state_study_consent_pdf",
                "no": "state_pushmessage_optin_final",
            },
        )

    async def state_study_consent_pdf(self):
        await self.worker.publish_message(
            self.inbound.reply(
                None,
                helper_metadata={"document": contentrepo.get_study_consent_form_url()},
            )
        )
        await asyncio.sleep(1.5)
        return await self.go_to_state("state_study_consent")

    async def state_study_consent(self):
        choices = [
            Choice("yes", "Yes, I agree"),
            Choice("no", "No, I don't agree"),
        ]
        question = self._(
            "\n".join(
                [
                    "*Fantastic! 👏🏾 🎉 And thank you 🙏🏽*",
                    "",
                    "Before we start, here are a few important notes.",
                    "",
                    "📈 We're doing this study to improve the chatbot to better help "
                    "*you* and others like you.",
                    "",
                    "✅ This study is voluntary and you can leave at any time by "
                    "responding with the keyword _*“menu”* however, if you exit before "
                    "completing the survey, you will *not* be able to receive the R30 "
                    "airtime voucher._",
                    "",
                    "❓ You can skip any questions you don't want to answer. "
                    "To try improve South Africa’s sexual health we need to ask "
                    "a number of questions that may be sensitive; for instance, "
                    "we ask about sexual behaviours,sexual orientation and health "
                    "status, among other topics. "
                    "",
                    "",
                    "🔒 You've seen and agreed to our privacy policy. Just a reminder "
                    "that we promise to keep all your info private and secure.",
                    "",
                    "👤 Your answers are anonymous and confidential. We won't share "
                    "data outside the BWise WhatsApp Chatbot team.",
                    "",
                    "📄  We have sent you a copy of this consent document. "
                    "Please see above. ",
                    "",
                    "*Are you happy with this?*",
                ]
            )
        )
        return WhatsAppButtonState(
            self,
            question=question,
            choices=choices,
            error=self._(get_generic_error()),
            next={
                "yes": "state_study_consent_yes_submit",
                "no": "state_pushmessage_optin_final",
            },
        )

    async def state_study_consent_yes_submit(self):
        msisdn = normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.lstrip(" + ")
        data = {
            "ejaf_study_optin": "True",
        }
        error = await rapidpro.update_profile(whatsapp_id, data, self.user.metadata)
        if error:
            return await self.go_to_state("state_error")
        return await self.go_to_state(BaselineSurveyApplication.START_STATE)
