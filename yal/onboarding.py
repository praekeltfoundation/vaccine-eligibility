import asyncio
import logging
from datetime import date

from dateutil.relativedelta import relativedelta

from vaccine.base_application import BaseApplication
from vaccine.states import (
    Choice,
    ChoiceState,
    FreeText,
    WhatsAppButtonState,
    WhatsAppListState,
)
from vaccine.utils import get_today, normalise_phonenumber
from vaccine.validators import nonempty_validator
from yal import contentrepo, turn, utils
from yal.change_preferences import Application as ChangePreferencesApplication
from yal.mainmenu import Application as MainMenuApplication
from yal.validators import day_validator, year_validator

logger = logging.getLogger(__name__)


class Application(BaseApplication):
    START_STATE = "state_dob_year"

    async def state_dob_year(self):
        return FreeText(
            self,
            question=self._(
                "\n".join(
                    [
                        "*GET STARTED*",
                        "Date of birth",
                        "-----",
                        "",
                        "Perfect. And finally, which year?",
                        "",
                        "Reply with a number. (e.g. 2007)",
                        "",
                        "-----",
                        "Rather not say?",
                        "No stress! Just tap SKIP.",
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
        return ChoiceState(
            self,
            question=self._(
                "*GETTING STARTED*\n"
                "Your date of birth\n"
                "-----\n"
                "Great! I'm just going to ask you a few quick questions\n"
                "\n"
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
            next="state_dob_day",
            error=self._("TODO"),
            error_footer=self._("\n" "Reply with the number next to the month."),
            buttons=[Choice("skip", self._("Skip"))],
        )

    async def state_dob_day(self):
        question = self._(
            "\n".join(
                [
                    "*GET STARTED*",
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
            if today.day == int(day) and today.month == int(month):
                age_msg = ""
                if year != "skip":
                    dob = date(int(year), int(month), int(day))
                    age_msg = f"{relativedelta(today, dob).years} today? "

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

        return await self.go_to_state("state_confirm_age")

    async def state_confirm_age(self):
        # TODO: Need to confirm in miro first
        return await self.go_to_state("state_relationship_status")

    async def state_relationship_status(self):
        question = self._(
            "\n".join(
                [
                    "*GET STARTED*",
                    "Your Relationship Status",
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
            next="state_relationship_status_confirm",
            error=self._("TODO"),
        )

    async def state_relationship_status_confirm(self):
        await self.worker.publish_message(
            self.inbound.reply(
                self._(
                    "\n".join(
                        [
                            "Amazing!",
                            "",
                            "✅ ~Birthday~",
                            "✅ ~Relationship Status~",
                            "◻️ *Location*",
                            "◻️ Gender",
                            "-----",
                            "",
                            f"As for me, it's been {utils.get_bot_age()} days and I'm "
                            "still waiting to meet that special some-bot 🤖.",
                            "Not that I'm counting...",
                        ]
                    )
                )
            )
        )
        await asyncio.sleep(0.5)
        return await self.go_to_state("state_province")

    async def state_province(self):
        province_text = "\n".join(
            [f"{i+1} - {name}" for i, (code, name) in enumerate(utils.PROVINCES)]
        )
        province_choices = [Choice(code, name) for code, name in utils.PROVINCES]
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
            next="state_suburb",
            error=self._("TODO"),
        )

    async def state_suburb(self):
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
        async def next_(choice: Choice):
            if choice.value == "other":
                return "state_name_gender_confirm"
            return "state_submit_onboarding"

        question = self._(
            "\n".join(
                [
                    "*GET STARTED*",
                    "Choose your gender",
                    "-----",
                    "",
                    "*Nearly there!*",
                    "",
                    "✅ ~Birthday~",
                    "✅ ~Relationship Status~",
                    "✅ ~Location~",
                    "◻️ *Gender*",
                    "-----",
                    "",
                    "*What's your gender?*",
                    " ",
                    "Please select the option you think best describes you:",
                    " ",
                    "1 - Girl/Woman",
                    "2 - Cisgender",
                    "3 - Boy?Man",
                    "4 - Genderfluid",
                    "5 - Intersex",
                    "6 - Non-binary",
                    "7 - Questioning",
                    "8 - Transgender",
                    "9 - Something else",
                    "10 - Skip",
                ]
            )
        )
        return WhatsAppListState(
            self,
            question=question,
            button="Gender",
            choices=[
                Choice("girl_woman", "Girl/Woman"),
                Choice("cisgender", "Cisgender"),
                Choice("boy_man", "Boy/Man"),
                Choice("genderfluid", "Genderfluid"),
                Choice("intersex", "Intersex"),
                Choice("non_binary", "Non-binary"),
                Choice("questioning", "Questioning"),
                Choice("transgender", "Transgender"),
                Choice("other", "Something else"),
                Choice("skip", "Skip"),
            ],
            next=next_,
            error=self._("TODO"),
        )

    async def state_name_gender_confirm(self):
        question = self._(
            "\n".join(
                [
                    "*GET STARTED*",
                    "Choose your gender",
                    "-----",
                    "",
                    "Sure. I want to make double sure you feel included.",
                    "",
                    "Would you like to name your own gender?",
                    "",
                    "1. Yes",
                    "2. No",
                ]
            )
        )
        error = self._("TODO")

        return WhatsAppButtonState(
            self,
            question=question,
            choices=[Choice("yes", "Yes"), Choice("no", "No")],
            error=error,
            next={
                "yes": "state_name_gender",
                "no": "state_submit_onboarding",
            },
        )

    async def state_name_gender(self):
        question = self._(
            "\n".join(
                [
                    "*GET STARTED*",
                    "Name your gender",
                    "-----",
                    "",
                    "No problem 😌  Go ahead and let me know what you'd prefer.",
                    "",
                    "*Type something and hit send.*",
                ]
            )
        )
        return FreeText(
            self,
            question=question,
            next="state_submit_onboarding",
            check=nonempty_validator(question),
        )

    async def state_submit_onboarding(self):
        msisdn = normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.lstrip(" + ")

        data = {
            "onboarding_completed": True,
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
        }

        error = await turn.update_profile(whatsapp_id, data)
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
        error = self._("TODO")

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
