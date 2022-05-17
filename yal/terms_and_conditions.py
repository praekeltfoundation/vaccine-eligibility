from vaccine.states import Choice, EndState, WhatsAppButtonState, WhatsAppListState
from yal.onboarding import Application as OnboardingApplication
from yal.yal_base_application import BaseApplication


class Application(BaseApplication):
    START_STATE = "state_welcome"

    async def state_welcome(self):
        await self.worker.publish_message(
            self.inbound.reply(
                self._(
                    "🙋🏾‍♀️  *HOWZIT! Welcome to B-Wise by Young Africa Live!*\n"
                    "-----\n"
                    "\n"
                    "*Sister Unathi, at your service!*\n"
                    "\n"
                    "I'm a chatbot working on behalf of B-Wise bot, here to answer "
                    "your questions about bodies, sex, relationships and health 😌."
                )
            )
        )
        return await self.go_to_state("state_emergency_prompt")

    async def state_emergency_prompt(self):
        question = self._(
            "🆘 *Got an emergency?*\n"
            "-----\n"
            "\n"
            "Before we continue, I just wanna check whether you're in an emergency "
            "situation and need to speak to a human.\n"
            "\n"
            "*REPLY:*\n"
            "1 - Talk to a human 🧑🏾‍🚀\n"
            "2 - No, I'm good 👍\n"
        )
        error = self._("TODO")

        return WhatsAppButtonState(
            self,
            question=question,
            choices=[
                Choice("yes", "Talk to a human 🧑🏾‍🚀"),
                Choice("no", "No, I'm good 👍"),
            ],
            error=error,
            next={
                "yes": "state_emergency",
                "no": "state_emergency_info",
            },
        )

    async def state_emergency(self):
        return EndState(
            self,
            self._("TODO: Emergency"),
            next=self.START_STATE,
        )

    async def state_emergency_info(self):
        await self.worker.publish_message(
            self.inbound.reply(
                self._(
                    "Cool 😎\n"
                    "\n"
                    "If you ever do need urgent, human help — just say the magic "
                    "word (*HELP*) and I'll link you to a real person."
                )
            )
        )
        return await self.go_to_state("state_get_to_know")

    async def state_get_to_know(self):
        question = self._(
            "*Let's get to know each other better*\n"
            "-----\n"
            "\n"
            "Before we get started, do you mind if I ask you a few Qs? It will help "
            "me do a better job at answering yours.\n"
            "\n"
            "*Reply:*\n"
            "1 - OK 👍\n"
            "2 - Why? 🤔"
        )
        error = self._("TODO")

        return WhatsAppButtonState(
            self,
            question=question,
            choices=[Choice("ok", "OK 👍"), Choice("why", "Why? 🤔")],
            error=error,
            next={
                "ok": "state_pre_terms",
                "why": "state_get_to_know_why",
            },
        )

    async def state_get_to_know_why(self):
        question = self._(
            "ℹ️ *QUESTIONS ABOUT YOU*\n"
            "Why do we ask these questions?\n"
            "-----\n"
            "\n"
            "This info helps the B-Wise team make me a better bot. *You never have "
            "to share anything you don't want to.*"
        )
        error = self._("TODO")

        return WhatsAppButtonState(
            self,
            question=question,
            choices=[Choice("ok", "OK 👍")],
            error=error,
            next={
                "ok": "state_pre_terms",
            },
        )

    async def state_pre_terms(self):
        await self.worker.publish_message(
            self.inbound.reply(self._("Awesome, thanks 😌  — So, first things first..."))
        )
        return await self.go_to_state("state_terms")

    async def state_terms(self):
        question = self._(
            "🔒 *TERMS & CONDITIONS*\n"
            "Young Africa Live: Privacy Policy\n"
            "-----\n"
            "\n"
            "*Before we chat, I need to make sure you’re 💯% cool with our Privacy "
            "Policy.*\n"
            "\n"
            "It explains your rights and choices when it comes to how we use and "
            "store your info.\n"
            "\n"
            "*We good to keep going?*\n"
            "\n"
            "1 - READ Privacy Policy\n"
            "2 - I ACCEPT (continue)\n"
            "3 - I DON'T ACCEPT"
        )
        error = self._("TODO")

        return WhatsAppListState(
            self,
            question=question,
            button="Privacy Policy",
            choices=[
                Choice("read", "Read Privacy Policy"),
                Choice("accept", "I Accept"),
                Choice("decline", "I Don't Accept"),
            ],
            error=error,
            next={
                "read": "state_read_terms",
                "accept": "state_submit_terms_and_conditions",
                "decline": "state_decline_confirm",
            },
        )

    async def state_decline_confirm(self):
        question = self._(
            "🔒 *TERMS & CONDITIONS*\n"
            "Young Africa Live: Privacy Policy\n"
            "-----\n"
            "\n"
            "⚠️ *Sure you wanna bounce?*\n"
            "\n"
            "Unfortunately, I can't share any info with you if you haven't accepted "
            "the Privacy Policy 😔.\n"
            "\n"
            "It's important for your safety and confidentiality...\n"
            "\n"
            "1. ✅ ACCEPT Privacy Policy\n"
            "2. 🛑  END chat"
        )
        error = self._("TODO")

        return WhatsAppButtonState(
            self,
            question=question,
            choices=[
                Choice("end", "End chat"),
                Choice("accept", "Accept Privacy Policy"),
            ],
            error=error,
            next={
                "end": "state_decline",
                "accept": "state_submit_terms_and_conditions",
            },
        )

    async def state_submit_terms_and_conditions(self):
        # TODO: Update turn profile terms_accepted=True

        return await self.go_to_state(OnboardingApplication.START_STATE)
