import re
from typing import List

from vaccine.base_application import BaseApplication
from vaccine.models import Message
from vaccine.states import Choice, EndState, FreeText, WhatsAppButtonState
from vaccine.utils import display_phonenumber
from vaccine.validators import nonempty_validator, phone_number_validator


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
            error=question,
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

    async def state_select_number(self):
        question = self._("Can the hotline team call you back on {number}?").format(
            number=display_phonenumber(self.user.addr)
        )
        return WhatsAppButtonState(
            self,
            question=question,
            choices=[
                Choice("this_number", self._("Use this number")),
                Choice("different_number", self._("Use a different number")),
            ],
            # TODO: Get a proper error messsage
            error=question,
            next="state_enter_number",
        )

    async def state_enter_number(self):
        if self.user.answers["state_select_number"] == "this_number":
            self.save_answer("state_enter_number", self.user.addr)
            return await self.go_to_state("state_submit_request")

        return FreeText(
            self,
            question=self._("Please TYPE the CELL PHONE NUMBER we can contact you on."),
            next="state_submit_request",
            check=phone_number_validator(
                self._(
                    "⚠️ Please type a valid cell phone number.\n" "Example _081234567_"
                )
            ),
        )
