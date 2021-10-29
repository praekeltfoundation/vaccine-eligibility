import json
import re
from typing import List, Optional, Tuple
from urllib.parse import urljoin

import aiohttp
from aiohttp_client_cache import CacheBackend, CachedSession

from vaccine import real411_config as config
from vaccine.base_application import BaseApplication
from vaccine.models import Message
from vaccine.states import (
    Choice,
    ChoiceState,
    EndState,
    FreeText,
    WhatsAppButtonState,
    WhatsAppListState,
)
from vaccine.utils import enforce_string, normalise_phonenumber
from vaccine.validators import email_validator, nonempty_validator

cache_backend = CacheBackend(expire_after=60)


def get_real411_api_client():
    return CachedSession(
        cache=cache_backend,
        timeout=aiohttp.ClientTimeout(total=5),
        headers={
            "Accept": "application/json",
            "User-Agent": "real411-whatsapp",
            "x-api-key": config.REAL411_TOKEN,
        },
    )


async def get_real411_form_data():
    async with get_real411_api_client() as session:
        response = await session.get(
            url=enforce_string(urljoin(config.REAL411_URL, "form-data"))
        )
        response.raise_for_status()
        return await response.json()


async def submit_real411_form(
    terms: bool,
    name: str,
    phone: str,
    source: int,
    reason: str,
    email: Optional[str] = None,
    source_url: Optional[str] = None,
) -> Tuple[int, List[str]]:
    # TODO: files
    for complaint_type in (await get_real411_form_data())["ComplaintType"]:
        if (
            "dis" in complaint_type["code"].lower()
            or "disinformation" in complaint_type["type"].lower()
        ):
            break
    for language in (await get_real411_form_data())["Language"]:
        if "end" in language["code"].lower() or "english" in language["name"].lower():
            break
    data = {
        "complaint_source": config.REAL411_IDENTIFIER,
        "agree": terms,
        "name": name,
        "phone": phone,
        "complaint_types": json.dumps([{"id": complaint_type["id"], "reason": reason}]),
        "language": language["id"],
        "source": source,
    }
    if email:
        data["email"] = email
    if source_url:
        data["source_url"] = source_url
    async with get_real411_api_client() as session:
        response = await session.post(
            url=enforce_string(urljoin(config.REAL411_URL, "submit/v2")), json=data
        )
        response.raise_for_status()
        response_data = await response.json()
        return (response_data["complaint_ref"], response_data["file_urls"])


async def finalise_real411_form(form_reference: str):
    async with get_real411_api_client() as session:
        response = await session.post(
            url=enforce_string(urljoin(config.REAL411_URL, "complaints/finalize")),
            json={"ref": form_reference},
        )
        response.raise_for_status()


class WhatsAppExitButtonState(WhatsAppButtonState):
    async def process_message(self, message: Message):
        choice = self._get_choice(message.content)
        if choice is None:
            state = await self.app.go_to_state("state_exit")
            return await state.process_message(message)
        else:
            return await super().process_message(message)


class WhatsAppExitListState(WhatsAppListState):
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
                "yes": "state_first_name",
                # TODO: Add state for if they select no
                "no": "state_first_name",
            },
        )

    async def state_first_name(self):
        question = self._(
            "*REPORT* 📵 Powered by ```Real411```\n" "\n" "Reply with your FIRST NAME:"
        )
        return FreeText(
            self,
            question=question,
            next="state_surname",
            # TODO: Add error message for empty text
            check=nonempty_validator(question),
        )

    async def state_surname(self):
        question = self._(
            "*REPORT* 📵 Powered by ```Real411```\n" "\n" "Reply with your SURNAME:"
        )
        return FreeText(
            self,
            question=question,
            next="state_email",
            # TODO: Add error message for empty text
            check=nonempty_validator(question),
        )

    async def state_email(self):
        question = self._(
            "*REPORT* 📵 Powered by ```Real411```\n"
            "\n"
            "Please TYPE your EMAIL address. (Or type SKIP if you are unable to share "
            "an email address.)"
        )
        # TODO: Add error message, maybe including error description from library
        return FreeText(
            self,
            question=question,
            next="state_source_type",
            check=email_validator(error_text=question, skip_keywords=["skip"]),
        )

    async def state_source_type(self):
        source_types = (await get_real411_form_data())["Source"]
        question = self._(
            "*REPORT* 📵 Powered by ```Real411```\n"
            "\n"
            "Please tell us where you saw/heard the information being reported"
        )
        return ChoiceState(
            self,
            question=question,
            choices=[Choice(s["id"], s["name"]) for s in source_types],
            error=question,
            next="state_description",
        )

    async def state_description(self):
        question = self._(
            "*REPORT* 📵 Powered by ```Real411```\n"
            "\n"
            "Please describe the information being reported in your own words:"
        )
        # TODO: Add error message
        return FreeText(
            self,
            question=question,
            next="state_media",
            check=nonempty_validator(question),
        )

    async def state_media(self):
        # TODO: split out into separate URL and media steps
        # TODO: make URL or media or both required, depending on API result
        # TODO: for whatsapp type, allow text only, if forwarded message
        question = self._(
            "*REPORT* 📵 Powered by ```Real411```\n"
            "\n"
            "Please share any additional information such as screenshots, photos, "
            "voicenotes or links (or type SKIP)"
        )
        # TODO: Add error message
        # TODO: What if they want to send multiple media items?
        return FreeText(
            self,
            question=question,
            next="state_opt_in",
            check=nonempty_validator(question),
        )

    async def state_opt_in(self):
        question = self._(
            "*REPORT* 📵 Powered by ```Real411```\n"
            "\n"
            "To complete your report please confirm that all the information is "
            "accurate to the best of your knowledge and that you give ContactNDOH "
            "permission to send you message about the outcome of your report"
        )
        return WhatsAppExitButtonState(
            self,
            question=question,
            choices=[Choice("yes", "I agree"), Choice("no", "No")],
            # Goes to state_exit for error handling
            error="",
            next="state_submit_report",
        )

    async def state_submit_report(self):
        answers = self.user.answers
        email = answers["state_email"]
        if email.strip().lower() == "skip":
            email = None
        form_reference, _ = await submit_real411_form(
            terms=answers["state_terms"] == "yes",
            name=f"{answers['state_first_name']} {answers['state_surname']}",
            phone=normalise_phonenumber(self.user.addr),
            source=answers["state_source_type"],
            reason=answers["state_description"],
            email=email,
        )
        await finalise_real411_form(form_reference)
        return await self.go_to_state("state_success")

    async def state_success(self):
        text = self._(
            "*REPORT* 📵 Powered by ```Real411```\n"
            "\n"
            "Thank you for helping to stop the spread of inaccurate or misleading "
            "information!\n"
            "\n"
            "Look out for messages from us in the next few days\n"
            "\n"
            "Reply 0 to return to the main MENU"
        )
        return EndState(self, text=text)
