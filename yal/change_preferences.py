import asyncio
import logging
import secrets
from urllib.parse import urljoin

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
from yal.utils import (
    GENDERS,
    extract_first_emoji,
    get_generic_error,
    normalise_phonenumber,
)
from yal.validators import age_validator

logging.basicConfig(level=config.LOG_LEVEL.upper())
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

        def get_field(name):
            value = self.user.metadata.get(name) or "skip"
            if value == "skip":
                return "Empty"

            if name == "gender":
                return GENDERS[value]

            return value

        age = self.user.metadata.get("age") or "skip"
        relationship_status = get_field("relationship_status").title()
        gender = get_field("gender")

        location = self.user.metadata.get("location_description")
        notifications = self.user.metadata.get("push_message_opt_in")
        if notifications == "True":
            notifications_change_state = "state_update_notifications_turn_off"
        else:
            notifications_change_state = "state_update_notifications_turn_on"

        question_list = [
            "⚙️CHAT SETTINGS / *Update your info*",
            "-----",
            "Here's the info you've saved. *What info would you like to " "change?*",
            "",
            "🍰 *Age*",
            age or "Empty",
            "",
            "🌈 *Gender*",
            gender,
            "",
            "🤖 *Bot Name+emoji*",
            "[persona_emoji] [persona_name]",
            "",
            "❤️ *Relationship?*",
            relationship_status or "Empty",
            "",
            "📍 *Location*",
            location or "Empty",
            "",
            "🔔 *Notifications*",
            "ON" if notifications == "True" else "OFF",
            "",
        ]

        choices_list = [
            Choice("state_update_age", self._("Age")),
            Choice("state_update_gender", self._("Gender")),
            Choice("state_update_bot_name", self._("Bot name + emoji")),
            Choice("state_update_relationship_status", self._("Relationship?")),
            Choice("state_update_location", self._("Location")),
            Choice(notifications_change_state, self._("Notifications")),
        ]

        ejaf_study_optin = self.user.metadata.get("ejaf_study_optin")

        if ejaf_study_optin == "True":
            question_list.extend(
                [
                    "📝 *Study Participant*",
                    "Yes",
                    "",
                ]
            )

            choices_list.append(
                Choice("state_update_study_optout", self._("Opt out of study"))
            )

        question_list.extend(
            [
                "*-----*",
                "*Or reply:*",
                "*0 -* 🏠 Back to Main *MENU*",
                "*# -* 🆘 Get *HELP*",
            ]
        )

        question = self._("\n".join(question_list))

        return WhatsAppListState(
            self,
            question=question,
            choices=choices_list,
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
        age = self.user.answers.get("state_update_age").lower()
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
        if self.user.answers.get("state_update_age").lower() == "skip":
            return await self.go_to_state("state_display_preferences")

        msisdn = normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.removeprefix("+")

        data = {
            "age": self.user.answers.get("state_update_age"),
        }

        error = await rapidpro.update_profile(whatsapp_id, data, self.user.metadata)
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
            Choice("relationship", self._("Yes, in relationship")),
            Choice("complicated", self._("It's complicated")),
            Choice("single", self._("Not seeing anyone")),
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
        whatsapp_id = msisdn.removeprefix("+")

        status = self.user.answers.get("state_update_relationship_status")

        error = await rapidpro.update_profile(
            whatsapp_id, {"relationship_status": status}, self.user.metadata
        )
        if error:
            return await self.go_to_state("state_error")

        return await self.go_to_state("state_conclude_changes")

    async def state_update_location(self):
        async def store_location_coords(content):
            logger.debug(">>> store_location_coords")
            if not self.inbound:
                logger.debug("no inbound")
                return
            if content and content.lower() == "skip":
                logger.debug("skipped")
                return
            loc = self.inbound.transport_metadata.get("message", {}).get("location", {})
            latitude = loc.get("latitude")
            longitude = loc.get("longitude")

            logger.debug(f"{latitude},{longitude}")
            if isinstance(latitude, float) and isinstance(longitude, float):
                self.save_metadata("new_latitude", latitude)
                self.save_metadata("new_longitude", longitude)
                logger.debug("location saved to metadata")
            else:
                logger.debug("location error")
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
        logger.debug(">>> state_get_updated_description_from_coords")
        if self.user.answers["state_update_location"].lower() == "skip":
            logger.debug("location skipped")
            return await self.go_to_state("state_display_preferences")

        metadata = self.user.metadata
        latitude = metadata.get("new_latitude")
        longitude = metadata.get("new_longitude")

        logger.debug(f"{latitude},{longitude}")

        async with get_google_api() as session:
            if latitude and longitude:
                for i in range(3):
                    try:
                        response = await session.get(
                            urljoin(
                                config.GOOGLE_PLACES_URL,
                                "/maps/api/geocode/json",
                            ),
                            params={
                                "latlng": f"{latitude},{longitude}",
                                "key": config.GOOGLE_PLACES_KEY,
                                "sessiontoken": secrets.token_bytes(20).hex(),
                                "language": "en",
                            },
                        )
                        response.raise_for_status()
                        data = await response.json()

                        logger.debug(data)

                        if data["status"] != "OK":
                            logger.debug("not ok")
                            return await self.go_to_state("state_error")

                        first_result = data["results"][0]
                        self.save_metadata("place_id", first_result["place_id"])
                        self.save_metadata(
                            "new_location_description",
                            first_result["formatted_address"],
                        )

                        return await self.go_to_state("state_update_location_confirm")
                    except HTTP_EXCEPTIONS as e:
                        if i == 2:
                            logger.exception(e)
                            logger.debug("http exception")
                            return await self.go_to_state("state_error")
                        else:
                            continue

    async def state_update_location_confirm(self):
        location = self.user.metadata.get("new_location_description")

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
        latitude = metadata.get("new_latitude")
        longitude = metadata.get("new_longitude")
        location_description = metadata.get("new_location_description")

        msisdn = normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.removeprefix("+")
        data = {
            "location_description": location_description,
            "latitude": latitude,
            "longitude": longitude,
        }

        await rapidpro.update_profile(whatsapp_id, data, self.user.metadata)

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
        whatsapp_id = msisdn.removeprefix("+")

        data = {
            "gender": self.user.answers.get("state_update_gender"),
        }

        error = await rapidpro.update_profile(whatsapp_id, data, self.user.metadata)
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

        data = {"persona_name": choice}
        msisdn = normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.removeprefix("+")

        error = await rapidpro.update_profile(whatsapp_id, data, self.user.metadata)
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
        data = {"persona_emoji": extract_first_emoji(choice)}
        msisdn = normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.removeprefix("+")

        error = await rapidpro.update_profile(whatsapp_id, data, self.user.metadata)
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

    async def state_update_notifications_turn_off(self):
        question = self._(
            "\n".join(
                [
                    "CHAT SETTINGS / ⚙️ Change or update your info / *Notifications*",
                    "-----",
                    "",
                    "*You are signed up* to receive alerts from [persona_emoji] "
                    "[persona_name]",
                    "",
                    'To stop receiving notifications, tap "Turn off alerts" '
                    "button below.",
                ]
            )
        )
        return WhatsAppButtonState(
            self,
            question=question,
            choices=[
                Choice("stop", "Turn off alerts"),
                Choice("back", "Go back"),
            ],
            error=self._(get_generic_error()),
            next={
                "stop": "state_update_notifications_turn_off_submit",
                "back": "state_display_preferences",
            },
        )

    async def state_update_notifications_turn_off_submit(self):
        data = {"push_message_opt_in": "False"}
        msisdn = normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.removeprefix("+")

        error = await rapidpro.update_profile(whatsapp_id, data, self.user.metadata)
        if error:
            return await self.go_to_state("state_error")

        question = self._(
            "\n".join(
                [
                    "[persona_emoji] *No problem! I won't send you daily messages.*",
                    "",
                    "Remember, you can still use the menu to get the info you need.",
                    "",
                    "You can also sign up for messages again at any time. "
                    "Just go to your profile page.",
                ]
            )
        )
        await self.publish_message(question)
        await asyncio.sleep(0.5)
        return await self.go_to_state("state_update_notifications_final")

    async def state_update_notifications_turn_on(self):
        question = self._(
            "\n".join(
                [
                    "CHAT SETTINGS / ⚙️ Change or update your info / *Notifications*",
                    "-----",
                    "",
                    "*You are not signed up* to receive alerts from [persona_emoji] "
                    "[persona_name]",
                ]
            )
        )
        return WhatsAppButtonState(
            self,
            question=question,
            choices=[
                Choice("start", "Turn on alerts"),
                Choice("back", "Go back"),
            ],
            error=self._(get_generic_error()),
            next={
                "start": "state_update_notifications_turn_on_submit",
                "back": "state_display_preferences",
            },
        )

    async def state_update_notifications_turn_on_submit(self):
        data = {"push_message_opt_in": "True"}
        msisdn = normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.removeprefix("+")

        error = await rapidpro.update_profile(whatsapp_id, data, self.user.metadata)
        if error:
            return await self.go_to_state("state_error")

        question = self._(
            "\n".join(
                [
                    "[persona_emoji] *Lekker! I've set up notifications.*",
                    "",
                    "🔔 I'll ping you once a day with info I think might be interesting "
                    "or helpful for you — and sometimes just to share something a "
                    "bit more fun.",
                    "",
                    "You can also stop these messages again at any time. Just go to "
                    'your profile page or send in the word "STOP".',
                ]
            )
        )
        await self.publish_message(question)
        await asyncio.sleep(0.5)
        return await self.go_to_state("state_update_notifications_final")

    async def state_update_notifications_final(self):
        choices = [
            Choice("menu", "Go to the menu"),
            Choice("aaq", "Ask a question"),
        ]

        question = self._(
            "\n".join(
                [
                    "CHAT SETTINGS / ⚙️ *Change or update your info*",
                    "-----",
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
                "aaq": "state_aaq_start",
            },
        )

    async def state_update_study_optout(self):
        question = self._(
            "\n".join(
                [
                    "*You are signed up to be a part of this study*",
                    "",
                    "If you no longer want to be part of the study please click"
                    " on the “Leave Study” button below.",
                    "",
                    "Please note that opting out of the study  means that you"
                    " will still receive daily notifications. You can opt out"
                    " of these in  *chat settings/notifications.*",
                ]
            )
        )
        return WhatsAppButtonState(
            self,
            question=question,
            choices=[
                Choice("leave", "Leave Study"),
                Choice("back", "Go back"),
            ],
            error=self._(get_generic_error()),
            next={
                "leave": "study_optout_confirm",
                "back": "state_display_preferences",
            },
        )

    async def study_optout_confirm(self):
        data = {"ejaf_study_optin": "False"}
        msisdn = normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.removeprefix("+")

        error = await rapidpro.update_profile(whatsapp_id, data, self.user.metadata)
        if error:
            return await self.go_to_state("state_error")

        choices = [
            Choice("menu", "Go to the menu"),
            Choice("aaq", "Ask a question"),
        ]

        question = self._(
            "\n".join(
                [
                    "[persona_emoji] *No problem! You will no longer be part"
                    " of this study.*",
                    "",
                    "Remember, you can still use the menu to get the info you need.",
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
                "aaq": "state_aaq_start",
            },
        )
