import asyncio
import logging

from vaccine.models import Message
from vaccine.states import Choice, EndState, WhatsAppButtonState
from vaccine.utils import get_display_choices, random_id
from yal import rapidpro, utils
from yal.askaquestion import Application as AaqApplication
from yal.assessments import Application as AssessmentApplication
from yal.change_preferences import Application as ChangePreferencesApplication
from yal.content_feedback_survey import ContentFeedbackSurveyApplication
from yal.mainmenu import Application as MainMenuApplication
from yal.onboarding import Application as OnboardingApplication
from yal.optout import Application as OptOutApplication
from yal.pleasecallme import Application as PleaseCallMeApplication
from yal.pushmessages_optin import Application as PushMessageOptInApplication
from yal.quiz import Application as QuizApplication
from yal.servicefinder import Application as ServiceFinderApplication
from yal.servicefinder_feedback_survey import ServiceFinderFeedbackSurveyApplication
from yal.surveys.baseline import Application as BaselineSurveyApplication
from yal.terms_and_conditions import Application as TermsApplication
from yal.usertest_feedback import Application as FeedbackApplication
from yal.utils import (
    get_current_datetime,
    get_generic_error,
    is_integer,
    normalise_phonenumber,
    replace_persona_fields,
)
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
TRACKING_KEYWORDS_ROUND_2 = {
    "chat2bwise",
    "talk2bwise",
    "hi",
    "click2bwise",
    "want2bwise",
    "start2bwise",
    "join",
    "register2bwise",
    "connect",
    "i saw this on facebook",
}
OPTOUT_KEYWORDS = {"stop", "opt out", "cancel", "quit"}
ONBOARDING_REMINDER_KEYWORDS = {
    "continue",
    "remind me later",
    "not interested",
}
ASSESSMENT_REENGAGEMENT_KEYWORDS = {
    "continue now",
    "let s do it",
    "ask away",
    "start the questions",
    "remind me in 1 hour",
    "not interested",
    "skip",
    "remind me tomorrow",
}
SURVEY_KEYWORDS = {"baseline"}
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
    PushMessageOptInApplication,
    ServiceFinderApplication,
    OptOutApplication,
    AaqApplication,
    FeedbackApplication,
    ContentFeedbackSurveyApplication,
    WaFbCrossoverFeedbackApplication,
    ServiceFinderFeedbackSurveyApplication,
    AssessmentApplication,
    BaselineSurveyApplication,
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
        if (
            keyword in EMERGENCY_KEYWORDS
            and message.transport_metadata.get("message", {}).get("type")
            != "interactive"
        ):
            # Go straight to please call me application start, phrase matches exactly
            self.user.session_id = None
            self.state_name = PleaseCallMeApplication.START_STATE
        elif (
            utils.check_keyword(keyword, EMERGENCY_KEYWORDS)
            and message.transport_metadata.get("message", {}).get("type")
            != "interactive"
        ):
            self.save_metadata("emergency_keyword_previous_state", self.state_name)
            # If keyword fuzzy matches an emergency keyword,
            # First confirm redirect with user
            self.user.session_id = None
            self.state_name = PleaseCallMeApplication.CONFIRM_REDIRECT

        if (
            keyword in GREETING_KEYWORDS
            or keyword in TRACKING_KEYWORDS
            or keyword in TRACKING_KEYWORDS_ROUND_2
        ):
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

        if keyword in ASSESSMENT_REENGAGEMENT_KEYWORDS:
            if self.user.metadata.get("assessment_reminder_sent"):
                self.user.session_id = None
                self.state_name = AssessmentApplication.REMINDER_STATE

        if keyword in SURVEY_KEYWORDS:
            self.user.session_id = None
            self.state_name = "state_invitation"

        # Fields that RapidPro sets after a feedback push message
        feedback_state = await self.get_feedback_state()
        if feedback_state:
            if not self.user.session_id:
                self.user.session_id = random_id()
            message.session_event = Message.SESSION_EVENT.RESUME
            self.state_name = feedback_state

        # Replies to template push messages
        payload = utils.get_by_path(
            message.transport_metadata, "message", "button", "payload"
        )
        if payload:
            if payload.startswith("state_") and payload in dir(self):
                self.user.session_id = None
                self.state_name = payload
            elif payload.startswith("page_id_") and is_integer(payload.split("_")[-1]):
                self.user.session_id = None
                self.save_metadata("push_related_page_id", payload.split("_")[-1])
                self.state_name = "state_prep_push_msg_related_page"

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
        if inbound in TRACKING_KEYWORDS or inbound in TRACKING_KEYWORDS_ROUND_2:
            self.save_answer("state_source_tracking", inbound)

        if inbound in OPTOUT_KEYWORDS:
            return await self.go_to_state(OptOutApplication.START_STATE)
        if (
            inbound in GREETING_KEYWORDS
            or inbound in TRACKING_KEYWORDS
            or inbound in TRACKING_KEYWORDS_ROUND_2
        ):
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

    async def state_locus_of_control_assessment(self):
        self.save_metadata("assessment_name", "locus_of_control")
        self.save_metadata(
            "assessment_end_state", "state_locus_of_control_assessment_end"
        )
        return await self.go_to_state(AssessmentApplication.START_STATE)

    async def state_locus_of_control_assessment_later(self):
        self.save_metadata("assessment_name", "locus_of_control")
        return await self.go_to_state("state_assessment_later_submit")

    async def state_sexual_health_literacy_assessment(self):
        self.save_metadata("assessment_name", "sexual_health_literacy")
        self.save_metadata(
            "assessment_end_state", "state_sexual_health_literacy_assessment_end"
        )
        return await self.go_to_state(AssessmentApplication.START_STATE)

    async def state_sexual_health_literacy_assessment_end(self):
        msg = "\n".join(
            [
                "🏁 🎉",
                "",
                "*Awesome. That's all the questions for now!*",
                "",
                "[persona_emoji] Thanks for being so patient and honest 😌.",
            ]
        )

        await self.publish_message(msg)
        await asyncio.sleep(0.5)
        score = self.user.metadata.get("assessment_score", 0)
        if score <= 25:
            # score of 0-25 high risk
            risk = "high_risk"
        else:
            # score of 26-30 low risk
            risk = "low_risk"

        msisdn = normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.lstrip(" + ")
        data = {
            "sexual_health_lit_risk": risk,
            "sexual_health_lit_score": score,
        }
        self.save_answer("state_sexual_health_lit_risk", risk)
        self.save_answer("state_sexual_health_lit_score", str(score))
        error = await rapidpro.update_profile(whatsapp_id, data, self.user.metadata)
        if error:
            return await self.go_to_state("state_error")

        return await self.go_to_state("state_sexual_health_literacy_send_risk_message")

    async def state_sexual_health_literacy_send_risk_message(self):
        questions = {
            "high_risk": [
                self._(
                    "\n".join(
                        [
                            "*You and your sexual health*",
                            "-----",
                            "",
                            "Looking at your answers, I think I know exactly "
                            "where to start. I've got some great info on "
                            "the basics of sex, love and relationships.",
                            "",
                            "By the time we're done, we'll have you feeling more "
                            "confident when it comes to all things sex and "
                            "relationships. 💪",
                        ]
                    )
                ),
            ],
            "low_risk": [
                self._(
                    "\n".join(
                        [
                            "*You and your sexual health*",
                            "-----",
                            "",
                            "Looking at your answers, it looks like you already "
                            "know quite a lot about the birds 🦉and the bees 🐝of "
                            "sex, love and relationships. Proud of you 🙏🏾",
                            "",
                            "That means we can skip the basics.",
                        ]
                    )
                ),
            ],
        }
        risk = self.user.metadata.get("sexual_health_lit_risk", "high_risk")
        for message in questions[risk]:
            await self.publish_message(message)
            await asyncio.sleep(0.5)
        return await self.go_to_state("state_generic_what_would_you_like_to_do")

    async def state_sexual_health_literacy_assessment_later(self):
        self.save_metadata("assessment_name", "sexual_health_literacy")
        return await self.go_to_state("state_assessment_later_submit")

    async def state_depression_and_anxiety_assessment(self):
        self.save_metadata("assessment_name", "depression_and_anxiety")
        self.save_metadata(
            "assessment_end_state", "state_depression_and_anxiety_assessment_end"
        )
        return await self.go_to_state(AssessmentApplication.START_STATE)

    async def state_depression_and_anxiety_assessment_end(self):
        score = self.user.metadata.get("assessment_score", 0)
        if score <= 10:
            # score of 0-10 high risk
            risk = "high_risk"
        else:
            # score of 11-20 low risk
            risk = "low_risk"

        msisdn = normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.lstrip(" + ")
        data = {
            "depression_and_anxiety_risk": risk,
            "depression_and_anxiety_score": score,
        }
        self.save_answer("state_depression_and_anxiety_risk", risk)
        self.save_answer("state_depression_and_anxiety_score", str(score))
        error = await rapidpro.update_profile(whatsapp_id, data, self.user.metadata)
        if error:
            return await self.go_to_state("state_error")
        return await self.go_to_state(
            "state_depression_and_anxiety_assessment_risk_message"
        )

    async def state_depression_and_anxiety_assessment_risk_message(self):
        questions = {
            "high_risk": [
                self._(
                    "\n".join(
                        [
                            "[persona_emoji]  Eish! Sounds like it's been a rough "
                            "couple of weeks, eh? Sorry to hear you've been down. 😔",
                            "",
                            "Let's see if we can work on changing that together, shall "
                            "we? I'll send you some more info on that soon! 📲",
                        ]
                    )
                ),
            ],
            "low_risk": [
                self._(
                    "\n".join(
                        [
                            "[persona_emoji]  Glad you've got your head in a good "
                            "place. It makes it easier to deal with the other "
                            "things life throws at you 😌",
                        ]
                    )
                ),
            ],
        }
        risk = self.user.metadata.get("depression_and_anxiety_risk", "high_risk")
        for message in questions[risk]:
            await self.publish_message(message)
            await asyncio.sleep(0.5)
        return await self.go_to_state("state_generic_what_would_you_like_to_do")

    async def state_depression_and_anxiety_assessment_later(self):
        self.save_metadata("assessment_name", "depression_and_anxiety")
        return await self.go_to_state("state_assessment_later_submit")

    async def state_connectedness_assessment(self):
        self.save_metadata("assessment_name", "connectedness")
        self.save_metadata("assessment_end_state", "state_connectedness_assessment_end")
        return await self.go_to_state(AssessmentApplication.START_STATE)

    async def state_connectedness_assessment_end(self):
        score = self.user.metadata.get("assessment_score", 0)
        if score <= 2:
            # score of 0-2 high risk
            risk = "high_risk"
        else:
            # score of 3-5 low risk
            risk = "low_risk"

        msisdn = normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.lstrip(" + ")
        data = {
            "connectedness_risk": risk,
            "connectedness_score": score,
        }
        self.save_answer("state_connectedness_risk", risk)
        self.save_answer("state_connectedness_score", str(score))
        error = await rapidpro.update_profile(whatsapp_id, data, self.user.metadata)
        if error:
            return await self.go_to_state("state_error")
        return await self.go_to_state("state_connectedness_assessment_risk_message")

    async def state_connectedness_assessment_risk_message(self):
        questions = {
            "high_risk": [
                self._(
                    "\n".join(
                        [
                            "I'm sorry to hear that 😔",
                            "",
                            "I know it can be hard when you feel like you don't have "
                            "the support you need.",
                            "",
                            "Over the next few weeks, I'll share some important "
                            "tips on how to get the help we need when we need it.",
                        ]
                    )
                ),
            ],
            "low_risk": [
                self._(
                    "\n".join(
                        [
                            "[persona_emoji] *That's awesome! So glad you have "
                            "somebody you can turn to when things get tough.*",
                            "",
                            "It's important to be able to share your feelings in an "
                            "assertive way and be listened to, whether it's by "
                            "friends, family or partners.",
                        ]
                    )
                ),
                self._(
                    "\n".join(
                        [
                            "Remember I'm also here to help however I can. "
                            "😌 Keep going! You're doing a great job so far!"
                        ]
                    )
                ),
            ],
        }
        risk = self.user.metadata.get("connectedness_risk", "high_risk")

        for message in questions[risk]:
            await self.publish_message(message)
            await asyncio.sleep(0.5)
        return await self.go_to_state("state_generic_what_would_you_like_to_do")

    async def state_connectedness_assessment_later(self):
        self.save_metadata("assessment_name", "connectedness")
        return await self.go_to_state("state_assessment_later_submit")

    async def state_gender_attitude_assessment(self):
        self.save_metadata("assessment_name", "gender_attitude")
        self.save_metadata(
            "assessment_end_state", "state_gender_attitude_assessment_end"
        )
        return await self.go_to_state(AssessmentApplication.START_STATE)

    async def state_gender_attitude_assessment_end(self):
        score = self.user.metadata.get("assessment_score", 0)
        if score <= 10:
            # score of 0-10 high risk
            risk = "high_risk"
        else:
            # score of 11-20 low risk
            risk = "low_risk"

        msisdn = normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.lstrip(" + ")
        data = {
            "gender_attitude_risk": risk,
            "gender_attitude_score": score,
        }
        self.save_answer("state_gender_attitude_risk", risk)
        self.save_answer("state_gender_attitude_score", str(score))
        error = await rapidpro.update_profile(whatsapp_id, data, self.user.metadata)
        if error:
            return await self.go_to_state("state_error")
        return await self.go_to_state("state_gender_attitude_assessment_risk_message")

    async def state_gender_attitude_assessment_risk_message(self):
        questions = {
            "high_risk": [
                self._(
                    "\n".join(
                        [
                            "[persona_emoji] Thanks for those honest answers.",
                            "",
                            "*Knowing the difference between a healthy and an "
                            "unhealthy relationship can help you understand what "
                            "it means to have a positive relationship.*",
                        ]
                    )
                ),
                self._(
                    "\n".join(
                        [
                            "Being aware of the way relationships affect you can also "
                            "help you make the best choice for you.",
                            "",
                            "I've got some solid tips on how you can do that. I'll "
                            "share them with you soon 📲",
                        ]
                    )
                ),
            ],
            "low_risk": [
                self._(
                    "\n".join(
                        [
                            "[persona_emoji] Thanks for those honest answers.",
                            "",
                            "*Knowing the difference between a healthy and an "
                            "unhealthy relationship can help you understand what "
                            "it means to have a positive relationship.*",
                        ]
                    )
                ),
                self._(
                    "\n".join(
                        [
                            "From your answers, it sounds like you know the part you "
                            "play in building and keeping a healthy relationship. "
                            "That's awesome.",
                            "",
                            "*If you do have any questions though, just send me a "
                            "message saying ASK.*",
                            "",
                            "I'll do my best to get you the answers, or hook you up "
                            "with a human who knows even more.",
                        ]
                    )
                ),
            ],
        }
        risk = self.user.metadata.get("gender_attitude_risk", "high_risk")

        for message in questions[risk]:
            await self.publish_message(message)
            await asyncio.sleep(0.5)
        return await self.go_to_state("state_generic_what_would_you_like_to_do")

    async def state_gender_attitude_assessment_later(self):
        self.save_metadata("assessment_name", "gender_attitude")
        return await self.go_to_state("state_assessment_later_submit")

    async def state_body_image_assessment(self):
        self.save_metadata("assessment_name", "body_image")
        self.save_metadata("assessment_end_state", "state_body_image_assessment_end")
        return await self.go_to_state(AssessmentApplication.START_STATE)

    async def state_body_image_assessment_end(self):
        score = self.user.metadata.get("assessment_score", 0)
        if score <= 5:
            # score of 0-5 high risk
            risk = "high_risk"
        else:
            # score of 6-10 low risk
            risk = "low_risk"

        msisdn = normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.lstrip(" + ")
        data = {
            "body_image_risk": risk,
            "body_image_score": score,
        }
        self.save_answer("state_body_image_risk", risk)
        self.save_answer("state_body_image_score", str(score))
        error = await rapidpro.update_profile(whatsapp_id, data, self.user.metadata)
        if error:
            return await self.go_to_state("state_error")
        return await self.go_to_state("state_body_image_assessment_risk_message")

    async def state_body_image_assessment_risk_message(self):
        questions = {
            "high_risk": [
                self._(
                    "\n".join(
                        [
                            "[persona_emoji]  Thanks for giving your honest view.",
                            "",
                            "*It's easy to feel uncomfortable with your body. But if "
                            "you focus on what you don't like, it can affect your "
                            "self-esteem and make you feel bad about "
                            "yourself all round.*",
                        ]
                    )
                ),
                self._(
                    "\n".join(
                        [
                            "You can feel good about yourself even if your body is "
                            "not 100% perfect. (What does that even mean?!)",
                            "",
                            "I've got some great tips to share about how to get to "
                            "like your body more. I'll share them with you soon 📲",
                        ]
                    )
                ),
            ],
            "low_risk": [
                self._(
                    "\n".join(
                        [
                            "[persona_emoji]  Thanks for giving your honest view.",
                            "",
                            "*I'm so happy you feel comfortable with your body! "
                            "Focusing on what you like about yourself can help boost "
                            "your self-esteem and make you feel a lot better about "
                            "yourself all round!*",
                        ]
                    )
                ),
                self._(
                    "\n".join(
                        [
                            "From your answers, it sounds like you've already started ",
                            "that journey of getting to know, love and appreciate your "
                            "body, which is awesome!"
                            "",
                            "*If you do have any questions though, just send me a "
                            "message saying ASK.*",
                            "",
                            "I'll do my best to get you the answers, or hook you up "
                            "with a human who knows even more.",
                        ]
                    )
                ),
            ],
        }
        risk = self.user.metadata.get("body_image_risk", "high_risk")

        await self.publish_message(questions[risk][0])
        await asyncio.sleep(0.5)
        await self.publish_message(questions[risk][1])
        await asyncio.sleep(0.5)
        return await self.go_to_state("state_generic_what_would_you_like_to_do")

    async def state_body_image_assessment_later(self):
        self.save_metadata("assessment_name", "body_image")
        return await self.go_to_state("state_assessment_later_submit")

    async def state_self_perceived_healthcare_assessment(self):
        self.save_metadata("assessment_name", "self_perceived_healthcare")
        self.save_metadata(
            "assessment_end_state", "state_self_perceived_healthcare_assessment_end"
        )
        return await self.go_to_state(AssessmentApplication.START_STATE)

    async def state_self_perceived_healthcare_assessment_end(self):
        score = self.user.metadata.get("assessment_score", 0)
        if score <= 5:
            # score of 0-5 high risk
            risk = "high_risk"
        else:
            # score of 6-10 low risk
            risk = "low_risk"

        msisdn = normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.lstrip(" + ")
        data = {
            "self_perceived_healthcare_risk": risk,
            "self_perceived_healthcare_score": score,
        }
        self.save_answer("state_self_perceived_healthcare_risk", risk)
        self.save_answer("state_self_perceived_healthcare_score", str(score))
        error = await rapidpro.update_profile(whatsapp_id, data, self.user.metadata)
        if error:
            return await self.go_to_state("state_error")
        return await self.go_to_state(
            "state_self_perceived_healthcare_assessment_risk_message"
        )

    async def state_self_perceived_healthcare_assessment_risk_message(self):
        msg = self._(
            "\n".join(
                [
                    "[persona_emoji]  *Fantastic! That's it.*",
                    "",
                    "I'll chat with you again tomorrow.",
                ]
            )
        )
        await self.publish_message(msg)
        await asyncio.sleep(0.5)
        return await self.go_to_state("state_generic_what_would_you_like_to_do")

    async def state_self_perceived_healthcare_assessment_later(self):
        self.save_metadata("assessment_name", "self_perceived_healthcare")
        return await self.go_to_state("state_assessment_later_submit")

    async def state_generic_what_would_you_like_to_do(self):
        choices = [
            Choice("menu", "Go to the menu"),
            Choice("aaq", "Ask a question"),
            Choice("settings", "Update settings"),
        ]
        question = self._(
            "\n".join(
                ["*What would you like to do now?*", get_display_choices(choices)]
            )
        )

        return WhatsAppButtonState(
            self,
            question=question,
            choices=choices,
            error=self._(get_generic_error()),
            next={
                "menu": "state_pre_mainmenu",
                "aaq": AaqApplication.START_STATE,
                "settings": ChangePreferencesApplication.START_STATE,
            },
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
