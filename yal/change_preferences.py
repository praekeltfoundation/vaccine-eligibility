import asyncio
import logging

from vaccine.base_application import BaseApplication
from vaccine.states import Choice, FreeText, WhatsAppButtonState, WhatsAppListState
from vaccine.utils import get_display_choices
from yal import rapidpro
from yal.utils import GENDERS, PROVINCES, get_generic_error, normalise_phonenumber
from yal.validators import age_validator

logger = logging.getLogger(__name__)


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

        province = fields.get("province")
        suburb = fields.get("suburb")
        street_name = fields.get("street_name")
        street_number = fields.get("street_number")

        province = dict(PROVINCES).get(province, "skip")

        location = " ".join(
            [
                s
                for s in [street_number, street_name, suburb, province]
                if s and s != "skip"
            ]
        )

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
                Choice("state_update_province", self._("Location")),
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
                        "ABOUT YOU / 🍰*Age*",
                        "-----",
                        "",
                        "*What is your age?*",
                        "_Type in the number only (e.g. 24)_",
                    ]
                )
            ),
            next="state_update_age_submit",
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

    async def state_update_age_submit(self):
        msisdn = normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.lstrip(" + ")

        data = {
            "age": self.user.answers.get("state_update_age"),
        }

        error = await rapidpro.update_profile(whatsapp_id, data)
        if error:
            return await self.go_to_state("state_error")

        return await self.go_to_state("state_display_preferences")

    async def state_update_relationship_status(self):
        question = self._(
            "\n".join(
                [
                    "*CHAT SETTINGS*",
                    "⚙️ Change or update your info",
                    "-----",
                    "",
                    "*And what about love? Seeing someone special right now?*",
                    "",
                    "*1*. Yes",
                    "*2*. It's complicated",
                    "*3*. No",
                    "*4*. Skip",
                ]
            )
        )
        return WhatsAppListState(
            self,
            question=question,
            button="Relationship Status",
            choices=[
                Choice("yes", self._("Yes")),
                Choice("complicated", self._("It's complicated")),
                Choice("no", self._("No")),
                Choice("skip", self._("Skip")),
            ],
            next="state_update_relationship_status_submit",
            error=self._(get_generic_error()),
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

        return await self.go_to_state("state_display_preferences")

    async def state_update_province(self):
        province_text = "\n".join(
            [f"{i+1} - {name}" for i, (code, name) in enumerate(PROVINCES)]
        )
        province_choices = [Choice(code, name) for code, name in PROVINCES]
        province_choices.append(Choice("skip", "Skip"))

        question = self._(
            "\n".join(
                [
                    "*ABOUT YOU*",
                    "📍 Province",
                    "-----",
                    "",
                    "🙍🏾‍♀️ To be able to recommend you youth-friendly clinics and FREE "
                    "services near you I'll need to know where you're staying "
                    "currently. 🙂",
                    "",
                    "*Which PROVINCE are you in?*",
                    "You can type the number or choose from the menu.",
                    "",
                    province_text,
                    "-----",
                    "👩🏾 *Rather not say?*",
                    "No stress! Just say SKIP.",
                ]
            )
        )
        return WhatsAppListState(
            self,
            question=question,
            button="Province",
            choices=province_choices,
            next="state_update_suburb",
            error=self._(get_generic_error()),
        )

    async def state_update_suburb(self):
        return FreeText(
            self,
            question=self._(
                "\n".join(
                    [
                        "*ABOUT YOU*",
                        "📍 Suburb/Town/Township/Village ",
                        "-----",
                        "",
                        "👩🏾 *OK. And which suburb, town, township or village was"
                        " that?*",
                        "Please type it for me and hit send.",
                        "-----",
                        "🙍🏾‍♀️ *Rather not say?*",
                        "No stress! Just tap *SKIP*.",
                    ]
                )
            ),
            next="state_update_street_name",
            buttons=[Choice("skip", self._("Skip"))],
        )

    async def state_update_street_name(self):
        return FreeText(
            self,
            question=self._(
                "\n".join(
                    [
                        "*ABOUT YOU*",
                        "📍 Street Name",
                        "-----",
                        "",
                        "👩🏾 *OK. And what about the street name?*",
                        "Could you type it for me and hit send?",
                        "-----",
                        "🙍🏾‍♀️ *Rather not say?*",
                        "No stress! Just tap *SKIP*.",
                    ]
                )
            ),
            next="state_update_street_number",
            buttons=[Choice("skip", self._("Skip"))],
        )

    async def state_update_street_number(self):
        return FreeText(
            self,
            question=self._(
                "\n".join(
                    [
                        "*ABOUT YOU*",
                        "📍Street Number",
                        "-----",
                        "",
                        "👩🏾  *And which number was that?*",
                        "Please type the street number for me and hit send.",
                        "-----",
                        "🙍🏾‍♀️ *Rather not say?*",
                        "No stress! Just tap *SKIP*.",
                    ]
                )
            ),
            next="state_update_location_submit",
            buttons=[Choice("skip", self._("Skip"))],
        )

    async def state_update_location_submit(self):
        msisdn = normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.lstrip(" + ")

        data = {
            "province": self.user.answers.get("state_update_province"),
            "suburb": self.user.answers.get("state_update_suburb"),
            "street_name": self.user.answers.get("state_update_street_name"),
            "street_number": self.user.answers.get("state_update_street_number"),
        }

        for field in ("province", "suburb", "street_name", "street_number"):
            if data.get(field):
                self.save_metadata(field, data[field])

        error = await rapidpro.update_profile(whatsapp_id, data)
        if error:
            return await self.go_to_state("state_error")

        return await self.go_to_state("state_display_preferences")

    async def state_update_gender(self):
        gender_text = "\n".join(
            [f"*{i+1}* - {name}" for i, (code, name) in enumerate(GENDERS.items())]
        )
        gender_choices = [Choice(code, name) for code, name in GENDERS.items()]
        gender_choices.append(Choice("skip", "Skip"))

        question = self._(
            "\n".join(
                [
                    "*CHAT SETTINGS*",
                    "Choose your gender",
                    "-----",
                    "",
                    "*What's your gender?*",
                    "",
                    "Please select the option you think best describes you:",
                    "",
                    gender_text,
                    f"*{len(gender_choices)}* - Skip",
                ]
            )
        )
        return WhatsAppListState(
            self,
            question=question,
            button="Gender",
            choices=gender_choices,
            next="state_update_gender_submit",
            error=self._(get_generic_error()),
        )

    async def state_update_gender_submit(self):
        msisdn = normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.lstrip(" + ")

        data = {"gender": self.user.answers.get("state_update_gender")}

        error = await rapidpro.update_profile(whatsapp_id, data)
        if error:
            return await self.go_to_state("state_error")

        return await self.go_to_state("state_display_preferences")

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
                    "_You can change this later by typing in *9* from the main "
                    "*MENU*._",
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
                    "-----",
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
            Choice("menu", self._("Main Menu")),
            Choice("ask_a_question", self._("Ask a question")),
        ]
        question = self._(
            "\n".join(
                [
                    "[persona_emoji] PERSONALISE YOUR B-WISE BOT / *Choose an emoji*",
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
                "ask_a_question": "state_aaq_start",
            },
        )
