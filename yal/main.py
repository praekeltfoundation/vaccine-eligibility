import logging

from vaccine.models import Message
from vaccine.states import EndState
from vaccine.utils import random_id
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
from yal.utils import get_current_datetime, replace_persona_fields
from yal.wa_fb_crossover_feedback import Application as WaFbCrossoverFeedbackApplication

logger = logging.getLogger(__name__)

GREETING_KEYWORDS = {"hi", "hello", "menu", "0", "main menu"}
HELP_KEYWORDS = {"#", "help", "please call me", "talk to a counsellor"}
TRACKING_KEYWORDS = {
    "hie",
    "hi",
    "hola",
    "heita",
    "bwise",
    "aweh",
    "hey",
    "hiya",
    "howzit",
    "hello",
    "start",
    "hishuga",
}
OPTOUT_KEYWORDS = {"stop"}
ONBOARDING_REMINDER_KEYWORDS = {
    "continue",
    "remind me later",
    "not interested",
}
CALLBACK_CHECK_KEYWORDS = {"callback"}
FEEDBACK_KEYWORDS = {"feedback"}
QA_RESET_FEEDBACK_TIMESTAMP_KEYWORDS = {"resetfeedbacktimestampobzvmp"}
EMERGENCY_KEYWORDS = utils.get_keywords("emergency")


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
        msisdn = utils.normalise_phonenumber(message.from_addr)
        whatsapp_id = msisdn.lstrip(" + ")
        error, fields = await rapidpro.get_profile(whatsapp_id)
        if error:
            return await self.go_to_state("state_error")
        for key, value in fields.items():
            if value:
                self.save_metadata(key, value)
            else:
                self.delete_metadata(key)

        keyword = utils.clean_inbound(message.content)
        # Restart keywords that interrupt the current flow
        if keyword in EMERGENCY_KEYWORDS:
            # Go straight to please call me application start, phrase matches exactly
            self.user.session_id = None
            self.state_name = PleaseCallMeApplication.START_STATE
        elif utils.check_keyword(keyword, EMERGENCY_KEYWORDS):
            self.save_metadata("emergency_keyword_previous_state", self.state_name)
            # If keyword fuzzy matches an emergency keyword,
            # First confirm redirect with user
            self.user.session_id = None
            self.state_name = PleaseCallMeApplication.CONFIRM_REDIRECT

        if keyword in GREETING_KEYWORDS or keyword in TRACKING_KEYWORDS:
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

        if keyword in QA_RESET_FEEDBACK_TIMESTAMP_KEYWORDS:
            self.user.session_id = None
            self.state_name = "state_qa_reset_feedback_timestamp_keywords"

        if keyword in ONBOARDING_REMINDER_KEYWORDS:
            if self.user.metadata.get("onboarding_reminder_sent"):
                self.user.session_id = None
                self.state_name = OnboardingApplication.REMINDER_STATE

        # Fields that RapidPro sets after a push message
        feedback_state = await self.get_feedback_state()
        if feedback_state:
            if not self.user.session_id:
                self.user.session_id = random_id()
            message.session_event = Message.SESSION_EVENT.RESUME
            self.state_name = feedback_state

        return await super().process_message(message)

    async def state_qa_reset_feedback_timestamp_keywords(self):
        self.save_metadata("feedback_timestamp", get_current_datetime().isoformat())
        return EndState(
            self,
            text="QA: Success! You can now modify the timestamp in RapidPro to trigger "
            "the message early",
        )

    async def get_feedback_state(self):
        """
        If the user needs to be in a feedback state, send return that state name,
        otherwise return None
        """
        feedback_survey_sent = self.user.metadata.get("feedback_survey_sent")
        feedback_type = self.user.metadata.get("feedback_type")
        if feedback_survey_sent and feedback_type == "content":
            return ContentFeedbackSurveyApplication.START_STATE
        if feedback_survey_sent and feedback_type == "facebook_banner":
            return WaFbCrossoverFeedbackApplication.START_STATE
        if feedback_survey_sent and feedback_type == "servicefinder":
            return ServiceFinderFeedbackSurveyApplication.START_STATE
        if feedback_survey_sent and (
            feedback_type == "ask_a_question" or feedback_type == "ask_a_question_2"
        ):
            return AaqApplication.TIMEOUT_RESPONSE_STATE

        feedback_survey_sent_2 = self.user.metadata.get("feedback_survey_sent_2")
        feedback_type_2 = self.user.metadata.get("feedback_type_2")
        if feedback_survey_sent_2 and feedback_type_2 == "servicefinder":
            return ServiceFinderFeedbackSurveyApplication.CALLBACK_2_STATE

    async def state_start(self):
        terms_accepted = self.user.metadata.get("terms_accepted")
        onboarding_completed = self.user.metadata.get("onboarding_completed")

        inbound = utils.clean_inbound(self.inbound.content)

        # Save keywords that are used for source tracking
        if inbound in TRACKING_KEYWORDS:
            self.save_answer("state_source_tracking", inbound)

        if inbound in OPTOUT_KEYWORDS:
            return await self.go_to_state(OptOutApplication.START_STATE)
        if inbound in GREETING_KEYWORDS or inbound in TRACKING_KEYWORDS:
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
