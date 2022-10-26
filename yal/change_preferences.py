import asyncio
import logging
import secrets
from urllib.parse import quote_plus, urljoin

import aiohttp

from vaccine.base_application import BaseApplication
from vaccine.states import (
    Choice,
    ErrorMessage,
    FreeText,
    WhatsAppButtonState,
    WhatsAppListState,
)
from vaccine.utils import HTTP_EXCEPTIONS, get_display_choices
from yal import config, rapidpro
from yal.utils import GENDERS, get_generic_error, normalise_phonenumber
from yal.validators import age_validator

logger = logging.getLogger(__name__)


def get_google_api():
    return aiohttp.ClientSession(
        timeout=aiohttp.ClientTimeout(total=5),
        headers={"Content-Type": "application/json", "User-Agent": "healthcheck-ussd"},
    )


class Application(BaseApplication):
    START_STATE = "state_display_preferences"

    async def state_display_preferences(self):
        async def next_(choice: Choice):
            return choice.value

        msisdn = normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.lstrip(" + ")

        error, fields = await rapidpro.get_profile(whatsapp_id)
        if error:
            return await self.go_to_state("state_error")

        def get_field(name):
            value = fields.get(name) or "skip"
            if value == "skip":
                return "Empty"

            if name == "gender":
                return GENDERS[value]

            return value

        age = fields.get("age") or "skip"
        relationship_status = get_field("relationship_status").title()
        gender = get_field("gender")

        location = fields.get("location_description")

        question = self._(
            "\n".join(
                [
                    "⚙️CHAT SETTINGS / *Update your info*",
                    "-----",
                    "Here's the info you've saved. *What info would you like to "
                    "change?*",
                    "",
                    "🍰 *Age*",
                    age or "Empty",
                    "",
                    "🌈Gender",
                    gender,
                    "",
                    "🤖*Bot Name+emoji*",
                    "[persona_emoji] [persona_name]",
                    "",
                    "❤️ *Relationship?*",
                    relationship_status or "Empty",
                    "",
                    "📍*Location*",
                    location or "Empty",
                    "",
                    "*-----*",
                    "*Or reply:*",
                    "*0 -* 🏠 Back to Main *MENU*",
                    "*# -* 🆘 Get *HELP*",
                ]
            )
        )

        return WhatsAppListState(
            self,
            question=question,
            choices=[
                Choice("state_update_age", self._("Age")),
                Choice("state_update_gender", self._("Gender")),
                Choice("state_update_bot_name", self._("Bot name + emoji")),
                Choice("state_update_relationship_status", self._("Relationship?")),
                Choice("state_update_location", self._("Location")),
            ],
            next=next_,
            error=self._(get_generic_error()),
            error_footer=self._("\n" "Reply with the number that matches your choice."),
            button="Change Preferences",
        )

    async def state_update_age(self):
        return FreeText(
            self,
            question=self._(
                "\n".join(
                    [
                        "*CHAT SETTINGS / ⚙️ Change or update your info* / *Age*",
                        "-----",
                        "",
                        "*What is your age?*",
                        "_Type in the number only (e.g. 24)_",
                        "",
                        "*-----*",
                        "Rather not say?",
                        "No stress! Just tap SKIP",
                    ]
                )
            ),
            next="state_update_age_confirm",
            check=age_validator(
                self._(
                    "\n".join(
                        [
                            "Hmm, something looks a bit off to me. Can we try again? "
                            "Remember to *only use numbers*. 👍🏽",
                            "",
                            "For example just send in *17* if you are 17 years old.",
                        ]
                    )
                )
            ),
            buttons=[Choice("skip", self._("Skip"))],
        )

    async def state_update_age_confirm(self):
        age = self.user.answers.get("state_update_age")
        if age == "skip":
            return await self.go_to_state("state_display_preferences")

        choices = [
            Choice("yes", self._("Yes")),
            Choice("no", self._("No")),
        ]
        question = self._(
            "\n".join(
                [
                    "*CHAT SETTINGS / ⚙️ Change or update your info* / *Age*",
                    "-----",
                    "",
                    f"*You've entered {age} as your age.*",
                    "",
                    "Is this correct?",
                    "",
                    get_display_choices(choices),
                ]
            )
        )
        return WhatsAppButtonState(
            self,
            question=question,
            choices=choices,
            error=self._(get_generic_error()),
            next={
                "yes": "state_update_age_submit",
                "no": "state_update_age",
            },
        )

    async def state_update_age_submit(self):
        if self.user.answers.get("state_update_age") == "skip":
            return await self.go_to_state("state_display_preferences")

        msisdn = normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.lstrip(" + ")

        data = {
            "age": self.user.answers.get("state_update_age"),
        }

        error = await rapidpro.update_profile(whatsapp_id, data)
        if error:
            return await self.go_to_state("state_error")
        return await self.go_to_state("state_conclude_changes")

    async def state_conclude_changes(self):
        choices = [
            Choice("menu", self._("Go to the menu")),
            Choice("state_aaq_start", self._("Ask a question")),
        ]
        question = self._(
            "\n".join(
                [
                    "CHAT SETTINGS / ⚙️ *Change or update your info*",
                    "*-----*",
                    "",
                    "Wonderful! [persona_emoji]",
                    "",
                    "*What would you like to do now?*",
                    "",
                    get_display_choices(choices),
                ]
            )
        )
        return WhatsAppButtonState(
            self,
            question=question,
            choices=choices,
            error=self._(get_generic_error()),
            next={
                "menu": "state_pre_mainmenu",
                "state_aaq_start": "state_aaq_start",
            },
        )

    async def state_update_relationship_status(self):
        choices = [
            Choice("yes", self._("Yes, in relationship")),
            Choice("complicated", self._("It's complicated")),
            Choice("no", self._("Not seeing anyone")),
            Choice("skip", self._("Skip")),
        ]
        question = self._(
            "\n".join(
                [
                    "*CHAT SETTINGS / ⚙️ Change or update your info* / *Relationship?*",
                    "-----",
                    "",
                    "[persona_emoji] *Are you currently in a relationship or seeing "
                    "someone special right now?",
                    "",
                    get_display_choices(choices),
                ]
            )
        )
        return WhatsAppListState(
            self,
            question=question,
            button="Relationship Status",
            choices=choices,
            next="state_update_relationship_status_confirm",
            error=self._(get_generic_error()),
        )

    async def state_update_relationship_status_confirm(self):
        rel = self.user.answers.get("state_update_relationship_status")
        if rel == "skip":
            return await self.go_to_state("state_display_preferences")

        choices = [
            Choice("yes", self._("Yes")),
            Choice("no", self._("No")),
        ]
        question = self._(
            "\n".join(
                [
                    "*CHAT SETTINGS / ⚙️ Change or update your info* / *Relationship?*",
                    "-----",
                    "",
                    f"*You've entered {rel} as your relationship status.*",
                    "",
                    "Is this correct?",
                    "",
                    get_display_choices(choices),
                ]
            )
        )
        return WhatsAppButtonState(
            self,
            question=question,
            choices=choices,
            error=self._(get_generic_error()),
            next={
                "yes": "state_update_relationship_status_submit",
                "no": "state_update_relationship_status",
            },
        )

    async def state_update_relationship_status_submit(self):
        msisdn = normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.lstrip(" + ")

        status = self.user.answers.get("state_update_relationship_status")

        error = await rapidpro.update_profile(
            whatsapp_id, {"relationship_status": status}
        )
        if error:
            return await self.go_to_state("state_error")

        return await self.go_to_state("state_conclude_changes")

    async def state_update_location(self):
        async def store_location_coords(content):
            if not self.inbound:
                return
            if content and content.lower() == "skip":
                return
            loc = self.inbound.transport_metadata.get("message", {}).get("location", {})
            latitude = loc.get("latitude")
            longitude = loc.get("longitude")
            if isinstance(latitude, float) and isinstance(longitude, float):
                self.save_metadata("latitude", latitude)
                self.save_metadata("longitude", longitude)
            else:
                raise ErrorMessage(
                    "\n".join(
                        [
                            "[persona_emoji]*Hmmm, for some reason I couldn't find "
                            "that location. Let's try again.*",
                            "",
                            "*OR*",
                            "",
                            "*Send HELP to talk to to a human.*",
                        ]
                    )
                )

        question = "\n".join(
            [
                "*CHAT SETTINGS / ⚙️ Change or update your info* / *Location*",
                "-----",
                "",
                "[persona_emoji] *You can change your location by sending me a pin "
                "(📍). To do this:*",
                "",
                "1️⃣Tap the *+ _(plus)_* button or the 📎*_(paperclip)_* button "
                "below.",
                "",
                "2️⃣Next, tap *Location* then select *Send Your Current Location.*",
                "",
                "_You can also use the *search 🔎 at the top of the screen, to type "
                "in the address or area* you want to share._",
                "",
                "*-----*",
                "Rather not say?",
                "No stress! Just tap SKIP",
            ]
        )

        return FreeText(
            self,
            question=question,
            next="state_get_updated_description_from_coords",
            check=store_location_coords,
            buttons=[Choice("skip", self._("Skip"))],
        )

    async def state_get_updated_description_from_coords(self):
        if self.user.answers["state_update_location"].lower() == "skip":
            return await self.go_to_state("state_display_preferences")

        metadata = self.user.metadata
        latitude = metadata.get("latitude")
        longitude = metadata.get("longitude")

        async with get_google_api() as session:
            for i in range(3):
                try:
                    response = await session.get(
                        urljoin(
                            config.GOOGLE_PLACES_URL,
                            "/maps/api/geocode/json",
                        ),
                        params={
                            "latlng": quote_plus(f"{latitude},{longitude}"),
                            "key": config.GOOGLE_PLACES_KEY,
                            "sessiontoken": secrets.token_bytes(20).hex(),
                            "language": "en",
                        },
                    )
                    response.raise_for_status()
                    data = await response.json()

                    if data["status"] != "OK":
                        return await self.go_to_state("state_error")

                    first_result = data["results"][0]
                    self.save_metadata("place_id", first_result["place_id"])
                    self.save_metadata(
                        "location_description", first_result["formatted_address"]
                    )

                    return await self.go_to_state("state_update_location_confirm")
                except HTTP_EXCEPTIONS as e:
                    if i == 2:
                        logger.exception(e)
                        return await self.go_to_state("state_error")
                    else:
                        continue

    async def state_update_location_confirm(self):
        location = self.user.metadata.get("location_description")

        choices = [
            Choice("yes", self._("Yes")),
            Choice("no", self._("No")),
        ]
        question = self._(
            "\n".join(
                [
                    "*CHAT SETTINGS / ⚙️ Change or update your info* / *Location?*",
                    "-----",
                    "",
                    f"*You've entered {location} as your location.*",
                    "",
                    "Is this correct?",
                    "",
                    get_display_choices(choices),
                ]
            )
        )
        return WhatsAppButtonState(
            self,
            question=question,
            choices=choices,
            error=self._(get_generic_error()),
            next={
                "yes": "state_update_location_submit",
                "no": "state_update_location",
            },
        )

    async def state_update_location_submit(self):
        metadata = self.user.metadata
        latitude = metadata.get("latitude")
        longitude = metadata.get("longitude")
        location_description = metadata.get("location_description")

        msisdn = normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.lstrip(" + ")
        data = {
            "location_description": location_description,
            "latitude": latitude,
            "longitude": longitude,
        }

        await rapidpro.update_profile(whatsapp_id, data)

        return await self.go_to_state("state_conclude_changes")

    async def state_update_gender(self):
        gender_text = "\n".join(
            [f"*{i+1}* - {name}" for i, (code, name) in enumerate(GENDERS.items())]
        )
        gender_choices = [Choice(code, name) for code, name in GENDERS.items()]
        gender_text = f"{gender_text}\n*{len(gender_choices) + 1}* - Skip"
        gender_choices.append(Choice("skip", self._("Skip")))

        question = self._(
            "\n".join(
                [
                    "*CHAT SETTINGS / ⚙️ Change or update your info* / *Gender*",
                    "*-----*",
                    "",
                    "*What's your gender?*",
                    "",
                    "Please click the button and select the option you think best "
                    "describes you:",
                    "",
                    gender_text,
                ]
            )
        )
        return WhatsAppListState(
            self,
            question=question,
            button="Gender",
            choices=gender_choices,
            next="state_update_other_gender",
            error=self._(get_generic_error()),
        )

    async def state_update_other_gender(self):
        gender = self.user.answers.get("state_update_gender")
        if gender == "skip":
            return await self.go_to_state("state_display_preferences")
        if gender != "other":
            return await self.go_to_state("state_update_gender_confirm")

        return FreeText(
            self,
            question=self._(
                "\n".join(
                    [
                        "*CHAT SETTINGS / ⚙️ Change or update your info* / *Gender*",
                        "-----",
                        "",
                        "[persona_emoji] No problem. I want to make double sure you "
                        "feel included.",
                        "",
                        "*Go ahead and let me know what you'd prefer. Type something "
                        "and hit send. 😌*",
                    ]
                )
            ),
            next="state_update_gender_confirm",
        )

    async def state_update_gender_confirm(self):
        gender = self.user.answers.get("state_update_gender").lower()
        if gender == "skip" or gender == "rather not say":
            return await self.go_to_state("state_display_preferences")
        if gender == "other":
            gender = self.user.answers.get("state_update_other_gender", "")
        else:
            gender = GENDERS[gender]

        choices = [
            Choice("yes", self._("Yes")),
            Choice("no", self._("No")),
        ]
        question = self._(
            "\n".join(
                [
                    "*CHAT SETTINGS / ⚙️ Change or update your info* / *Gender*",
                    "-----",
                    "",
                    f"*You've chosen {gender} as your gender.*",
                    "",
                    "Is this correct?",
                    "",
                    get_display_choices(choices),
                ]
            )
        )
        return WhatsAppButtonState(
            self,
            question=question,
            choices=choices,
            error=self._(get_generic_error()),
            next={
                "yes": "state_update_gender_submit",
                "no": "state_update_gender",
            },
        )

    async def state_update_gender_submit(self):
        msisdn = normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.lstrip(" + ")

        data = {
            "gender": self.user.answers.get("state_update_gender"),
            "gender_other": self.user.answers.get("state_update_other_gender", ""),
        }

        error = await rapidpro.update_profile(whatsapp_id, data)
        if error:
            return await self.go_to_state("state_error")

        return await self.go_to_state("state_conclude_changes")

    async def state_update_bot_name(self):
        question = self._(
            "\n".join(
                [
                    "[persona_emoji] PERSONALISE YOUR B-WISE BOT / *Give me a name*",
                    "-----",
                    "",
                    "*What would you like to call me?*",
                    "It can be any name you like or one that reminds you of someone "
                    "you trust.",
                    "",
                    "Just type and send me your new bot name.",
                    "",
                    '_If you want to do this later, just click the "skip" button._',
                ]
            )
        )
        return FreeText(
            self,
            question=question,
            next="state_update_bot_name_submit",
            buttons=[Choice("skip", self._("Skip"))],
        )

    async def state_update_bot_name_submit(self):
        choice = self.user.answers.get("state_update_bot_name")
        if choice == "skip":
            return await self.go_to_state("state_update_bot_emoji")

        self.save_metadata("persona_name", choice)

        data = {"persona_name": choice}
        msisdn = normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.lstrip(" + ")

        error = await rapidpro.update_profile(whatsapp_id, data)
        if error:
            return await self.go_to_state("state_error")

        question = self._(
            "\n".join(
                [
                    "Great - from now on you can call me [persona_name].",
                    "",
                    "_You can change this later from the main *MENU*._",
                ]
            )
        )
        await self.publish_message(question)
        await asyncio.sleep(0.5)

        return await self.go_to_state("state_update_bot_emoji")

    async def state_update_bot_emoji(self):
        question = self._(
            "\n".join(
                [
                    "[persona_emoji] PERSONALISE YOUR B-WISE BOT / *Choose an emoji*",
                    "*-----*",
                    "",
                    "*Why not use an emoji to accompany my new name?*",
                    "Send in the new emoji you'd like to use now.",
                    "",
                    '_If you want to do this later, just click the "skip" button._',
                ]
            )
        )
        return FreeText(
            self,
            question=question,
            next="state_update_bot_emoji_submit",
            buttons=[Choice("skip", self._("Skip"))],
        )

    async def state_update_bot_emoji_submit(self):
        choice = self.user.answers.get("state_update_bot_emoji")
        if choice == "skip":
            return await self.go_to_state("state_display_preferences")

        self.save_metadata("persona_emoji", choice)

        data = {"persona_emoji": choice}
        msisdn = normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.lstrip(" + ")

        error = await rapidpro.update_profile(whatsapp_id, data)
        if error:
            return await self.go_to_state("state_error")

        choices = [
            Choice("menu", self._("Go to the menu")),
            Choice("ask_a_question", self._("Ask a question")),
        ]
        question = self._(
            "\n".join(
                [
                    "[persona_emoji] PERSONALISE YOUR B-WISE BOT / *Choose an emoji*",
                    "*-----*",
                    "",
                    "Wonderful! [persona_emoji]",
                    "",
                    "*What would you like to do now?*",
                    "",
                    get_display_choices(choices),
                ]
            )
        )
        return WhatsAppButtonState(
            self,
            question=question,
            choices=choices,
            error=self._(get_generic_error()),
            next={
                "menu": "state_pre_mainmenu",
                "ask_a_question": "state_aaq_start",
            },
        )
