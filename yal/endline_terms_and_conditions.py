from vaccine.base_application import BaseApplication
from vaccine.states import Choice, ChoiceState, WhatsAppButtonState
from yal.utils import get_generic_error

class Application(BaseApplication):
    START_STATE = "state_start"

    async def state_start(self):
        question = self._(
            "\n".join(
                [
                    "Hi there from [insert custom name] [insert custom emoji] and your BWise friends.",
                    "",
                    "About 3 months ago you joined BWise. Answer a few questions about BWise and get *R50 airtime*🤑.",
                    "",
                    "This should only take 10-15 mins.",
                    "",
                    "Reply wth *ANSWER* to start."
                ]
            )
        )
        error = self._(get_generic_error())

        return WhatsAppButtonState(
            self,
            question=question,
            choices=[
                Choice("accept", "Yes, I want to answer"),
                Choice("reminder", "Remind me tomorrow"),
                Choice("decline", "I’m not interested"),
            ],
            error=error,
            next={
                "accept": "state_accept_consent",
                "decline": "state_accept_consent",
                "reminder": "state_accept_consent"
            },
        )
    

    async def state_consent(self):
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
                Choice("yes", "yes, I agree"),
                Choice("no", "No, I don't agree"),
                Choice("question", "I have some questions")
            ],
            error=error,
            next={
                "yes": "state_accept_consent",
                "no": "state_accept_consent",
                "question": "state_accept_consent"
            }
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
                Choice("yes", "yes, I agree"),
                Choice("no", "No, I don't agree"),
            ],
            error=error,
            next={
                "ok": "state_relationship_status",
                "no": "state_accept_consent",
            }
        )
    

    async def state_relationship_status(self):
        choices=[
                Choice("yes", "Yes"),
                Choice("no", "No"),
                Choice("complicated", "It is complicated"),
                Choice("rather", "Rather not say"),
                Choice("skip", "Skip question")
        ]
        question = self._(
            "\n".join(
                [
                    "*Are you seeing someone special right now?*",
                ]
            )
        )
        error = self._(get_generic_error())

        return ChoiceState(
            self,
            question=question,
            error=error,
            choices=choices,
            next="state_monthly_household_income",
        )

    async def state_monthly_household_income(self):
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
            # where to go from here
        )