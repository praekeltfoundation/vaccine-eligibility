import json
import re
from asyncio import gather
from base64 import b64decode
from typing import List, Optional, Tuple
from urllib.parse import urljoin

import aiohttp
from aiohttp_client_cache import CacheBackend, CachedSession

from vaccine import real411_config as config
from vaccine.base_application import BaseApplication
from vaccine.models import Message
from vaccine.states import Choice, EndState, FreeText, WhatsAppButtonState
from vaccine.utils import enforce_string, normalise_phonenumber, save_media
from vaccine.validators import email_validator, enforce_mime_types

cache_backend = CacheBackend(expire_after=60)

BLANK_PNG = b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAAAXNSR0IArs4c6QAAAAtJREFUGFdjYAACAA"
    "AFAAGq1chRAAAAAElFTkSuQmCC"
)

ACCEPTED_MIME_TYPES = [
    "video/mp4",
    "image/jpeg",
    "image/png",
    "application/pdf",
    "audio/ogg",
    "video/ogg",
    "audio/wav",
    "audio/x-wav",
]


class Real411APIException(Exception):
    """
    Error when interacting with the Real411 API
    """


def get_real411_api_client() -> aiohttp.ClientSession:
    return CachedSession(
        cache=cache_backend,
        headers={
            "Accept": "application/json",
            "User-Agent": "contactndoh-real411",
            "x-api-key": config.REAL411_TOKEN,
        },
    )


def check_real411_api_response(data: dict) -> None:
    if not data.get("success") or data.get("errors"):
        raise Real411APIException(f"Error in API response: {data.get('errors')}")


async def get_real411_single_resource(resource_type: str, resource_code: str) -> dict:
    async with get_real411_api_client() as session:
        response = await session.get(
            url=enforce_string(urljoin(config.REAL411_URL, resource_type)),
            params={"limit": -1, "code": resource_code},
        )
        response.raise_for_status()
        data = await response.json()
        check_real411_api_response(data)
        if data["data"]["total"] != 1:
            raise Real411APIException(
                f"{data['data']['total']} {resource_type} returned for {resource_code}"
            )
        return data["data"]["rows"][0]


async def submit_real411_form(
    terms: bool,
    name: str,
    phone: str,
    reason: str,
    email: Optional[str] = None,
    file_names: Optional[List[dict]] = None,
) -> Tuple[str, List[str], str]:
    complaint_type, language, source = await gather(
        get_real411_single_resource("complaint-type", "DIS"),
        get_real411_single_resource("language", "ENG"),
        get_real411_single_resource("source", "WHT"),
    )
    data = {
        "agree": terms,
        "name": name,
        "email": email or "reporting@praekelt.org",
        "phone": phone,
        "complaint_types": json.dumps([{"id": complaint_type["id"], "reason": reason}]),
        "language": language["id"],
        "source": source["id"],
        "file_names": file_names or [],
    }
    async with get_real411_api_client() as session:
        response = await session.post(
            url=enforce_string(urljoin(config.REAL411_URL, "complaint")), json=data
        )
        response.raise_for_status()
        response_data = await response.json()
        check_real411_api_response(response_data)
        return (
            response_data["data"]["complaint_ref"],
            response_data["data"]["file_urls"],
            response_data["data"]["real411_backlink"],
        )


async def finalise_real411_form(form_reference: str) -> None:
    async with get_real411_api_client() as session:
        response = await session.post(
            url=enforce_string(urljoin(config.REAL411_URL, "complaint/finalize")),
            json={"ref": form_reference},
        )
        response.raise_for_status()
        check_real411_api_response(await response.json())


def get_whatsapp_api() -> aiohttp.ClientSession:
    return aiohttp.ClientSession(
        headers={
            "User-Agent": "contactndoh-real411",
            "Authorization": f"Bearer {config.WHATSAPP_TOKEN}",
        },
    )


async def get_whatsapp_media(media_id: str) -> bytes:
    async with get_whatsapp_api() as session:
        response = await session.get(
            url=urljoin(config.WHATSAPP_URL, f"v1/media/{media_id}")
        )
        response.raise_for_status()
        return await response.read()


