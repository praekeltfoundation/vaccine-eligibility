import logging

from vaccine.states import EndState
from yal import turn, utils
from yal.change_preferences import Application as ChangePreferencesApplication
from yal.mainmenu import Application as MainMenuApplication
from yal.onboarding import Application as OnboardingApplication
from yal.pleasecallme import Application as PleaseCallMeApplication
from yal.quiz import Application as QuizApplication
from yal.terms_and_conditions import Application as TermsApplication

logger = logging.getLogger(__name__)

GREETING_KEYWORDS = {"hi", "hello", "menu", "0"}
HELP_KEYWORDS = {"#", "help", "please call me"}


class Application(
    TermsApplication,
    OnboardingApplication,
    MainMenuApplication,
    ChangePreferencesApplication,
    QuizApplication,
    PleaseCallMeApplication,
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

        return await super().process_message(message)

    async def state_start(self):
        msisdn = utils.normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.lstrip(" + ")

        error, fields = await turn.get_profile(whatsapp_id)
        if error:
            return await self.go_to_state("state_error")

        prototype_user = fields.get("prototype_user")
        terms_accepted = fields.get("terms_accepted")
        onboarding_completed = fields.get("onboarding_completed")

        if not prototype_user:
            return await self.go_to_state("state_coming_soon")

        inbound = utils.clean_inbound(self.inbound.content)

        if inbound in GREETING_KEYWORDS:
            if terms_accepted and onboarding_completed:
                return await self.go_to_state(MainMenuApplication.START_STATE)
            elif terms_accepted:
                return await self.go_to_state(OnboardingApplication.START_STATE)
            else:
                return await self.go_to_state(TermsApplication.START_STATE)

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
            self._("TODO: Catch all temp flow"),
            next=self.START_STATE,
        )
