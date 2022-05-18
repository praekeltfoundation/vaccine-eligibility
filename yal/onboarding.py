from vaccine.states import Choice, ChoiceState, EndState, FreeText
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

    async def state_end(self):
        return EndState(
            self,
            self._("TODO: Onboarding"),
            next=self.START_STATE,
        )
