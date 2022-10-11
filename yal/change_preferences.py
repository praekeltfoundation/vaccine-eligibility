import asyncio
import logging

from vaccine.base_application import BaseApplication
from vaccine.states import (
    Choice,
    ChoiceState,
    FreeText,
    WhatsAppListState,
    WhatsAppButtonState
)
from vaccine.utils import get_display_choices
from yal import rapidpro
from yal.utils import GENDERS, PROVINCES, get_generic_error, normalise_phonenumber
from yal.validators import day_validator, year_validator

logger = logging.getLogger(__name__)


class Application(BaseApplication):
    START_STATE = "state_display_preferences"

    async def state_display_preferences(self):
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

        dob_year = fields.get("dob_year") or "skip"
        dob_month = fields.get("dob_month") or "skip"
        dob_day = fields.get("dob_day") or "skip"
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

        dob = []
        if dob_day != "skip" and dob_month != "skip":
            dob.append(dob_day)
            dob.append(dob_month)
        elif dob_day != "skip":
            dob.append(dob_month)

        if dob_year != "skip":
            dob.append(dob_year)

        question = self._(
            "\n".join(
                [
                    "*CHAT SETTINGS*",
                    "⚙️ Change or update your info",
                    "-----",
                    "*👩🏾 No problem. Here's the info you've saved:*",
                    "",
                    "☑️ 🎂 *Birthday*",
                    "/".join(dob) if dob != [] else "Empty",
                    "",
                    "☑️ 💟 *In a Relationship?*",
                    relationship_status,
                    "",
                    "☑️ 📍 *Location*",
                    location or "Empty",
                    "",
                    "☑️ 🌈  *Identity*",
                    gender,
                    "",
                    "[persona_emoji] *Bot name*",
                    "B-wise [persona_name]"
                ]
            )
        )

        await self.publish_message(question)
        await asyncio.sleep(0.5)

        return await self.go_to_state("state_change_info_prompt")

    async def state_change_info_prompt(self):
        async def next_(choice: Choice):
            return choice.value

        question = self._(
            "\n".join(
                [
                    "👩🏾 *What info would you like to change?*",
                    "",
                    "1. Birthday",
                    "2. Relationship Status",
                    "3. Location",
                    "4. Identity",
                    "5. Bot name and emoji",
                    "-----",
                    "*Or reply:*",
                    "*0* - 🏠 Back to *Main MENU*",
                    "*#* - 🆘 Get *HELP*",
                ]
            )
        )

        return WhatsAppListState(
            self,
            question=question,
            choices=[
                Choice("state_update_dob_year", self._("Birthday")),
                Choice(
                    "state_update_relationship_status", self._("Relationship Status")
                ),
                Choice("state_update_province", self._("Location")),
                Choice("state_update_gender", self._("Identity")),
                Choice("state_update_bot_name", self._("Bot name and emoji")),
            ],
            next=next_,
            error=self._(get_generic_error()),
            error_footer=self._("\n" "Reply with the number that matches your choice."),
            button="Change Preferences",
        )

    async def state_update_dob_year(self):
        return FreeText(
            self,
            question=self._(
                "\n".join(
                    [
                        "*CHAT SETTINGS*",
                        "Date of birth",
                        "-----",
                        "",
                        "Which year were you born in?",
                        "",
                        "Reply with a number. (e.g. 2007)",
                        "",
                        "-----",
                        "Rather not say?",
                        "No stress! Just tap SKIP.",
                    ]
                )
            ),
            next="state_update_dob_month",
            check=year_validator(
                self._(
                    "⚠️  Please TYPE in only the YEAR you were born.\n" "Example _1980_"
                )
            ),
            buttons=[Choice("skip", self._("Skip"))],
        )

    async def state_update_dob_month(self):
        return ChoiceState(
            self,
            question=self._(
                "*CHAT SETTINGS*\n"
                "Your date of birth\n"
                "-----\n"
                "*What month where you born in?*\n"
                "Reply with a number:"
            ),
            choices=[
                Choice("1", self._("January")),
                Choice("2", self._("February")),
                Choice("3", self._("March")),
                Choice("4", self._("April")),
                Choice("5", self._("May")),
                Choice("6", self._("June")),
                Choice("7", self._("July")),
                Choice("8", self._("August")),
                Choice("9", self._("September")),
                Choice("10", self._("October")),
                Choice("11", self._("November")),
                Choice("12", self._("December")),
            ],
            footer=self._("\n" "If you'd rather not say, just tap *SKIP*."),
            next="state_update_dob_day",
            error=self._(get_generic_error()),
            error_footer=self._("\n" "Reply with the number next to the month."),
            buttons=[Choice("skip", self._("Skip"))],
        )

    async def state_update_dob_day(self):
        question = self._(
            "\n".join(
                [
                    "*CHAT SETTINGS*",
                    "Your date of birth",
                    "-----",
                    "",
                    "*Great. And which day were you born on?*",
                    "",
                    "Reply with a number. (e.g. *30* - if you were born on the 30th)",
                    "",
                    "If you'd rather not say, just tap *SKIP*.",
                ]
            )
        )

        dob_year = self.user.answers["state_update_dob_year"]
        dob_month = self.user.answers["state_update_dob_month"]

        return FreeText(
            self,
            question=question,
            next="state_update_dob_submit",
            check=day_validator(dob_year, dob_month, question),
            buttons=[Choice("skip", self._("Skip"))],
        )

    async def state_update_dob_submit(self):
        msisdn = normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.lstrip(" + ")

        data = {
            "dob_month": self.user.answers.get("state_update_dob_month"),
            "dob_day": self.user.answers.get("state_update_dob_day"),
            "dob_year": self.user.answers.get("state_update_dob_year"),
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
                    "It can be any name you like or one that reminds you of someone you trust.",
                    "",
                    "Just type and send me your new bot name.",
                    "",
                    "_If you want to do this later, just click the \"skip\" button._"
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
                    "_You can change this later by typing in *9* from the main *MENU*._",
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
                    "_If you want to do this later, just click the \"skip\" button._",
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
            return await self.go_to_state("state_change_info_prompt")

        self.save_metadata("persona_emoji", choice)

        data = {"persona_emoji": choice}
        msisdn = normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.lstrip(" + ")

        error = await rapidpro.update_profile(whatsapp_id, data)
        if error:
            return await self.go_to_state("state_error")

        choices = [
            Choice("menu", self._("Main Menu")),
            Choice(
                "ask_a_question", self._("Ask a question")
            ),
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
