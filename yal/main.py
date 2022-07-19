import logging

from vaccine.states import EndState
from yal import rapidpro, utils
from yal.askaquestion import Application as AaqApplication
from yal.change_preferences import Application as ChangePreferencesApplication
from yal.mainmenu import Application as MainMenuApplication
from yal.onboarding import Application as OnboardingApplication
from yal.optout import Application as OptOutApplication
from yal.pleasecallme import Application as PleaseCallMeApplication
from yal.quiz import Application as QuizApplication
from yal.servicefinder import Application as ServiceFinderApplication
from yal.terms_and_conditions import Application as TermsApplication

logger = logging.getLogger(__name__)

GREETING_KEYWORDS = {"hi", "hello", "menu", "0"}
HELP_KEYWORDS = {"#", "help", "please call me"}
OPTOUT_KEYWORDS = {"stop"}
ONBOARDING_REMINDER_KEYWORDS = {
    "yes",
    "no, thanks",
    "remind me later",
    "not interested",
}
CALLBACK_CHECK_KEYWORDS = {
    "yes i got a callback",
    "yes but i missed it",
    "no i m still waiting",
}
AAQ_TIMEOUT_KEYWORDS = {"yes", "no", "yes ask again", "no i m good"}


class Application(
    TermsApplication,
    OnboardingApplication,
    MainMenuApplication,
    ChangePreferencesApplication,
    QuizApplication,
    PleaseCallMeApplication,
    ServiceFinderApplication,
    OptOutApplication,
    AaqApplication,
):
    START_STATE = "state_start"

    async def process_message(self, message):
        keyword = utils.clean_inbound(message.content)
        # Restart keywords
        if keyword in GREETING_KEYWORDS:
            self.user.session_id = None
            self.state_name = self.START_STATE

        if keyword in HELP_KEYWORDS:
            self.user.session_id = None
            self.state_name = PleaseCallMeApplication.START_STATE

        if keyword in OPTOUT_KEYWORDS:
            self.user.session_id = None
            self.state_name = OptOutApplication.START_STATE
        return await super().process_message(message)

    async def state_start(self):
        msisdn = utils.normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.lstrip(" + ")

        error, fields = await rapidpro.get_profile(whatsapp_id)
        if error:
            return await self.go_to_state("state_error")

        prototype_user = fields.get("prototype_user")
        terms_accepted = fields.get("terms_accepted")
        onboarding_completed = fields.get("onboarding_completed")
        # If one of these values is True then the user might be responding
        # to a scheduled msg
        onboarding_reminder_sent = fields.get("onboarding_reminder_sent")
        callback_check_sent = fields.get("callback_check_sent")
        aaq_timeout_sent = fields.get("aaq_timeout_sent")

        if not prototype_user:
            return await self.go_to_state("state_coming_soon")

        for field in ("province", "suburb", "street_name", "street_number"):
            if fields.get(field):
                self.save_metadata(field, fields[field])

        inbound = utils.clean_inbound(self.inbound.content)

        if inbound in OPTOUT_KEYWORDS:
            return await self.go_to_state(OptOutApplication.START_STATE)
        if inbound in GREETING_KEYWORDS:
            if terms_accepted and onboarding_completed:
                return await self.go_to_state(MainMenuApplication.START_STATE)
            elif terms_accepted:
                return await self.go_to_state(OnboardingApplication.START_STATE)
            else:
                return await self.go_to_state(TermsApplication.START_STATE)

        if callback_check_sent and (inbound.lower() in CALLBACK_CHECK_KEYWORDS):
            return await self.go_to_state(
                PleaseCallMeApplication.CALLBACK_RESPONSE_STATE
            )

        if onboarding_reminder_sent and (
            inbound.lower() in ONBOARDING_REMINDER_KEYWORDS
        ):
            return await self.go_to_state(OnboardingApplication.REMINDER_STATE)

        if aaq_timeout_sent and (inbound.lower() in AAQ_TIMEOUT_KEYWORDS):
            return await self.go_to_state(AaqApplication.TIMEOUT_RESPONSE_STATE)

        return await self.go_to_state("state_catch_all")

    async def state_coming_soon(self):
        return EndState(
            self,
            self._("TODO: coming soon"),
            next=self.START_STATE,
        )

    async def state_catch_all(self):
        return EndState(
            self,
            self._(
                "\n".join(
                    [
                        "👩🏾 *Howzit! Welcome to B-Wise by Young Africa Live!*",
                        "",
                        "If you're looking for answers to questions about bodies, sex, "
                        "relationships and health, please reply with the word *HI*.",
                    ]
                )
            ),
            next=self.START_STATE,
        )
