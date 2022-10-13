import asyncio
import logging

from vaccine.base_application import BaseApplication
from vaccine.states import Choice, WhatsAppButtonState, WhatsAppListState
from yal import contentrepo, rapidpro
from yal.onboarding import Application as OnboardingApplication
from yal.utils import get_generic_error, normalise_phonenumber

logger = logging.getLogger(__name__)


class Application(BaseApplication):
    START_STATE = "state_welcome"

    async def state_welcome(self):
        question = self._(
            "\n".join(
                [
                    "👋🏾 *HOWZIT! Welcome to B-Wise!*",
                    "",
                    "I'm a chatbot service 🤖 here to answer questions about "
                    "your body, sex, relationships and health 😌",
                    "",
                    "Most of the time you'll be talking to me, but I can also connect "
                    "you to an actual human (loveLife counsellor) if you need help.",
                    "",
                    "Let's start by creating your profile (just click the button "
                    "below) ⬇️",
                ]
            )
        )
        error = self._(get_generic_error())

        return WhatsAppButtonState(
            self,
            question=question,
            choices=[Choice("create", "Create a profile")],
            error=error,
            next="state_terms",
        )

    async def state_terms(self):
        question = self._(
            "\n".join(
                [
                    "🔒 TERMS & CONDITIONS / *B-Wise: Privacy Policy*",
                    "-----",
                    "",
                    "*Before we chat, I need to make sure... Are you 💯% cool with "
                    "me sending you messages?*",
                    "",
                    "You can read the Privacy Policy, which explains your rights and "
                    "choices when it comes to how we use and store your info.",
                    "",
                    "1. Yes, cool with me",
                    "2. No, not keen",
                    "3. Read Privacy Policy",
                ]
            )
        )
        return WhatsAppListState(
            self,
            question=question,
            button="Privacy Policy",
            choices=[
                Choice("accept", "Yes, cool with me"),
                Choice("decline", "No, not keen"),
                Choice("read", "Read Privacy Policy"),
            ],
            error=self._(get_generic_error()),
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
            "\n".join(
                [
                    "🔒 TERMS & CONDITIONS / *B-Wise: Privacy Policy*",
                    "-----",
                    "",
                    "⚠️ *Are you Sure?*",
                    "",
                    "Unfortunately, I can't share any info with you if you haven't "
                    "accepted the Privacy Policy 😔.",
                    "",
                    "It's important for your safety and confidentiality...",
                    "",
                    "*1. ACCEPT* Privacy Policy",
                    "*2. END* chat",
                ]
            )
        )
        return WhatsAppButtonState(
            self,
            question=question,
            choices=[
                Choice("accept", "ACCEPT"),
                Choice("end", "END chat"),
            ],
            error=self._(get_generic_error()),
            next={
                "end": "state_decline_1",
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
                    "*HI* whenever you're ready to chat again. In the meantime, be "
                    "wise and look after yourself 😉👋🏾"
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
                "*Check out B-Wise online!* 👆🏾\n"
                "\n"
                "https://bwisehealth.com/ \n"
                "\n"
                "You'll find loads of info about sex, relationships and health. It's "
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

        await self.worker.publish_message(
            self.inbound.reply(self._("Excellent - now we can get you set up."))
        )
        await asyncio.sleep(0.5)
        return await self.go_to_state(OnboardingApplication.START_STATE)
