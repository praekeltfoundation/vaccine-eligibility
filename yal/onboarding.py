from datetime import date

from dateutil.relativedelta import relativedelta

from vaccine.states import (
    Choice,
    ChoiceState,
    EndState,
    FreeText,
    WhatsAppButtonState,
    WhatsAppListState,
)
from vaccine.utils import get_today
from vaccine.validators import nonempty_validator
from yal.mainmenu import Application as MainMenuApplication
from yal.utils import get_bot_age
from yal.validators import day_validator
from yal.yal_base_application import YalBaseApplication


class Application(YalBaseApplication):
    START_STATE = "state_dob_month"

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
        return FreeText(
            self,
            question=question,
            next="state_dob_year",
            check=day_validator(question),
            buttons=[Choice("skip", self._("Skip"))],
        )

    async def state_dob_year(self):
        return FreeText(
            self,
            question=self._(
                "\n".join(
                    [
                        "GET STARTED",
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
            next="state_end",
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
                            f"*Yoh! {age_msg}HAPPY BIRTHDAY! *🎂 🎉 ",
                            "",
                            "Hope you're having a great one so far! Remember—age is "
                            "just a number. Here's to always having  wisdom that goes"
                            " beyond your years 😉 🥂",
                        ]
                    )
                )
                await self.worker.publish_message(self.inbound.reply(msg))

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
            choices=[
                Choice("1", self._("Yes")),
                Choice("2", self._("It's complicated")),
                Choice("3", self._("No")),
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
                            f"As for me, it's been {get_bot_age()} days and I'm "
                            "still waiting to meet that special some-bot 🤖.",
                            "Not that I'm counting...",
                        ]
                    )
                )
            )
        )
        return await self.go_to_state("state_location")

    async def state_location(self):
        # TODO: Need to confirm in miro first
        return await self.go_to_state("state_gender")

    async def state_gender(self):
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
            choices=[
                Choice("1", "Girl/Woman"),
                Choice("2", "Cisgender"),
                Choice("3", "Boy?Man"),
                Choice("4", "Genderfluid"),
                Choice("5", "Intersex"),
                Choice("6", "Non-binary"),
                Choice("7", "Questioning"),
                Choice("8", "Transgender"),
                Choice("9", "Something else"),
                Choice("10", "Skip"),
            ],
            next="TODO func?",
            error=self._("TODO"),
        )

    async def state_name_gender_confirm(self):
        question = self._(
            "\n".join(
                [
                    "GET STARTED",
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

    def state_name_gender(self):
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
        # TODO: save fields on turn contact profile
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
                "change": "state_change_pref",
            },
        )

    async def state_change_pref(self):
        return EndState(
            self,
            self._("TODO: Change Pref"),
            next=self.START_STATE,
        )
