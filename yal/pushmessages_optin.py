import asyncio
import logging

from vaccine.base_application import BaseApplication
from vaccine.states import Choice, WhatsAppButtonState
from vaccine.utils import get_display_choices
from yal import rapidpro
from yal.askaquestion import Application as AaqApplication
from yal.mainmenu import Application as MainMenuApplication
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
                    "If you'd like, I can also send you notifications once a day with "
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
