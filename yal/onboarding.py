import asyncio
import logging
from datetime import date, datetime

from dateutil.relativedelta import relativedelta

from vaccine.base_application import BaseApplication
from vaccine.states import (
    Choice,
    ChoiceState,
    FreeText,
    WhatsAppButtonState,
    WhatsAppListState,
)
from vaccine.utils import get_today
from vaccine.validators import nonempty_validator
from yal import contentrepo, rapidpro, utils
from yal.change_preferences import Application as ChangePreferencesApplication
from yal.mainmenu import Application as MainMenuApplication
from yal.utils import GENERIC_ERROR, get_current_datetime
from yal.validators import day_validator, year_validator

logger = logging.getLogger(__name__)


class Application(BaseApplication):
    START_STATE = "state_dob_full"
    async def update_last_onboarding_time(self):
        msisdn = utils.normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.lstrip(" + ")
        data = {
            "last_onboarding_time": get_current_datetime().isoformat(),
            "onboarding_reminder_type": "5 min"
        }

        return await rapidpro.update_profile(whatsapp_id, data)

    async def state_dob_full(self):
        await self.update_last_onboarding_time()
        return FreeText(
            self,
            question=self._(
                "\n".join(
                    [
                        "*ABOUT YOU*",
                        "🎂 Date of Birth",
                        "-----",
                        "🙍🏾‍♀️ *Great! I'm just going to ask you a few quick "
                        "questions*",
                        "",
                        "*What is your Date of birth?*",
                        "Type the numbers that match when you were born e.g. "
                        "(30/09/2007)",
                    ]
                )
            ),
            next="state_validate_full_dob",
            buttons=[Choice("skip", self._("Skip"))],
        )

    async def state_validate_full_dob(self):
        value = self.user.answers["state_dob_full"]

        if value == "skip":
            self.save_answer("state_dob_day", "skip")
            self.save_answer("state_dob_month", "skip")
            self.save_answer("state_dob_year", "skip")
            return await self.go_to_state("state_relationship_status")

        try:
            dob = datetime.strptime(value, "%d/%m/%Y")

            self.save_answer("state_dob_day", str(dob.day))
            self.save_answer("state_dob_month", str(dob.month))
            self.save_answer("state_dob_year", str(dob.year))

            return await self.go_to_state("state_check_birthday")
        except ValueError:
            msg = self._(
                "Umm...I'm sorry but I'm not sure what that means🤦🏾‍♀️ You can help "
                "me by trying again. This time, we'll break it up into year, "
                "month and day.👍🏽"
            )
            await self.worker.publish_message(self.inbound.reply(msg))
            await asyncio.sleep(0.5)
            return await self.go_to_state("state_dob_year")

    async def state_dob_year(self):
        await self.update_last_onboarding_time()
        return FreeText(
            self,
            question=self._(
                "\n".join(
                    [
                        "*ABOUT YOU*",
                        "🎂 Date of Birth",
                        "-----",
                        "🙍🏾‍♀️ *Great! I'm just going to ask you a few quick "
                        "questions*",
                        "",
                        "*Which year were you born?*",
                        "Reply with a number. (e.g.2007)",
                        "",
                        "",
                        "If you'd rather not say, just tap *SKIP*.",
                    ]
                )
            ),
            next="state_dob_month",
            check=year_validator(
                self._(
                    "⚠️  Please TYPE in only the YEAR you were born.\n" "Example _1980_"
                )
            ),
            buttons=[Choice("skip", self._("Skip"))],
        )

    async def state_dob_month(self):
        await self.update_last_onboarding_time()
        return ChoiceState(
            self,
            question=self._(
                "\n".join(
                    [
                        "*ABOUT YOU*",
                        "🎂 Date of Birth",
                        "-----",
                        "🙍🏾‍♀️ *Great!  And What month where you born in?*",
                        "",
                        "Reply with a number:",
                    ]
                )
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
            next="state_dob_day",
            error=self._(GENERIC_ERROR),
            error_footer=self._("\n" "Reply with the number next to the month."),
            buttons=[Choice("skip", self._("Skip"))],
        )

    async def state_dob_day(self):
        await self.update_last_onboarding_time()
        question = self._(
            "\n".join(
                [
                    "*ABOUT YOU*",
                    "🎂 Date of Birth",
                    "-----",
                    "",
                    "🙍🏾‍♀️ *Perfect! And finally, which day were you born on?*",
                    "",
                    "Reply with a number from 1-31",
                    "(e.g. 30 - if you were born on the 30th)",
                    "",
                    "*If you'd rather not say, just tap SKIP.*",
                ]
            )
        )

        dob_year = self.user.answers["state_dob_year"]
        dob_month = self.user.answers["state_dob_month"]

        return FreeText(
            self,
            question=question,
            next="state_check_birthday",
            check=day_validator(dob_year, dob_month, question),
            buttons=[Choice("skip", self._("Skip"))],
        )

    async def state_check_birthday(self):
        day = self.user.answers["state_dob_day"]
        month = self.user.answers["state_dob_month"]
        year = self.user.answers["state_dob_year"]

        if day != "skip" and month != "skip":
            today = get_today()
            if year != "skip":
                dob = date(int(year), int(month), int(day))
                age = relativedelta(today, dob).years
                self.save_answer("age", str(age))

            if today.day == int(day) and today.month == int(month):
                age_msg = ""
                if year != "skip":
                    age_msg = f"{age} today? "

                msg = self._(
                    "\n".join(
                        [
                            f"*Yoh! {age_msg}HAPPY BIRTHDAY!* 🎂 🎉 ",
                            "",
                            "Hope you're having a great one so far! Remember—age is "
                            "just a number. Here's to always having  wisdom that goes"
                            " beyond your years 😉 🥂",
                        ]
                    )
                )
                await self.worker.publish_message(
                    self.inbound.reply(
                        msg,
                        helper_metadata={"image": contentrepo.get_image_url("hbd.png")},
                    )
                )
                await asyncio.sleep(1.5)

        return await self.go_to_state("state_relationship_status")

    async def state_relationship_status(self):
        await self.update_last_onboarding_time()
        question = self._(
            "\n".join(
                [
                    "*Fantastic!*",
                    "✅  Birthday",
                    "◻️  *Relationship Status*",
                    "◻️  Location",
                    "◻️  Gender",
                    "",
                    "-----",
                    "*ABOUT YOU*",
                    "💟 Relationship Status",
                    "",
                    "🙍🏾‍♀️ *And what about love? Seeing someone special right now?*",
                    "",
                    "1. Yes",
                    "2. It's complicated",
                    "3. No",
                    "4. Skip",
                ]
            )
        )
        return WhatsAppListState(
            self,
            question=question,
            button="Relationship Status",
            choices=[
                Choice("yes", self._("I'm seeing someone")),
                Choice("complicated", self._("It's complicated")),
                Choice("no", self._("I'm not seeing anyone")),
                Choice("skip", self._("Skip")),
            ],
            next="state_province",
            error=self._(GENERIC_ERROR),
        )

    async def state_province(self):
        await self.update_last_onboarding_time()
        province_text = "\n".join(
            [f"{i+1} - {name}" for i, (code, name) in enumerate(utils.PROVINCES)]
        )
        province_choices = [Choice(code, name) for code, name in utils.PROVINCES]
        province_choices.append(Choice("skip", "Skip"))

        question = self._(
            "\n".join(
                [
                    "Amazing!",
                    "",
                    "✅ Birthday",
                    "✅ Relationship Status",
                    "◻️ Location",
                    "◻️ Gender",
                    "",
                    "You're half way there👍🏾",
                    "-----",
                    "ABOUT YOU",
                    "📍 Province",
                    "",
                    "To be able to suggest youth-friendly clinics and FREE services "
                    "near you, I need to know where you live.",
                    "",
                    "🙍🏾‍♀️Which PROVINCE are you in?",
                    "Type the number or choose from the list.",
                    "",
                    province_text,
                ]
            )
        )
        return WhatsAppListState(
            self,
            question=question,
            button="Province",
            choices=province_choices,
            next="state_full_address",
            error=self._(GENERIC_ERROR),
        )

    async def state_full_address(self):
        await self.update_last_onboarding_time()
        age = int(self.user.answers.get("age", -1))
        if age < 18:
            return await self.go_to_state("state_gender")

        return FreeText(
            self,
            question=self._(
                "\n".join(
                    [
                        "ABOUT YOU",
                        "📍Address ",
                        "-----",
                        "",
                        "👩🏾 OK. Lets see which facilities are close to you. What is "
                        "your address?",
                        "Type the name of your neighbourhood, your street and your "
                        "house number.",
                        "",
                        "e.g.",
                        "Mofolo South",
                        "Lekoropo street",
                        "1876",
                        "-----",
                        "🙍🏾‍♀️ Rather not say?",
                        "No stress! Just tap SKIP.",
                    ]
                )
            ),
            next="state_validate_full_address",
            buttons=[Choice("skip", self._("Skip"))],
        )

    async def state_validate_full_address(self):
        value = self.user.answers["state_full_address"]

        if value == "skip":
            return await self.go_to_state("state_gender")

        try:
            lines = value.split("\n")

            assert len(lines) == 3

            self.save_answer("state_suburb", lines[0].strip())
            self.save_answer("state_street_name", lines[1].strip())
            self.save_answer("state_street_number", lines[2].strip())

            return await self.go_to_state("state_gender")
        except (AssertionError, IndexError):
            msg = self._(
                "Umm...I'm sorry but I'm not sure what that means🤦🏾‍♀️ You can help "
                "me by trying again. This time, we'll break it up into "
                "neighbourhood, street and number.👍🏽"
            )
            await self.worker.publish_message(self.inbound.reply(msg))
            await asyncio.sleep(0.5)
            return await self.go_to_state("state_suburb")

    async def state_suburb(self):
        await self.update_last_onboarding_time()
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
            next="state_street_name",
            buttons=[Choice("skip", self._("Skip"))],
        )

    async def state_street_name(self):
        await self.update_last_onboarding_time()
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
            next="state_street_number",
            buttons=[Choice("skip", self._("Skip"))],
        )

    async def state_street_number(self):
        await self.update_last_onboarding_time()
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
            next="state_gender",
            buttons=[Choice("skip", self._("Skip"))],
        )

    async def state_gender(self):
        await self.update_last_onboarding_time()

        async def next_(choice: Choice):
            if choice.value == "other":
                return "state_name_gender"
            return "state_submit_onboarding"

        gender_text = "\n".join(
            [
                f"*{i+1}* - {name}"
                for i, (code, name) in enumerate(utils.GENDERS.items())
            ]
        )
        gender_choices = [Choice(code, name) for code, name in utils.GENDERS.items()]
        gender_choices.append(Choice("skip", "Skip"))

        question = self._(
            "\n".join(
                [
                    "*ABOUT YOU*",
                    "🌈 How you identify",
                    "-----",
                    "",
                    "*You're almost done!*🙌🏾",
                    "",
                    "✅ Birthday",
                    "✅ Relationship Status",
                    "✅ Location",
                    "◻️ Gender",
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
            next=next_,
            error=self._(GENERIC_ERROR),
        )

    async def state_name_gender(self):
        await self.update_last_onboarding_time()
        question = self._(
            "\n".join(
                [
                    "*ABOUT YOU*",
                    "🌈 Preferred Identity",
                    "-----",
                    "",
                    "🙍🏾‍♀️ Sure. I want to make double sure you feel included.",
                    "",
                    "*Go ahead and let me know what you'd prefer. Type something and "
                    "hit send. *😌",
                ]
            )
        )
        return FreeText(
            self,
            question=question,
            next="state_submit_onboarding",
            check=nonempty_validator(question),
            buttons=[Choice("skip", self._("Skip"))],
        )

    async def state_submit_onboarding(self):
        msisdn = utils.normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.lstrip(" + ")

        data = {
            "onboarding_completed": "True",
            "dob_month": self.user.answers.get("state_dob_month"),
            "dob_day": self.user.answers.get("state_dob_day"),
            "dob_year": self.user.answers.get("state_dob_year"),
            "relationship_status": self.user.answers.get("state_relationship_status"),
            "gender": self.user.answers.get("state_gender"),
            "gender_other": self.user.answers.get("state_name_gender"),
            "province": self.user.answers.get("state_province"),
            "suburb": self.user.answers.get("state_suburb"),
            "street_name": self.user.answers.get("state_street_name"),
            "street_number": self.user.answers.get("state_street_number"),
            "onboarding_reminder_type": "",
        }

        for field in ("province", "suburb", "street_name", "street_number"):
            if data.get(field):
                self.save_metadata(field, data[field])

        error = await rapidpro.update_profile(whatsapp_id, data)
        if error:
            return await self.go_to_state("state_error")

        return await self.go_to_state("state_onboarding_complete")

    async def state_onboarding_complete(self):
        question = self._(
            "\n".join(
                [
                    "*Lekker—We're good to go!*",
                    "",
                    "✅ Birthday",
                    "✅ Relationship Status",
                    "✅ Location",
                    "✅ Gender",
                    "-----",
                    "",
                    "Thanks! Next time we chat, I'll be able to give you some "
                    "personal recommendations for things to check out 😉.",
                    "",
                    "*Shall we get chatting?*",
                    "",
                    "1 - OK",
                    "2 - Change my preferences",
                ]
            )
        )
        error = self._(GENERIC_ERROR)

        return WhatsAppButtonState(
            self,
            question=question,
            choices=[Choice("ok", "OK"), Choice("change", "Change preferences")],
            error=error,
            next={
                "ok": MainMenuApplication.START_STATE,
                "change": ChangePreferencesApplication.START_STATE,
            },
        )
