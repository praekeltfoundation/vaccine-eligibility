import logging
from datetime import datetime, timedelta

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
from yal.segmentation_survey import Application as SegmentSurveyApplication
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
    "hisuga",
}
OPTOUT_KEYWORDS = {"stop"}
ONBOARDING_REMINDER_KEYWORDS = {
    "continue",
    "remind me later",
    "not interested",
}
CALLBACK_CHECK_KEYWORDS = {"callback"}
FEEDBACK_KEYWORDS = {"feedback"}
FEEDBACK_FIELDS = {
    "feedback_timestamp",
    "feedback_timestamp_2",
}
QA_RESET_FEEDBACK_TIMESTAMP_KEYWORDS = {"resetfeedbacktimestampobzvmp"}
SEGMENT_SURVEY_ACCEPT = {"hell yeah"}
SEGMENT_SURVEY_DECLINE = {"no rather not"}


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
    SegmentSurveyApplication,
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

        if keyword in SEGMENT_SURVEY_ACCEPT or keyword in SEGMENT_SURVEY_DECLINE:
            msisdn = utils.normalise_phonenumber(message.from_addr)
            whatsapp_id = msisdn.lstrip(" + ")
            error, fields = await rapidpro.get_profile(whatsapp_id)

            segment_survey_complete = str(
                fields.get("segment_survey_complete", "False")
            ).lower()
            if segment_survey_complete == "pending":
                self.user.session_id = None
                if keyword in SEGMENT_SURVEY_ACCEPT:
                    self.state_name = SegmentSurveyApplication.START_STATE
                else:
                    self.state_name = SegmentSurveyApplication.DECLINE_STATE
            elif segment_survey_complete == "true":
                self.user.session_id = None
                self.state_name = SegmentSurveyApplication.COMPLETED_STATE

        if keyword in QA_RESET_FEEDBACK_TIMESTAMP_KEYWORDS:
            self.user.session_id = None
            self.state_name = "state_qa_reset_feedback_timestamp_keywords"

        self.inbound = message
        feedback_state = await self.get_feedback_state()
        if feedback_state:
            if not self.user.session_id:
                self.user.session_id = random_id()
            self.inbound.session_event = Message.SESSION_EVENT.RESUME
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
        feedback_timestamp = self.user.metadata.get("feedback_timestamp")
        in_one_minute = get_current_datetime() + timedelta(minutes=1)
        feedback_in_time = feedback_timestamp and (
            datetime.fromisoformat(feedback_timestamp) < in_one_minute
        )
        feedback_timestamp_2 = self.user.metadata.get("feedback_timestamp_2")
        feedback_in_time_2 = feedback_timestamp_2 and (
            datetime.fromisoformat(feedback_timestamp_2) < in_one_minute
        )
        if feedback_in_time or feedback_in_time_2:
            msisdn = utils.normalise_phonenumber(self.inbound.from_addr)
            whatsapp_id = msisdn.lstrip("+")
            error, fields = await rapidpro.get_profile(whatsapp_id)
            if error:
                return "state_error"
            feedback_survey_sent = fields.get("feedback_survey_sent")
            feedback_type = fields.get("feedback_type")
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

            feedback_survey_sent_2 = fields.get("feedback_survey_sent_2")
            feedback_type_2 = fields.get("feedback_type_2")
            if feedback_survey_sent_2 and feedback_type_2 == "servicefinder":
                return ServiceFinderFeedbackSurveyApplication.CALLBACK_2_STATE

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
        for field in FEEDBACK_FIELDS:
            if fields.get(field):
                self.save_metadata(field, fields[field])

        feedback_state = await self.get_feedback_state()
        if feedback_state:
            # Treat this like a session resume
            if not self.user.session_id:
                self.user.session_id = random_id()
            self.inbound.session_event = Message.SESSION_EVENT.RESUME
            return await self.go_to_state(feedback_state)

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
