import re
from typing import List

from vaccine.base_application import BaseApplication
from vaccine.models import Message
from vaccine.states import Choice, EndState, WhatsAppButtonState


class WhatsAppExitButtonState(WhatsAppButtonState):
    async def process_message(self, message: Message):
        choice = self._get_choice(message.content)
        if choice is None:
            state = await self.app.go_to_state("state_exit")
            return await state.process_message(message)
        else:
            return await super().process_message(message)


class Application(BaseApplication):
    START_STATE = "state_start"

    async def process_message(self, message: Message) -> List[Message]:
        if message.session_event == Message.SESSION_EVENT.CLOSE:
            self.state_name = "state_timeout"

        keyword = re.sub(r"\W+", " ", message.content or "").strip().lower()
        # Exit keywords
        if keyword in (
            "menu",
            "0",
            "main menu",
            "cases",
            "vaccine",
            "vaccines",
            "latest",
        ):
            self.state_name = "state_exit"

        return await super().process_message(message)

    async def state_timeout(self):
        return EndState(
            self,
            # TODO: Proper copy
            self._("We haven't heard from you in while."),
        )

    async def state_exit(self):
        return EndState(self, "", helper_metadata={"automation_handle": True})

    async def state_start(self):
        question = self._(
            "*REPORT* 📵 Powered by ```Real411```\n"
            "\n"
            "There is a lot of information going around related to the COVID-19 "
            "pandemic. Some of this information may be false and potentially harmful. "
            "Help to stop the spread of inaccurate or misleading information by "
            "reporting it here."
        )
        return WhatsAppExitButtonState(
            self,
            question=question,
            choices=[
                Choice("tell_me_more", self._("Tell me more")),
                Choice("terms_and_conditions", self._("View and Accept T&Cs")),
            ],
            # Goes to state_exit for error handling
            error="",
            next={
                # TODO: add tell me more state
                "tell_me_more": "state_terms",
                "terms_and_conditions": "state_terms",
            },
        )

    async def state_terms(self):
        question = self._(
            "*REPORT* 📵 Powered by ```Real411```\n"
            "\n"
            "Your information is kept private and confidential and only used with your "
            "consent for the purpose of reporting disinformation.\n"
            "\n"
            # TODO: add privacy policy
            "Do you agree to the attached PRIVACY POLICY?"
        )
        return WhatsAppExitButtonState(
            self,
            question=question,
            choices=[Choice("yes", "I agree"), Choice("no", "No thanks")],
            # Goes to state_exit for error handling
            error="",
            next={
                "yes": "state_province",
                # TODO: Add state for if they select no
                "no": "state_province",
            },
        )
