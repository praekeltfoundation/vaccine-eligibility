import asyncio

from vaccine.base_application import BaseApplication
from vaccine.states import (
    Choice,
    ChoiceState,
    FreeText,
    WhatsAppButtonState,
    WhatsAppListState,
)
from yal import rapidpro
from yal.surveys.endline import Application as EndlineApplication
from yal.utils import get_current_datetime, get_generic_error, normalise_phonenumber


class Application(BaseApplication):
    START_STATE = "state_start_terms"

    async def state_start_terms(self):
        question = self._(
            "\n".join(
                [
                    "*Fantastic! 👏🏾 🎉 And thank you 🙏🏽*",
                    "",
                    "Before we start, here are a few important notes.",
                    "",
                    "📈 We’re doing this study to improve the chatbot to better help"
                    " *you* and others like you. It should only take 10-15 mins"
                    " and we'll give you R50 airtime at the end.",
                    "",
                    "✅ This study is voluntary and you can leave at any time by"
                    " responding with the keyword *“menu”* however, if you exit"
                    " before completing the survey, you will *not* be able to"
                    " receive the R30 airtime voucher.",
                    "",
                    "❓ You can skip any questions you don’t want to answer."
                    " To try improve South Africa’s sexual health we need to "
                    "ask a number of questions that may be sensitive; for instance,"
                    " we ask about sexual behaviours, sexual orientation and health"
                    " status, among other topics.",
                    "",
                    "🔒 You’ve seen and agreed to the BWise privacy policy."
                    " Just a reminder that we promise to keep all your info"
                    " private and secure.",
                    "",
                    "👤 Your answers are anonymous and confidential. We won’t share"
                    " data outside the BWise WhatsApp Chatbot team.",
                    "",
                    "📄  We have sent you a document which explains the study in more"
                    " detail. Please see it above to decide if you're happy to join"
                    " the study.*Do you agree to start the survey?*",
                ]
            )
        )
        error = self._(get_generic_error())

        return WhatsAppButtonState(
            self,
            question=question,
            choices=[
                Choice("yes", "Yes, I agree"),
                Choice("no", "No, I don't agree"),
                Choice("question", "I have some questions"),
            ],
            error=error,
            next={
                "yes": "state_accept_consent",
                "no": "state_no_consent",
                "question": "state_have_questions",
            },
        )

    async def state_accept_consent(self):
        question = self._(
            "\n".join(
                [
                    "*Amazing Thank you!*",
                    "Okay, first I've got a few questions to help me figure out how "
                    "you're doing at taking care of your love and health needs.",
                    "",
                    "I'm going to ask a few questions about you and how much you "
                    "agree or disagree with some statements about you, your life, "
                    "and your health?",
                ]
            )
        )
        error = self._(get_generic_error())

        return WhatsAppButtonState(
            self,
            question=question,
            choices=[
                Choice("yes", "ok, let's start"),
                Choice("no", "I can't right now"),
            ],
            error=error,
            next={
                "yes": "state_relationship_status_endline",
                "no": "state_set_reminder_timer",
            },
        )

    async def state_no_consent(self):
        question = self._(
            "\n".join(
                [
                    "That's completely okay, there are no consequences to not taking ,"
                    "part in this study. Please enjoy the BWise tool and stay safe. "
                    "If you change your mind, please send *Answer* to this number",
                ]
            )
        )

        return FreeText(self, question=question, next=None)

    async def state_have_questions(self):
        question = self._(
            "\n".join(
                [
                    "You should be able to find the answer to any questions you "
                    "have in the consent doc we sent you. If you still have "
                    "questions, please email bwise@praekelt.org",
                ]
            )
        )

        return FreeText(
            self,
            question=question,
            next=None,
        )

    async def state_relationship_status_endline(self):
        choices = [
            Choice("yes", "Yes"),
            Choice("no", "No"),
            Choice("complicated", "It is complicated"),
            Choice("rather", "Rather not say"),
            Choice("skip", "Skip question"),
        ]
        question = self._(
            "\n".join(
                [
                    "*Are you seeing someone special right now?*",
                ]
            )
        )
        error = self._(get_generic_error())

        return WhatsAppListState(
            self,
            question=question,
            error=error,
            choices=choices,
            button="Choose Option",
            next="state_monthly_household_income_endline",
        )

    async def state_monthly_household_income_endline(self):
        choices = [
            Choice("no_income", self._("No income")),
            Choice("R1_R400", self._("R1 - R400")),
            Choice("R401_R800", self._("R401 - R800")),
            Choice("R801_R1600", self._("R801 - R1600")),
            Choice("R1601_R3200", self._("R1 601 - R3200")),
            Choice("R3201_R6400", self._("R3 201 - R6400")),
            Choice("R6401_R12800", self._("R6 401 - R12800")),
            Choice("R12801_R25600", self._("R12 801 - R25600")),
            Choice("R25601_R51200", self._("R25 601 - R51200")),
            Choice("R51201_R102 400", self._("R51 201 - R102 400")),
            Choice("R102401_R204 800", self._("R102 401 - R204 800")),
            Choice("R204801_or_more", self._("R204 801 or more")),
            Choice("skip_question", self._("Skip question")),
        ]

        question = self._(
            "\n".join(
                [
                    "*What is the total monthly income of your whole household?*",
                    "",
                    "Please respond with the *number* of an option below",
                ]
            )
        )
        error = self._(
            "\n".join(
                [
                    "*Oops. We did not understand your answer*",
                    "Please respond with the *number* of an option below",
                    "",
                    "What is the total monthly income of your whole household?",
                ]
            )
        )
        return ChoiceState(
            self,
            question=question,
            error=error,
            choices=choices,
            next="state_submit_terms_and_conditions_endline",
        )

    async def state_set_reminder_timer(self):
        msisdn = normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.lstrip(" + ")

        assessment_name = self.user.metadata.get(
            "assessment_name", "locus_of_control_endline"
        )
        data = {
            "assessment_reminder": get_current_datetime().isoformat(),
            "assessment_reminder_name": assessment_name,
            "assessment_reminder_type": "reengagement 30min",
        }

        return await rapidpro.update_profile(whatsapp_id, data, self.user.metadata)

    async def state_submit_terms_and_conditions_endline(self):
        msisdn = normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.lstrip(" + ")

        error = await rapidpro.update_profile(
            whatsapp_id, {"endline_terms_accepted": "True"}, self.user.metadata
        )
        if error:
            return await self.go_to_state("state_error")

        await self.worker.publish_message(
            self.inbound.reply(self._("Excellent - now we can get you set up."))
        )
        await asyncio.sleep(0.5)
        return await self.go_to_state(EndlineApplication.START_STATE)
