import re
from typing import List

from vaccine.base_application import BaseApplication
from vaccine.models import Message
from vaccine.states import Choice, EndState, FreeText, WhatsAppButtonState
from vaccine.validators import nonempty_validator


class Application(BaseApplication):
    START_STATE = "state_menu"

    async def process_message(self, message: Message) -> List[Message]:
        keyword = re.sub(r"\W+", " ", message.content or "").strip().lower()
        # Exit keywords
        if keyword in ("menu", "0", "main menu"):
            self.state_name = "state_exit"

        return await super().process_message(message)

    async def state_exit(self):
        return EndState(self, "", helper_metadata={"automation_handle": True})

    async def state_menu(self):
        question = self._(
            "The toll-free hotline is available for all your vaccination questions!\n"
            "Call 0800 029 999\n"
            "\n"
            "⏰ Operating hours for *Registration and appointment queries*\n"
            "Monday to Friday\n"
            "7am-8pm\n"
            "Saturdays, Sundays and Public Holidays\n"
            "8am-6pm\n"
            "\n"
            "---------------------\n"
            "\n"
            "The toll-free hotline is also available for you to call *24 hours a day*, "
            "every day for *Emergencies, health advice and post vaccination queries*"
        )
        return WhatsAppButtonState(
            self,
            question=question,
            header=self._("💉 *VACCINE SUPPORT*"),
            choices=[
                Choice("call_me_back", self._("Call me back")),
                Choice("main_menu", self._("Main Menu")),
            ],
            # TODO: Get proper error message
            error="Please select a valid choice",
            next="state_full_name",
        )

    async def state_full_name(self):
        question = self._(
            "Please type your NAME\n"
            "(This will be given to the hotline team to use when they call you back)"
        )
        return FreeText(
            self,
            question=question,
            next="state_select_number",
            # TODO: Get proper error message
            check=nonempty_validator(question),
        )
