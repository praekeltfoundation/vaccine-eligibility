import asyncio
import logging

from vaccine.base_application import BaseApplication
from vaccine.states import Choice, WhatsAppButtonState, WhatsAppListState
from yal import contentrepo, rapidpro
from yal.onboarding import Application as OnboardingApplication
from yal.pleasecallme import Application as PleaseCallMeApplication
from yal.utils import GENERIC_ERROR, normalise_phonenumber

logger = logging.getLogger(__name__)


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
        await asyncio.sleep(0.5)
        return await self.go_to_state("state_emergency_prompt")

    async def state_emergency_prompt(self):
        question = self._(
            "🆘 *Are you in trouble?*\n"
            "-----\n"
            "\n"
            "🙍🏾‍♀️ Before we continue, I just want to check - *do you need to speak "
            "to a human now?*\n"
            "\n"
            "*REPLY:*\n"
            "*1* - Yes, I need human help\n"
            "*2* - No, I'm good"
        )
        return WhatsAppButtonState(
            self,
            question=question,
            choices=[
                Choice("yes", "Yes, I need help now"),
                Choice("no", "No, I'm good"),
            ],
            error=self._(GENERIC_ERROR),
            next={
                "yes": PleaseCallMeApplication.START_STATE,
                "no": "state_emergency_info",
            },
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
        await asyncio.sleep(0.5)
        return await self.go_to_state("state_get_to_know")

    async def state_get_to_know(self):
        question = self._(
            "*Let's get to know each other better*\n"
            "\n"
            "Do you mind if I ask you a few Qs? It will help me do a better job at "
            "answering your questions. 🙃\n"
            "\n"
            "*Reply:*\n"
            "*1* - OK\n"
            "*2* - Why?"
        )
        return WhatsAppButtonState(
            self,
            question=question,
            choices=[Choice("ok", "Ok"), Choice("why", "Why?")],
            error=self._(GENERIC_ERROR),
            next={
                "ok": "state_pre_terms",
                "why": "state_get_to_know_why",
            },
        )

    async def state_get_to_know_why(self):
        question = self._(
            "🤔 *Why the questions?*\n"
            "\n"
            "🙍🏾‍♀️ These questions help the B-Wise team improve your experience with "
            "me. The more I learn from you, the better the service will be for you.\n"
            "\n"
            "*Don't worry, you never have to share anything you don't want to. 🙂*\n"
            "\n"
            "*Ready?*\n"
            "*1* - Ok\n"
            "*2* - No Thanks"
        )
        return WhatsAppButtonState(
            self,
            question=question,
            choices=[Choice("ok", "Ok"), Choice("no", "No thanks")],
            error=self._(GENERIC_ERROR),
            next={"ok": "state_pre_terms", "no": "state_decline_get_to_know"},
        )

    async def state_decline_get_to_know(self):
        await self.worker.publish_message(
            self.inbound.reply(
                self._(
                    "😫 *We're sad to see you go.\n"
                    "\n"
                    "🙍🏾‍♀️ Although we'd love to chat, we understand that you might "
                    "not be ready. If you change your mind, just sent the word HI "
                    "to this number and we can start again.\n"
                    "\n"
                    "*See you next time*👋🏾"
                )
            )
        )
        await asyncio.sleep(0.5)
        return await self.go_to_state("state_decline_2")

    async def state_pre_terms(self):
        await self.worker.publish_message(
            self.inbound.reply(self._("Awesome, thanks 😌  — So, first things first..."))
        )
        await asyncio.sleep(0.5)
        return await self.go_to_state("state_terms")

    async def state_terms(self):
        question = self._(
            "🔒 *TERMS & CONDITIONS*\n"
            "_B-Wise by Young Africa Live: Privacy Policy_\n"
            "-----\n"
            "\n"
            "*Before we chat, I need to make sure you’re 💯% cool with our Privacy "
            "Policy.*\n"
            "\n"
            "It explains your rights and choices when it comes to how we use and "
            "store your info.\n"
            "\n"
            "*1 - READ* Privacy Policy\n"
            "*2 - I ACCEPT* (continue)\n"
            "*3 - I DON'T ACCEPT*"
        )
        return WhatsAppListState(
            self,
            question=question,
            button="Privacy Policy",
            choices=[
                Choice("read", "Read Privacy Policy"),
                Choice("accept", "I Accept"),
                Choice("decline", "I Don't Accept"),
            ],
            error=self._(GENERIC_ERROR),
            next={
                "read": "state_terms_pdf",
                "accept": "state_submit_terms_and_conditions",
                "decline": "state_decline_confirm",
            },
        )

    async def state_terms_pdf(self):
        await self.worker.publish_message(
            self.inbound.reply(
                None,
                helper_metadata={"document": contentrepo.get_privacy_policy_url()},
            )
        )
        await asyncio.sleep(1.5)
        return await self.go_to_state("state_terms")

    async def state_decline_confirm(self):
        question = self._(
            "🔒 *TERMS & CONDITIONS*\n"
            "_Young Africa Live: Privacy Policy_\n"
            "-----\n"
            "\n"
            "⚠️ *Are you Sure?*\n"
            "\n"
            "Unfortunately, I can't share any info with you if you haven't accepted "
            "the Privacy Policy 😔.\n"
            "\n"
            "It's important for your safety and confidentiality...\n"
            "\n"
            "*1. ACCEPT* Privacy Policy\n"
            "*2. END* chat"
        )
        return WhatsAppButtonState(
            self,
            question=question,
            choices=[
                Choice("end", "END chat"),
                Choice("accept", "ACCEPT Privacy Policy"),
            ],
            error=self._(GENERIC_ERROR),
            next={
                "end": "state_decline",
                "accept": "state_submit_terms_and_conditions",
            },
        )

    async def state_decline_1(self):
        await self.worker.publish_message(
            self.inbound.reply(
                self._(
                    "*No stress—I get it.* 😌\n"
                    "\n"
                    "It's wise to think these things over. Your online safety is "
                    "important to us too.\n"
                    "\n"
                    "If you change your mind though, we'll be here! Just send me a "
                    "*HI* whenever you're ready to chat again. In the mean time, be "
                    "wise, and look after yourself 😉👋🏾"
                )
            )
        )
        await asyncio.sleep(0.5)
        return await self.go_to_state("state_decline_2")

    async def state_decline_2(self):
        error = self._("Send *HI* to start again.")

        return WhatsAppButtonState(
            self,
            question=self._(
                "*Need quick answers?*\n"
                "*Check out B-Wise online!*👆🏾\n"
                "\n"
                "https://bwisehealth.com/ \n"
                "\n"
                "You'll find loads of sex, relationships and health info there. It's "
                "also my other virtual office.\n"
                "\n"
                "Feel free to drop me a virtual _howzit_ there too!\n"
                "\n"
                "-----\n"
                "Send *HI* to start again."
            ),
            choices=[
                Choice("hi", "HI"),
            ],
            error=error,
            next={
                "hi": "state_welcome",
            },
        )

    async def state_submit_terms_and_conditions(self):
        msisdn = normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.lstrip(" + ")

        error = await rapidpro.update_profile(whatsapp_id, {"terms_accepted": "True"})
        if error:
            return await self.go_to_state("state_error")

        return await self.go_to_state(OnboardingApplication.START_STATE)
