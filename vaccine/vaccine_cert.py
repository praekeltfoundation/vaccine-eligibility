import base64
import binascii
import json
import re
from urllib.parse import ParseResult, urlunparse

import aiohttp
import cv2
import numpy
import zbar

import vaccine.vaccine_cert_config as config
from vaccine.base_application import BaseApplication
from vaccine.models import Message
from vaccine.states import EndState, ErrorMessage, FreeText


class Application(BaseApplication):
    START_STATE = "state_start"

    @staticmethod
    def whatsapp_media_url(media_id: str) -> str:
        return urlunparse(
            ParseResult(
                scheme="https",
                netloc=config.API_HOST or "",
                path=f"/v1/media/{media_id}",
                params="",
                query="",
                fragment="",
            )
        )

    async def process_message(self, message: Message) -> list[Message]:
        if message.session_event == Message.SESSION_EVENT.CLOSE:
            self.state_name = "state_timeout"

        keyword = re.sub(r"\W+", " ", message.content or "").strip().lower()
        # Exit keywords
        if keyword in (
            "menu",
            "0",
        ):
            self.state_name = "state_exit"

        return await super().process_message(message)

    async def state_timeout(self):
        return EndState(
            self,
            "We haven't heard from you in while. This session is timed out due to "
            "inactivity. Send in the keyword *CERTIFICATE* to try again.",
        )

    async def state_exit(self):
        return EndState(self, "", helper_metadata={"automation_handle": True})

    async def state_start(self):
        async def get_whatsapp_media(media_id):
            client = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=5),
                headers={
                    "User-Agent": "vaccine-cert",
                    "Authorization": f"Bearer {config.API_TOKEN}",
                },
            )
            response = await client.get(self.whatsapp_media_url(media_id))
            response.raise_for_status()
            return numpy.frombuffer(await response.read(), numpy.uint8)

        def decode_qrcode_image(image):
            image = cv2.imdecode(image, cv2.IMREAD_GRAYSCALE)
            _, bw_image = cv2.threshold(image, 127, 255, cv2.THRESH_BINARY)
            return zbar.Scanner().scan(bw_image)

        def interpret_vaccine_qrcode(data):
            # Certificate is inside the JSON body under the "hcert" key
            # The certificate is base64 encoded JSON.
            try:
                cert_encoded = json.loads(data)["hcert"]
                return json.loads(base64.b64decode(cert_encoded).decode())
            except (json.JSONDecodeError, KeyError, TypeError, binascii.Error) as e:
                raise ErrorMessage(
                    "Sorry, the QR code is not a valid vaccine certificate QR code. "
                    "Please try sending a photo that contains the vaccine certificate "
                    "QR code, or reply *MENU* to quit."
                ) from e

        async def image_check(content):
            msg = self.inbound.transport_metadata.get("message", {})
            if msg.get("type") != "image":
                raise ErrorMessage(
                    "Sorry, that is not a photo. Please try sending a photo that "
                    "contains the QR code on the vaccine certificate again, or reply "
                    "*MENU* to quit."
                )
            image_id = msg["image"]["id"]
            results = decode_qrcode_image(await get_whatsapp_media(image_id))
            if len(results) == 0:
                raise ErrorMessage(
                    "Sorry, we cannot find any QR codes in that photo. Please try "
                    "again by sending another photo, or reply *MENU* to quit."
                )
            if len(results) > 1:
                raise ErrorMessage(
                    "Sorry, we found more than one QR code in that photo. Please try "
                    "again by sending another photo that contains only a single QR "
                    "code, or reply *MENU* to quit"
                )
            qrcode = results[0].data.decode()
            self.vaccine_certificate = interpret_vaccine_qrcode(qrcode)

        return FreeText(
            self,
            question="*Vaccine certificate validation*\n"
            "\n"
            "Please send a photo that contains the QR code on your vaccine certificate",
            next="state_display_details",
            check=image_check,
        )

    async def state_display_details(self):
        cert = self.vaccine_certificate
        vaccines = "\n".join(
            [
                f"{vac.get('vaccineDate')} {vac.get('vaccineReceived')} "
                f"{vac.get('proofOfVaccineCode')}"
                for vac in cert.get("immunizationEvents", [])
            ]
        )
        return EndState(
            self,
            "The scanned vaccine certificate has the following details:\n"
            f"Identification Type: {cert.get('idType')}\n"
            f"Identification Value: {cert.get('idValue')}\n"
            f"Name: {cert.get('firstName')} {cert.get('surname')}\n"
            f"Date of Birth: {cert.get('dateOfBirth')}\n"
            "\n"
            "Vaccines:\n"
            f"{vaccines}\n"
            "\n"
            "Reply *CERTIFICATE* if you want to check another vaccine certificate",
        )
