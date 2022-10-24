import logging

from vaccine.states import EndState
from yal import rapidpro, utils
from yal.askaquestion import Application as AaqApplication
from yal.change_preferences import Application as ChangePreferencesApplication
from yal.content_feedback_survey import ContentFeedbackSurveyApplication
from yal.mainmenu import Application as MainMenuApplication
from yal.onboarding import Application as OnboardingApplication
from yal.optout import Application as OptOutApplication
from yal.pleasecallme import Application as PleaseCallMeApplication
from yal.quiz import Application as QuizApplication
from yal.servicefinder import Application as ServiceFinderApplication
from yal.servicefinder_feedback_survey import ServiceFinderFeedbackSurveyApplication
from yal.terms_and_conditions import Application as TermsApplication
from yal.usertest_feedback import Application as FeedbackApplication
from yal.utils import replace_persona_fields
from yal.wa_fb_crossover_feedback import Application as WaFbCrossoverFeedbackApplication

logger = logging.getLogger(__name__)

GREETING_KEYWORDS = {"hi", "hello", "menu", "0", "main menu"}
HELP_KEYWORDS = {"#", "help", "please call me", "talk to a counsellor"}
OPTOUT_KEYWORDS = {"stop"}
ONBOARDING_REMINDER_KEYWORDS = {
    "continue",
    "remind me later",
    "not interested",
}
CALLBACK_CHECK_KEYWORDS = {"callback"}
FEEDBACK_KEYWORDS = {"feedback"}
CONTENT_FEEDBACK_KEYWORDS = {
    "1",
    "2",
    "3",
    "yes",
    "not really",
    "yes thanks",
    "yes i did",
    "no i didn t",
    "no not helpful",
    "i knew this before",
    "yes i went",
    "no i didn t go",
    "no",
    "yes ask again",
    "no i m good",
    "nope",
    "no go back to list"
}


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
    FeedbackApplication,
    ContentFeedbackSurveyApplication,
    WaFbCrossoverFeedbackApplication,
    ServiceFinderFeedbackSurveyApplication,
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

        if keyword in FEEDBACK_KEYWORDS:
            self.user.session_id = None
            self.state_name = FeedbackApplication.START_STATE

        if keyword in CALLBACK_CHECK_KEYWORDS:
            self.user.session_id = None
            self.state_name = PleaseCallMeApplication.CALLBACK_RESPONSE_STATE

        if keyword in ONBOARDING_REMINDER_KEYWORDS:
            msisdn = utils.normalise_phonenumber(message.from_addr)
            whatsapp_id = msisdn.lstrip(" + ")
            error, fields = await rapidpro.get_profile(whatsapp_id)
            if error:
                return await self.go_to_state("state_error")

            onboarding_reminder_sent = fields.get("onboarding_reminder_sent")
            if onboarding_reminder_sent:
                self.user.session_id = None
                self.state_name = OnboardingApplication.REMINDER_STATE

        if keyword in CONTENT_FEEDBACK_KEYWORDS:
            msisdn = utils.normalise_phonenumber(message.from_addr)
            whatsapp_id = msisdn.lstrip(" + ")
            error, fields = await rapidpro.get_profile(whatsapp_id)
            if error:
                return await self.go_to_state("state_error")
            feedback_survey_sent = fields.get("feedback_survey_sent")
            feedback_type = fields.get("feedback_type")
            if feedback_survey_sent and feedback_type == "content":
                self.state_name = ContentFeedbackSurveyApplication.START_STATE
            if feedback_survey_sent and feedback_type == "facebook_banner":
                self.state_name = WaFbCrossoverFeedbackApplication.START_STATE
            if feedback_survey_sent and feedback_type == "servicefinder":
                self.state_name = ServiceFinderFeedbackSurveyApplication.START_STATE
            if feedback_survey_sent and (
                feedback_type == "ask_a_question" or feedback_type == "ask_a_question_2"
            ):
                self.state_name = AaqApplication.TIMEOUT_RESPONSE_STATE

            feedback_survey_sent_2 = fields.get("feedback_survey_sent_2")
            feedback_type_2 = fields.get("feedback_type_2")
            if feedback_survey_sent_2 and feedback_type_2 == "servicefinder":
                self.state_name = (
                    ServiceFinderFeedbackSurveyApplication.CALLBACK_2_STATE
                )

        return await super().process_message(message)

    async def state_start(self):
        msisdn = utils.normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.lstrip(" + ")

        error, fields = await rapidpro.get_profile(whatsapp_id)
        if error:
            return await self.go_to_state("state_error")

        terms_accepted = fields.get("terms_accepted")
        onboarding_completed = fields.get("onboarding_completed")

        # Cache some profile info
        for field in ("latitude", "longitude", "location_description"):
            if fields.get(field):
                self.save_metadata(field, fields[field])
        for field in utils.PERSONA_FIELDS:
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

        return await self.go_to_state("state_catch_all")

    async def state_catch_all(self):
        return EndState(
            self,
            self._(
                "\n".join(
                    [
                        "[persona_emoji] *Hey there — Welcome to B-Wise!*",
                        "",
                        "If you're looking for answers to questions about bodies, sex, "
                        "relationships and health, please reply with the word *HI*.",
                    ]
                )
            ),
            next=self.START_STATE,
        )

    def send_message(self, content, continue_session=True, **kw):
        """
        Replaces any persona placeholders in content before sending
        """
        content = replace_persona_fields(content, self.user.metadata)
        return super().send_message(content, continue_session, **kw)

    async def publish_message(self, question):
        """
        Replaces any persona placeholders in content before sending
        """
        content = replace_persona_fields(question, self.user.metadata)
        await self.worker.publish_message(self.inbound.reply(content))
