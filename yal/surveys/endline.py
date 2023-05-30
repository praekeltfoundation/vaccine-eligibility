# import asyncio
import logging

from vaccine.base_application import BaseApplication
from vaccine.states import Choice, WhatsAppButtonState
from yal import rapidpro
from yal.askaquestion import Application as AAQApplication
from yal.assessments import Application as AssessmentApplication
from yal.change_preferences import Application as ChangePreferencesApplication
from yal.utils import get_current_datetime, get_generic_error, normalise_phonenumber

logger = logging.getLogger(__name__)


class Application(BaseApplication):
    depression_score = 0
    anxiety_score = 0
    START_STATE = "state_endline_start"

    async def set_reminder_timer(self):
        msisdn = normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.lstrip(" + ")

        assessment_name = self.user.metadata.get("assessment_name", "self_esteem_endline")
        data = {
            "assessment_reminder": get_current_datetime().isoformat(),
            "assessment_reminder_name": assessment_name,
            "assessment_reminder_type": "reengagement 30min",
        }

        return await rapidpro.update_profile(whatsapp_id, data, self.user.metadata)

    # Endline start - Use this to link to survey from other areas
    async def state_endline_start(self):
        return await self.go_to_state("state_self_esteem_assessment")

    # Self Esteem
    async def state_self_esteem_assessment_endline(self):
        self.save_metadata("assessment_name", "self_esteem_endline")
        self.save_metadata(
            "assessment_end_state", "state_self_esteem_assessment_endline_end"
        )
        await self.set_reminder_timer()
        return await self.go_to_state(AssessmentApplication.START_STATE)

    async def state_self_esteem_assessment_endline_end(self):
        score = self.user.metadata.get("assessment_score", 0)
        if score <= 14:
            # score of 0-14 high risk
            risk = "high_risk"
        else:
            # score of 15-30 low risk
            risk = "low_risk"

        msisdn = normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.lstrip(" + ")
        data = {
            "self_esteem_risk": risk,
            "self_esteem_score": score,
        }
        self.save_answer("state_self_esteem_risk", risk)
        self.save_answer("state_self_esteem_score", str(score))
        error = await rapidpro.update_profile(whatsapp_id, data, self.user.metadata)
        if error:
            return await self.go_to_state("state_error")
        self.save_metadata("assessment_name", "connectedness_endline")
        self.save_metadata(
            "assessment_end_state", "state_connectedness_assessment_endline_end"
        )
        await self.set_reminder_timer()
        return await self.go_to_state(AssessmentApplication.START_STATE)

    # Connectedness
    async def state_connectedness_assessment_endline_end(self):
        score = self.user.metadata.get("assessment_score", 0)
        if score <= 1:
            # score of 0-1 high risk
            risk = "high_risk"
        else:
            # score of 2-3 low risk
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
        self.save_metadata("assessment_name", "body_image_endline")
        self.save_metadata("assessment_end_state", "state_body_image_assessment_endline_end")

        await self.set_reminder_timer()
        return await self.go_to_state(AssessmentApplication.START_STATE)

    # Body Image
    async def state_body_image_assessment_endline_end(self):
        score = self.user.metadata.get("assessment_score", 0)
        if score <= 4:
            # score of 0-4 high risk
            risk = "high_risk"
        else:
            # score of 5-6 low risk
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
        self.save_metadata("assessment_name", "depression_endline")
        self.save_metadata("assessment_end_state", "state_depression_assessment_endline_end")

        await self.set_reminder_timer()
        return await self.go_to_state(AssessmentApplication.START_STATE)

    # Depression
    async def state_depression_assessment_endline_end(self):
        score = self.user.metadata.get("assessment_score", 0)
        self.depression_score = score
        if score >= 3:
            # score of 3-6 high risk
            risk = "high_risk"
        else:
            # score of 0-2 low risk
            risk = "low_risk"

        msisdn = normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.lstrip(" + ")
        data = {
            "depression_risk": risk,
            "depression_score": score,
        }
        self.save_answer("state_depression_risk", risk)
        self.save_answer("state_depression_score", str(score))
        error = await rapidpro.update_profile(whatsapp_id, data, self.user.metadata)
        if error:
            return await self.go_to_state("state_error")
        self.save_metadata("assessment_name", "anxiety_endline")
        self.save_metadata("assessment_end_state", "state_anxiety_assessment_endline_end")

        await self.set_reminder_timer()
        return await self.go_to_state(AssessmentApplication.START_STATE)

    # Anxiety
    async def state_anxiety_assessment_endline_end(self):
        score = self.user.metadata.get("assessment_score", 0)
        self.anxiety_score = score
        if score >= 3:
            # score of 3-6 high risk
            risk = "high_risk"
        else:
            # score of 0-2 low risk
            risk = "low_risk"

        msisdn = normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.lstrip(" + ")
        data = {
            "anxiety_risk": risk,
            "anxiety_score": score,
        }
        self.save_answer("state_anxiety_v2_risk", risk)
        self.save_answer("state_anxiety_v2_score", str(score))
        error = await rapidpro.update_profile(whatsapp_id, data, self.user.metadata)
        if error:
            return await self.go_to_state("state_error")
        return await self.go_to_state("state_depression_and_anxiety_endline_end")

    # Depression & Anxiety - This is not a question set, but rather a piece of
    # logic to work out a combined "depression_and_anxiety" score

    async def state_depression_and_anxiety_endline_end(self):
        score = int(self.anxiety_score) + int(self.depression_score)
        if score >= 6:
            # score of 6-12 high risk
            risk = "high_risk"
        else:
            # score of 6-10 low risk
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
        return await self.go_to_state("state_self_perceived_healthcare_assessment_endline")


    # Self Perceived Healthcare
    async def state_self_perceived_healthcare_assessment_endline(self):
        self.save_metadata("assessment_name", "self_perceived_healthcare_endline")
        self.save_metadata(
            "assessment_end_state", "state_self_perceived_healthcare_assessment_endline_end"
        )

        await self.set_reminder_timer()
        return await self.go_to_state(AssessmentApplication.START_STATE)

    async def state_self_perceived_healthcare_assessment_endline_end(self):
        score = self.user.metadata.get("assessment_score", 0)
        if score <= 6:
            # score of 2-6 high risk
            risk = "high_risk"
        else:
            # score of 7-10 low risk
            risk = "low_risk"

        msisdn = normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.lstrip(" + ")
        data = {
            "self_perceived_healthcare_risk": risk,
            "self_perceived_healthcare_score": score,
        }
        self.save_answer("state_self_perceived_healthcare_v2_risk", risk)
        self.save_answer("state_self_perceived_healthcare_v2_score", str(score))
        error = await rapidpro.update_profile(whatsapp_id, data, self.user.metadata)
        if error:
            return await self.go_to_state("state_error")
        self.save_metadata("assessment_name", "sexual_health_literacy_endline")
        self.save_metadata(
            "assessment_end_state", "state_sexual_health_lit_assessment_endline_end"
        )

        await self.set_reminder_timer()
        return await self.go_to_state(AssessmentApplication.START_STATE)

    # Sexual Health Literacy
    async def state_sexual_health_lit_assessment_endline_end(self):
        score = self.user.metadata.get("assessment_score", 0)
        if score <= 33:
            # score of 0-33 high risk
            risk = "high_risk"
        else:
            # score of 34-55 low risk
            risk = "low_risk"

        msisdn = normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.lstrip(" + ")
        data = {
            "sexual_health_lit_risk": risk,
            "sexual_health_lit_score": score,
        }
        self.save_answer("state_sexual_health_lit_endline_risk", risk)
        self.save_answer("state_sexual_health_lit_endline_score", str(score))
        error = await rapidpro.update_profile(whatsapp_id, data, self.user.metadata)
        if error:
            return await self.go_to_state("state_error")
        self.save_metadata("assessment_name", "gender_attitude_endline")
        self.save_metadata(
            "assessment_end_state", "state_gender_attitude_assessment_endline_end"
        )

        await self.set_reminder_timer()
        return await self.go_to_state(AssessmentApplication.START_STATE)

    # Gender Attitudes
    async def state_gender_attitude_assessment_endline_end(self):
        score = self.user.metadata.get("assessment_score", 0)
        if score <= 8:
            # score of 0-8 high risk
            risk = "high_risk"
        else:
            # score of 9-12 low risk
            risk = "low_risk"

        msisdn = normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.lstrip(" + ")
        data = {
            "gender_attitude_risk": risk,
            "gender_attitude_score": score,
        }
        self.save_answer("state_gender_attitude_endline_risk", risk)
        self.save_answer("state_gender_attitude_endline_score", str(score))
        error = await rapidpro.update_profile(whatsapp_id, data, self.user.metadata)
        if error:
            return await self.go_to_state("state_error")
        self.save_metadata("assessment_name", "sexual_consent_endline")
        self.save_metadata(
            "assessment_end_state", "state_sexual_consent_assessment_endline_end"
        )

        await self.set_reminder_timer()
        return await self.go_to_state(AssessmentApplication.START_STATE)

    # # Sexual Consent
    async def state_sexual_consent_assessment_endline_end(self):
        score = self.user.metadata.get("assessment_score", 0)
        if score <= 6:
            # score of 0-6 high risk
            risk = "high_risk"
        else:
            # score of 7-10 low risk
            risk = "low_risk"

        msisdn = normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.lstrip(" + ")
        data = {
            "sexual_consent_risk": risk,
            "sexual_consent_score": score,
        }
        self.save_answer("state_sexual_consent_endlinr_risk", risk)
        self.save_answer("state_sexual_consent_endline_score", str(score))
        error = await rapidpro.update_profile(whatsapp_id, data, self.user.metadata)
        if error:
            return await self.go_to_state("state_error")
        self.save_metadata("assessment_name", "alcohol_endline")
        self.save_metadata("assessment_end_state", "state_alcohol_assessment_endline_end")

        await self.set_reminder_timer()
        return await self.go_to_state(AssessmentApplication.START_STATE)

    # Alcohol
    async def state_alcohol_assessment_endline_end(self):
        score = self.user.metadata.get("assessment_score", 0)
        if score >= 13:
            # score of 13-20 high risk
            risk = "high_risk"
        else:
            # score of 4-12 low risk
            risk = "low_risk"

        msisdn = normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.lstrip(" + ")
        data = {
            "alcohol_risk": risk,
            "alcohol_score": score,
        }
        self.save_answer("state_alcohol_endline_risk", risk)
        self.save_answer("state_alcohol_endline_score", str(score))
        error = await rapidpro.update_profile(whatsapp_id, data, self.user.metadata)
        if error:
            return await self.go_to_state("state_error")

        return await self.go_to_state("state_submit_endline_completed")
    
    # Platform Review
    async def state_platform_review_endline(self):

        return await self.go_to_state("state_submit_endline_completed")

    # Baseline Airtime Incentive
    async def state_submit_endline_completed(self):
        msisdn = normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.lstrip(" + ")
        data = {
            "endline_survey_completed": "True",
            "ejaf_endline_airtime_incentive_sent": "False",
            "ejaf_endline_completed_on": get_current_datetime().isoformat(),
        }
        self.save_answer("endline_survey_completed", "True")

        error = await rapidpro.update_profile(whatsapp_id, data, self.user.metadata)
        if error:
            return await self.go_to_state("state_error")

        return await self.go_to_state("state_endline_end")

    async def state_endline_end(self):

        return WhatsAppButtonState(
            self,
            question=self._(
                "\n".join(
                    [
                        "*And thats a wrap!*",
                        "",
                        "Thank you for taking part in our survey 🙏🏽",
                        "",
                        "*You will get your R50 airtime within 24 hours.*",
                        "",
                        "You can engage with the B-Wise chatbot at any time "
                        "for some helpful messages or to ask any questions",
                    ]
                )
            ),
            choices=[
                Choice("menu", self._("Go to the menu")),
                Choice("aaq", self._("Ask a question")),
                Choice("update_settings", self._("Update Settings")),
            ],
            next={
                "menu": "state_pre_mainmenu",
                "aaq": AAQApplication.START_STATE,
                "update_settings": ChangePreferencesApplication.START_STATE,
            },
            error=self._(get_generic_error()),
        )
