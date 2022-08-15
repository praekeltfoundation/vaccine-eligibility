from vaccine.base_application import BaseApplication
from vaccine.states import Choice, EndState, WhatsAppListState
from yal import rapidpro, utils
from yal.utils import GENERIC_ERROR


class Application(BaseApplication):
    START_STATE = "state_check_feedback"

    async def state_check_feedback(self):
        msisdn = utils.normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.lstrip(" + ")

        error, fields = await rapidpro.get_profile(whatsapp_id)
        if error:
            return await self.go_to_state("state_error")

        if fields.get("usertesting_feedback_complete") == "PENDING":
            return await self.go_to_state("state_feedback_pleasecallme")
        elif fields.get("usertesting_feedback_complete") == "TRUE":
            return await self.go_to_state("state_already_completed")
        else:
            return await self.go_to_state("state_catch_all")

    async def state_already_completed(self):
        return EndState(
            self,
            self._("Thanks, you have already completed this survey."),
            next=self.START_STATE,
        )

    async def state_feedback_pleasecallme(self):
        question = self._(
            "\n".join(
                [
                    "Now that you've gone though our service, how would your rate "
                    "your experience using the *Please Call Me feature?*",
                    "",
                    "*1* - Excellent",
                    "*2* - Good",
                    "*3* - Ok",
                    "*4* - Not so good",
                    "*5* - Really bad",
                    "",
                    "*6* - Skip",
                ]
            )
        )
        return WhatsAppListState(
            self,
            question=question,
            button="Opt Out",
            choices=[
                Choice("excellent", self._("Excellent")),
                Choice("good", self._("Good")),
                Choice("ok", self._("Ok")),
                Choice("not_so_good", self._("Not so good")),
                Choice("really_bad", self._("Really bad")),
                Choice("skip", self._("Skip")),
            ],
            next="state_feedback_servicefinder",
            error=self._(GENERIC_ERROR),
        )

    async def state_feedback_servicefinder(self):
        question = self._(
            "\n".join(
                [
                    "How would your rate your experience using the *Service Finder?*",
                    "",
                    "*1* - Excellent",
                    "*2* - Good",
                    "*3* - Ok",
                    "*4* - Not so good",
                    "*5* - Really bad",
                    "",
                    "*6* - Skip",
                ]
            )
        )
        return WhatsAppListState(
            self,
            question=question,
            button="Opt Out",
            choices=[
                Choice("excellent", self._("Excellent")),
                Choice("good", self._("Good")),
                Choice("ok", self._("Ok")),
                Choice("not_so_good", self._("Not so good")),
                Choice("really_bad", self._("Really bad")),
                Choice("skip", self._("Skip")),
            ],
            next="state_feedback_changepreferences",
            error=self._(GENERIC_ERROR),
        )

    async def state_feedback_changepreferences(self):
        question = self._(
            "\n".join(
                [
                    "How would your rate your experience using the *Settings "
                    "(updating your profile etc)?*",
                    "",
                    "*1* - Excellent",
                    "*2* - Good",
                    "*3* - Ok",
                    "*4* - Not so good",
                    "*5* - Really bad",
                    "",
                    "*6* - Skip",
                ]
            )
        )
        return WhatsAppListState(
            self,
            question=question,
            button="Opt Out",
            choices=[
                Choice("excellent", self._("Excellent")),
                Choice("good", self._("Good")),
                Choice("ok", self._("Ok")),
                Choice("not_so_good", self._("Not so good")),
                Choice("really_bad", self._("Really bad")),
                Choice("skip", self._("Skip")),
            ],
            next="state_feedback_askaquestion",
            error=self._(GENERIC_ERROR),
        )

    async def state_feedback_askaquestion(self):
        question = self._(
            "\n".join(
                [
                    "How would your rate your experience using the *Ask a Question "
                    "service?*",
                    "",
                    "*1* - Excellent",
                    "*2* - Good",
                    "*3* - Ok",
                    "*4* - Not so good",
                    "*5* - Really bad",
                    "",
                    "*6* - Skip",
                ]
            )
        )
        return WhatsAppListState(
            self,
            question=question,
            button="Opt Out",
            choices=[
                Choice("excellent", self._("Excellent")),
                Choice("good", self._("Good")),
                Choice("ok", self._("Ok")),
                Choice("not_so_good", self._("Not so good")),
                Choice("really_bad", self._("Really bad")),
                Choice("skip", self._("Skip")),
            ],
            next="state_feedback_quickreply",
            error=self._(GENERIC_ERROR),
        )

    async def state_feedback_quickreply(self):
        question = self._(
            "\n".join(
                [
                    "How easy was it to get the information you were looking for "
                    "using the *Quick Reply Button?*",
                    "",
                    "*1* - Excellent",
                    "*2* - Good",
                    "*3* - Ok",
                    "*4* - Not so good",
                    "*5* - Really bad",
                    "",
                    "*6* - Skip",
                ]
            )
        )
        return WhatsAppListState(
            self,
            question=question,
            button="Opt Out",
            choices=[
                Choice("excellent", self._("Excellent")),
                Choice("good", self._("Good")),
                Choice("ok", self._("Ok")),
                Choice("not_so_good", self._("Not so good")),
                Choice("really_bad", self._("Really bad")),
                Choice("skip", self._("Skip")),
            ],
            next="state_feedback_numberskeywords",
            error=self._(GENERIC_ERROR),
        )

    async def state_feedback_numberskeywords(self):
        question = self._(
            "\n".join(
                [
                    "How easy was it to get the information you were looking for "
                    "*the numbers and keywords?*",
                    "",
                    "*1* - Excellent",
                    "*2* - Good",
                    "*3* - Ok",
                    "*4* - Not so good",
                    "*5* - Really bad",
                    "",
                    "*6* - Skip",
                ]
            )
        )
        return WhatsAppListState(
            self,
            question=question,
            button="Opt Out",
            choices=[
                Choice("excellent", self._("Excellent")),
                Choice("good", self._("Good")),
                Choice("ok", self._("Ok")),
                Choice("not_so_good", self._("Not so good")),
                Choice("really_bad", self._("Really bad")),
                Choice("skip", self._("Skip")),
            ],
            next="state_feedback_usefulinformation",
            error=self._(GENERIC_ERROR),
        )

    async def state_feedback_usefulinformation(self):
        question = self._(
            "\n".join(
                [
                    "How useful was the information you found?:",
                    "",
                    "*1* - Extremely useful",
                    "*2* - Very useful",
                    "*3* - Quite useful",
                    "*4* - Not that useful",
                    "*5* - Completely useless",
                    "",
                    "*6* - Skip",
                ]
            )
        )
        return WhatsAppListState(
            self,
            question=question,
            button="Opt Out",
            choices=[
                Choice("extremely_useful", self._("Extremely useful")),
                Choice("very_useful", self._("Very useful")),
                Choice("quite_useful", self._("Quite useful")),
                Choice("not_that_usefull", self._("Not that useful")),
                Choice("useless", self._("Completely useless")),
                Choice("skip", self._("Skip")),
            ],
            next="state_feedback_lookforinformation",
            error=self._(GENERIC_ERROR),
        )

    async def state_feedback_lookforinformation(self):
        question = self._(
            "\n".join(
                [
                    "How likely are you to use this chatbot to look for information "
                    "in the future?",
                    "",
                    "*1* - Extremely likely",
                    "*2* - Very likely",
                    "*3* - Quite likely",
                    "*4* - Unlikely",
                    "",
                    "*5* - Skip",
                ]
            )
        )
        return WhatsAppListState(
            self,
            question=question,
            button="Opt Out",
            choices=[
                Choice("extremely_likely", self._("Extremely likely")),
                Choice("very_likely", self._("Very likely")),
                Choice("quite_likely", self._("Quite likely")),
                Choice("unlikely", self._("Unlikely")),
                Choice("skip", self._("Skip")),
            ],
            next="state_feedback_willreturn",
            error=self._(GENERIC_ERROR),
        )

    async def state_feedback_willreturn(self):
        question = self._(
            "\n".join(
                [
                    "How often do you think you might use {Young Africa Live/BWise "
                    "in the future?",
                    "",
                    "*1* - All the time",
                    "*2* - Quite a lot",
                    "*3* - Sometimes",
                    "*4* - Not much",
                    "*5* - Hardly ever",
                    "",
                    "*5* - Skip",
                ]
            )
        )
        return WhatsAppListState(
            self,
            question=question,
            button="Opt Out",
            choices=[
                Choice("all_the_time", self._("All the time")),
                Choice("a_lot", self._("Quite a lot")),
                Choice("sometimes", self._("Sometimes")),
                Choice("not_much", self._("Not much")),
                Choice("hardly_ever", self._("Hardly ever")),
                Choice("skip", self._("Skip")),
            ],
            next="state_submit_completed_feedback",
            error=self._(GENERIC_ERROR),
        )

    async def state_submit_completed_feedback(self):
        msisdn = utils.normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.lstrip(" + ")
        data = {
            "usertesting_feedback_complete": "TRUE",
        }

        error = await rapidpro.update_profile(whatsapp_id, data)
        if error:
            return await self.go_to_state("state_error")
        return await self.go_to_state("state_completed_feedback")

    async def state_completed_feedback(self):
        text = self._("Thank you for your feedback. Have a great day.")
        return EndState(self, text=text, next=self.START_STATE)