def get_healthcheck_api() -> aiohttp.ClientSession:
    return aiohttp.ClientSession(
        headers={
            "User-Agent": "contactndoh-real411",
            "Authorization": f"Token {config.HEALTHCHECK_TOKEN}",
        }
    )


async def store_complaint_id(complaint_ref: str, msisdn: str) -> None:
    async with get_healthcheck_api() as session:
        response = await session.post(
            url=enforce_string(
                urljoin(config.HEALTHCHECK_URL, "v2/real411/complaint/")
            ),
            json={"complaint_ref": complaint_ref, "msisdn": msisdn},
        )
        response.raise_for_status()


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
            self._(
                "We haven't heard from you in while. Reply *0* to return to the main "
                "*MENU*, or *REPORT* to try again."
            ),
        )

    async def state_exit(self):
        return EndState(self, "", helper_metadata={"automation_handle": True})

    async def state_start(self):
        question = self._(
            "*REPORT* 📵 powered by ```Real411.org```\n"
            "\n"
            "There is a lot of information about COVID-19 being shared on WhatsApp. "
            "Some of this information is false and could be harmful. Report misleading "
            "or inaccurate information here to help stop its spread on WhatsApp."
        )
        error = self._(
            "This service works best when you use the options given. Please try using "
            "the buttons below or reply *0* to return the main *MENU*."
        )
        return WhatsAppButtonState(
            self,
            question=question,
            choices=[
                Choice("tell_me_more", self._("Learn more")),
                Choice("terms_and_conditions", self._("Continue")),
            ],
            error=error,
            next={
                "tell_me_more": "state_tell_me_more",
                "terms_and_conditions": "state_terms_pdf",
            },
        )

    async def state_tell_me_more(self):
        question = self._(
            "*REPORT* 📵 powered by ```Real411.org``` allows you to report WhatsApp "
            "messages that include:\n"
            "- disinformation\n"
            "- hate speech\n"
            "- incitement to violence\n"
            "- harassment of a journalist\n"
            "\n"
            "*Disinformation* is false, inaccurate or misleading information that aims "
            "to cause public harm on purpose.\n"
            "\n"
            "*Hate speech* includes messages that intend to harm a person or group, or "
            "make them feel less than other people.\n"
            "\n"
            "*Incitement to violence* includes messages that encourage violence that "
            "could cause harm, damage or even death.\n"
            "\n"
            "*Harrassment of a journalist* includes messages to members of the media "
            "that aim to humiliate, shame, threaten or intimidate them.\n"
            "\n"
            "Use this service to report WhatsApp messages that were forwarded to you "
            "personally or to a WhatsApp group that your are a member of. You can "
            "report what you've seen on social media, websites, TV or radio at "
            "www.real411.org/complaints-create."
        )
        error = self._(
            "This service works best when you use the options given. Please try using "
            "the buttons below."
        )
        return WhatsAppButtonState(
            self,
            question=question,
            choices=[
                Choice("continue", self._("Continue")),
                Choice("exit", self._("Exit")),
            ],
            error=error,
            next={
                "continue": "state_terms_pdf",
                "exit": "state_refuse_terms",
            },
        )

    async def state_terms_pdf(self):
        self.messages.append(
            self.inbound.reply(
                None,
                helper_metadata={
                    "document": "https://healthcheck-rasa-images.s3.af-south-1."
                    "amazonaws.com/Real411_Privacy+Policy_WhatsApp_02112021.docx.pdf"
                },
            )
        )
        return await self.go_to_state("state_terms")

    async def state_terms(self):
        question = self._(
            "*REPORT* 📵 powered by ```Real411.org```\n"
            "\n"
            "Your information is kept private and confidential. It is only used with "
            "your permission to report disinformation.\n"
            "\n"
            "Do you agree to the attached PRIVACY POLICY?"
        )
        error = self._(
            "This service works best when you use the options given. Try using the "
            "buttons below or reply *0* to return the main *MENU*.\n"
            "\n"
            "Do you agree to our PRIVACY POLICY?"
        )
        return WhatsAppButtonState(
            self,
            question=question,
            choices=[Choice("yes", "I agree"), Choice("no", "No thanks")],
            error=error,
            next={
                "yes": "state_first_name",
                "no": "state_refuse_terms",
            },
        )

    async def state_refuse_terms(self):
        return EndState(
            self,
            self._(
                "*REPORT* 📵 Powered by ```Real411.org```\n"
                "\n"
                "If you change your mind, type *REPORT* anytime.\n"
                "Reply *0* to return to the main *MENU*"
            ),
        )

    async def state_first_name(self):
        question = self._(
            "*REPORT* 📵 Powered by ```Real411.org```\n"
            "\n"
            "Reply with your FIRST NAME:"
        )
        return FreeText(
            self,
            question=question,
            next="state_surname",
        )

    async def state_surname(self):
        question = self._(
            "*REPORT* 📵 Powered by ```Real411.org```\n" "\n" "Reply with your SURNAME:"
        )
        return FreeText(
            self,
            question=question,
            next="state_confirm_name",
        )

    async def state_confirm_name(self):
        return WhatsAppButtonState(
            self,
            question=self._(
                "*REPORT* 📵 Powered by ```Real411.org```\n"
                "\n"
                "Please confirm that your full name is {first_name} {surname}"
            ).format(
                first_name=self.user.answers["state_first_name"],
                surname=self.user.answers["state_surname"],
            ),
            choices=[
                Choice("yes", self._("Confirm")),
                Choice("no", self._("Edit name")),
            ],
            error=self._(
                "This service works best when you use the options given. Try using the "
                "buttons below or reply *0* to return the main *MENU*.\n"
                "\n"
                "Please confirm your full name as {first_name} {surname}"
            ).format(
                first_name=self.user.answers["state_first_name"],
                surname=self.user.answers["state_surname"],
            ),
            next={"yes": "state_email", "no": "state_first_name"},
        )

    async def state_email(self):
        question = self._(
            "*REPORT* 📵 powered by ```Real411.org```\n"
            "\n"
            "Please TYPE your EMAIL address. (Or type SKIP if you can't share an email "
            "address.)"
        )
        error = self._(
            "*REPORT* 📵 powered by ```Real411.org```\n"
            "\n"
            "Please TYPE a valid EMAIL address or type *SKIP* if you can't share an "
            "email address"
        )
        return FreeText(
            self,
            question=question,
            next="state_description",
            check=email_validator(error_text=error, skip_keywords=["skip", "*skip*"]),
        )

    async def state_description(self):
        question = self._(
            "*REPORT* 📵 powered by ```Real411.org```\n"
            "\n"
            "To report a WhatsApp message that contains misinformation about COVID-19, "
            "please type a description of the complaint in your own words OR simply "
            "forward the message that you would like to report."
        )
        error = self._(
            "I'm afraid we cannot read the file that you sent through.\n"
            "\n"
            "We can only read video, image, document or audio files that have these "
            "letters at the end of the file name:\n"
            ".mp4\n"
            ".jpeg\n"
            ".png\n"
            ".pdf\n"
            ".ogg\n"
            ".wave\n"
            ".x-wav\n"
            "\n"
            "If you cannot send one of these files, don't worry. We will investigate "
            "based on the description of the problem that you already typed in."
        )
        return FreeText(
            self,
            question=question,
            next="state_media",
            check=[
                enforce_mime_types(self, error, ACCEPTED_MIME_TYPES),
                save_media(self, "state_description_file"),
            ],
        )

    async def state_media(self):
        question = self._(
            "*REPORT* 📵 powered by ```Real411.org```\n"
            "\n"
            "Please share any extra information, such as screenshots, photos, "
            "or links (or type SKIP)"
        )
        error = self._(
            "I'm afraid we cannot read the file that you sent through.\n"
            "\n"
            "We can only read video, image, document or audio files that have these "
            "letters at the end of the file name:\n"
            ".mp4\n"
            ".jpeg\n"
            ".png\n"
            ".pdf\n"
            ".ogg\n"
            ".wave\n"
            ".x-wav\n"
            "\n"
            "If you cannot send one of these files, don't worry. We will investigate "
            "based on the description of the problem that you already typed in."
        )
        return FreeText(
            self,
            question=question,
            next="state_opt_in",
            check=[
                enforce_mime_types(self, error, ACCEPTED_MIME_TYPES),
                save_media(self, "state_media_file"),
            ],
        )

    async def state_opt_in(self):
        question = self._(
            "*REPORT* 📵 powered by ```Real411.org```\n"
            "\n"
            "To complete your report, please confirm that all the information you've "
            "given is accurate to the best of your knowledge and that you give "
            "ContactNDOH permission to send you a message about the outcome of your "
            "report"
        )
        error = self._(
            "This service works best when you use the options given. Please try using "
            "the buttons below or reply *0* to return the main *MENU*.\n"
            "\n"
            "Do you agree to share your report with Real411.org?"
        )
        return WhatsAppButtonState(
            self,
            question=question,
            choices=[Choice("yes", "I agree"), Choice("no", "No")],
            error=error,
            next={
                "yes": "state_send_interim_message",
                "no": "state_do_not_share",
            },
        )

    async def state_send_interim_message(self):
        await self.worker.publish_message(
            self.inbound.reply(
                self._(
                    "*REPORT* 📵 powered by ```Real411.org```\n"
                    "\n"
                    "Thank you for your submission\n"
                    "⏳ Please wait while we process your submission to give you a "
                    "reference number and a link to track your submission"
                )
            )
        )
        return await self.go_to_state("state_submit_report")

    async def state_submit_report(self):
        answers = self.user.answers
        email = answers["state_email"]
        if email.strip().lower() == "skip":
            email = None
        files = []
        if answers.get("state_description_file"):
            file = json.loads(answers["state_description_file"])
            files.append({"name": file["id"], "type": file["mime_type"]})
        if answers.get("state_media_file"):
            file = json.loads(answers["state_media_file"])
            files.append({"name": file["id"], "type": file["mime_type"]})
        if not files:
            files.append({"name": "placeholder", "type": "image/png"})

        self.form_reference, file_urls, self.backlink = await submit_real411_form(
            terms=answers["state_terms"] == "yes",
            name=f"{answers['state_first_name']} {answers['state_surname']}",
            phone=normalise_phonenumber(self.user.addr),
            reason=f"{answers['state_description']}\n\n{answers['state_media']}",
            email=email,
            file_names=files,
        )
        await store_complaint_id(self.form_reference, self.user.addr)
        async with aiohttp.ClientSession(
            headers={"User-Agent": "contactndoh-real411"},
        ) as session:
            for file, file_url in zip(files, file_urls):
                if file["name"] == "placeholder":
                    file_data = BLANK_PNG
                else:
                    file_data = await get_whatsapp_media(file["name"])
                result = await session.put(
                    file_url,
                    data=file_data,
                    headers={"Content-Type": file["type"]},
                )
                result.raise_for_status()

        await finalise_real411_form(self.form_reference)
        return await self.go_to_state("state_success")

    async def state_success(self):
        text = self._(
            "*REPORT* 📵 Powered by ```Real411.org```\n"
            f"_Complaint ID: {self.form_reference}_\n"
            "\n"
            "Thank you for helping to stop the spread of inaccurate or misleading "
            "information!\n"
            "\n"
            "Look out for messages from us in the next few days\n"
            "\n"
            f"To track the status of your report, visit {self.backlink}\n"
            "\n"
            "Reply 0 to return to the main MENU"
        )
        return EndState(self, text=text)

    async def state_do_not_share(self):
        return EndState(
            self,
            text=self._(
                "*REPORT* 📵 powered by ```Real411.org```\n"
                "\n"
                "Your report will not be shared.\n"
                "\n"
                "If you have seen or heard anything on other platforms, including "
                "social media, websites or even TV or radio, you can also report them "
                "at www.real411.org/complaints-create.\n"
                "\n"
                "Reply *REPORT *to start over\n"
                "Reply *0 *to return to the main *MENU*"
            ),
        )

    async def state_error(self):
        return EndState(
            self,
            text=self._(
                "Something went wrong. Please try again later. Reply *0* to go back to "
                "the main *MENU*, or *REPORT* to try again."
            ),
        )
