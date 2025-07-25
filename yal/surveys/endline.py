# import asyncio
import logging

from vaccine.base_application import BaseApplication
from vaccine.states import Choice, FreeText, WhatsAppButtonState
from yal import rapidpro
from yal.askaquestion import Application as AAQApplication
from yal.assessments import Application as AssessmentApplication
from yal.change_preferences import Application as ChangePreferencesApplication
from yal.utils import (
    get_current_datetime,
    get_generic_error,
    get_generic_error_options,
    normalise_phonenumber,
)

logger = logging.getLogger(__name__)


class Application(BaseApplication):
    depression_score = 0
    anxiety_score = 0
    START_STATE = "state_endline_start"
    SURVEY_VALIDATION_STATE = "state_survey_validation"

    async def set_endline_reminder_timer(self):
        msisdn = normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.removeprefix("+")

        assessment_name = self.user.metadata.get(
            "assessment_name", "locus_of_control_endline"
        )
        data = {
            "assessment_reminder": get_current_datetime().isoformat(),
            "assessment_reminder_name": assessment_name,
            "assessment_reminder_type": "endline reengagement 30min",
        }

        return await rapidpro.update_profile(whatsapp_id, data, self.user.metadata)

    # Endline start - Use this to link to survey from other areas
    async def state_endline_start(self):
        return await self.go_to_state("state_locus_of_control_assessment_endline")

    # Locus of Control
    async def state_locus_of_control_assessment_endline(self):
        self.save_metadata("assessment_name", "locus_of_control_endline")
        self.save_metadata(
            "assessment_end_state", "state_locus_of_control_assessment_endline_end"
        )
        await self.set_endline_reminder_timer()
        return await self.go_to_state(AssessmentApplication.START_STATE)

    async def state_locus_of_control_assessment_endline_end(self):
        score = self.user.metadata.get("assessment_score", 0)
        # score of 0-14 high risk
        # score of 15-30 low risk
        risk = "high_risk" if score <= 12 else "low_risk"

        msisdn = normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.removeprefix("+")
        data = {
            "locus_of_control_risk": risk,
            "locus_of_control_score": score,
        }
        self.save_answer("state_locus_of_control_endline_risk", risk)
        self.save_answer("state_locus_of_control_endline_score", str(score))
        error = await rapidpro.update_profile(whatsapp_id, data, self.user.metadata)
        if error:
            return await self.go_to_state("state_error")

        await self.set_endline_reminder_timer()
        return await self.go_to_state("state_self_esteem_assessment_endline")

    # Self Esteem
    async def state_self_esteem_assessment_endline(self):
        self.save_metadata("assessment_name", "self_esteem_endline")
        self.save_metadata(
            "assessment_end_state", "state_self_esteem_assessment_endline_end"
        )
        await self.set_endline_reminder_timer()
        return await self.go_to_state(AssessmentApplication.START_STATE)

    async def state_self_esteem_assessment_endline_end(self):
        score = self.user.metadata.get("assessment_score", 0)
        # score of 0-14 high risk
        # score of 15-30 low risk
        risk = "high_risk" if score <= 14 else "low_risk"

        msisdn = normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.removeprefix("+")
        data = {
            "self_esteem_risk": risk,
            "self_esteem_score": score,
        }
        self.save_answer("state_self_esteem_endline_risk", risk)
        self.save_answer("state_self_esteem_endline_score", str(score))
        error = await rapidpro.update_profile(whatsapp_id, data, self.user.metadata)
        if error:
            return await self.go_to_state("state_error")

        await self.set_endline_reminder_timer()
        return await self.go_to_state("state_connectedness_assessment_endline")

    # Connectedness
    async def state_connectedness_assessment_endline(self):
        self.save_metadata("assessment_name", "connectedness_endline")
        self.save_metadata(
            "assessment_end_state", "state_connectedness_assessment_endline_end"
        )
        await self.set_endline_reminder_timer()
        return await self.go_to_state(AssessmentApplication.START_STATE)

    async def state_connectedness_assessment_endline_end(self):
        score = self.user.metadata.get("assessment_score", 0)
        # score of 0-1 high risk
        # score of 2-3 low risk
        risk = "high_risk" if score <= 1 else "low_risk"

        msisdn = normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.removeprefix("+")
        data = {
            "connectedness_risk": risk,
            "connectedness_score": score,
        }
        self.save_answer("state_connectedness_endline_risk", risk)
        self.save_answer("state_connectedness_endline_score", str(score))
        error = await rapidpro.update_profile(whatsapp_id, data, self.user.metadata)
        if error:
            return await self.go_to_state("state_error")

        await self.set_endline_reminder_timer()
        return await self.go_to_state("state_body_image_assessment_endline")

    # Body Image
    async def state_body_image_assessment_endline(self):
        self.save_metadata("assessment_name", "body_image_endline")
        self.save_metadata(
            "assessment_end_state", "state_body_image_assessment_endline_end"
        )

        await self.set_endline_reminder_timer()
        return await self.go_to_state(AssessmentApplication.START_STATE)

    async def state_body_image_assessment_endline_end(self):
        score = self.user.metadata.get("assessment_score", 0)
        # score of 0-4 high risk
        # score of 5-6 low risk
        risk = "high_risk" if score <= 4 else "low_risk"

        msisdn = normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.removeprefix("+")
        data = {
            "body_image_risk": risk,
            "body_image_score": score,
        }
        self.save_answer("state_body_image_endline_risk", risk)
        self.save_answer("state_body_image_endline_score", str(score))
        error = await rapidpro.update_profile(whatsapp_id, data, self.user.metadata)
        if error:
            return await self.go_to_state("state_error")

        await self.set_endline_reminder_timer()
        return await self.go_to_state("state_anxiety_assessment_endline")

    # Anxiety
    async def state_anxiety_assessment_endline(self):
        self.save_metadata("assessment_name", "anxiety_endline")
        self.save_metadata(
            "assessment_end_state", "state_anxiety_assessment_endline_end"
        )

        await self.set_endline_reminder_timer()
        return await self.go_to_state(AssessmentApplication.START_STATE)

    async def state_anxiety_assessment_endline_end(self):
        score = self.user.metadata.get("assessment_score", 0)
        self.anxiety_score = score
        # score of 3-6 high risk
        # score of 0-2 low risk
        risk = "high_risk" if score >= 3 else "low_risk"

        msisdn = normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.removeprefix("+")
        data = {
            "anxiety_risk": risk,
            "anxiety_score": score,
        }
        self.save_answer("state_anxiety_endline_risk", risk)
        self.save_answer("state_anxiety_endline_score", str(score))
        error = await rapidpro.update_profile(whatsapp_id, data, self.user.metadata)
        if error:
            return await self.go_to_state("state_error")
        return await self.go_to_state("state_depression_assessment_endline")

    # Depression
    async def state_depression_assessment_endline(self):
        self.save_metadata("assessment_name", "depression_endline")
        self.save_metadata(
            "assessment_end_state", "state_depression_assessment_endline_end"
        )

        await self.set_endline_reminder_timer()
        return await self.go_to_state(AssessmentApplication.START_STATE)

    async def state_depression_assessment_endline_end(self):
        score = self.user.metadata.get("assessment_score", 0)
        self.depression_score = score
        # score of 3-6 high risk
        # score of 0-2 low risk
        risk = "high_risk" if score >= 3 else "low_risk"

        msisdn = normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.removeprefix("+")
        data = {
            "depression_risk": risk,
            "depression_score": score,
        }
        self.save_answer("state_depression_endline_risk", risk)
        self.save_answer("state_depression_endline_score", str(score))
        error = await rapidpro.update_profile(whatsapp_id, data, self.user.metadata)
        if error:
            return await self.go_to_state("state_error")

        await self.set_endline_reminder_timer()
        return await self.go_to_state(
            "state_self_perceived_healthcare_assessment_endline"
        )

    # Self Perceived Healthcare
    async def state_self_perceived_healthcare_assessment_endline(self):
        self.save_metadata("assessment_name", "self_perceived_healthcare_endline")
        self.save_metadata(
            "assessment_end_state",
            "state_self_perceived_healthcare_assessment_endline_end",
        )

        await self.set_endline_reminder_timer()
        return await self.go_to_state(AssessmentApplication.START_STATE)

    async def state_self_perceived_healthcare_assessment_endline_end(self):
        score = self.user.metadata.get("assessment_score", 0)
        # score of 2-6 high risk
        # score of 7-10 low risk
        risk = "high_risk" if score <= 6 else "low_risk"

        msisdn = normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.removeprefix("+")
        data = {
            "self_perceived_healthcare_risk": risk,
            "self_perceived_healthcare_score": score,
        }
        self.save_answer("state_self_perceived_healthcare_endline_risk", risk)
        self.save_answer("state_self_perceived_healthcare_endline_score", str(score))
        error = await rapidpro.update_profile(whatsapp_id, data, self.user.metadata)
        if error:
            return await self.go_to_state("state_error")

        await self.set_endline_reminder_timer()
        return await self.go_to_state("state_sexual_health_lit_assessment_endline")

    # Sexual Health Literacy
    async def state_sexual_health_lit_assessment_endline(self):
        self.save_metadata("assessment_name", "sexual_health_literacy_endline")
        self.save_metadata(
            "assessment_end_state", "state_sexual_health_lit_assessment_endline_end"
        )

        await self.set_endline_reminder_timer()
        return await self.go_to_state(AssessmentApplication.START_STATE)

    async def state_sexual_health_lit_assessment_endline_end(self):
        score = self.user.metadata.get("assessment_score", 0)
        # score of 0-33 high risk
        # score of 34-55 low risk
        risk = "high_risk" if score <= 33 else "low_risk"

        msisdn = normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.removeprefix("+")
        data = {
            "sexual_health_lit_risk": risk,
            "sexual_health_lit_score": score,
        }
        self.save_answer("state_sexual_health_lit_endline_risk", risk)
        self.save_answer("state_sexual_health_lit_endline_score", str(score))
        error = await rapidpro.update_profile(whatsapp_id, data, self.user.metadata)
        if error:
            return await self.go_to_state("state_error")

        await self.set_endline_reminder_timer()
        return await self.go_to_state("state_gender_attitude_assessment_endline")

    # Gender Attitudes
    async def state_gender_attitude_assessment_endline(self):
        self.save_metadata("assessment_name", "gender_attitude_endline")
        self.save_metadata(
            "assessment_end_state", "state_gender_attitude_assessment_endline_end"
        )

        await self.set_endline_reminder_timer()
        return await self.go_to_state(AssessmentApplication.START_STATE)

    async def state_gender_attitude_assessment_endline_end(self):
        score = self.user.metadata.get("assessment_score", 0)
        # score of 0-8 high risk
        # score of 9-12 low risk
        risk = "high_risk" if score <= 8 else "low_risk"

        msisdn = normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.removeprefix("+")
        data = {
            "gender_attitude_risk": risk,
            "gender_attitude_score": score,
        }
        self.save_answer("state_gender_attitude_endline_risk", risk)
        self.save_answer("state_gender_attitude_endline_score", str(score))
        error = await rapidpro.update_profile(whatsapp_id, data, self.user.metadata)
        if error:
            return await self.go_to_state("state_error")

        await self.set_endline_reminder_timer()
        return await self.go_to_state("state_sexual_consent_assessment_endline")

    # Sexual Consent
    async def state_sexual_consent_assessment_endline(self):
        self.save_metadata("assessment_name", "sexual_consent_endline")
        self.save_metadata(
            "assessment_end_state", "state_sexual_consent_assessment_endline_end"
        )

        await self.set_endline_reminder_timer()
        return await self.go_to_state(AssessmentApplication.START_STATE)

    async def state_sexual_consent_assessment_endline_end(self):
        score = self.user.metadata.get("assessment_score", 0)
        # score of 0-6 high risk
        # score of 7-10 low risk
        risk = "high_risk" if score <= 6 else "low_risk"

        msisdn = normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.removeprefix("+")
        data = {
            "sexual_consent_risk": risk,
            "sexual_consent_score": score,
        }
        self.save_answer("state_sexual_consent_endline_risk", risk)
        self.save_answer("state_sexual_consent_endline_score", str(score))
        error = await rapidpro.update_profile(whatsapp_id, data, self.user.metadata)
        if error:
            return await self.go_to_state("state_error")

        await self.set_endline_reminder_timer()
        return await self.go_to_state("state_alcohol_assessment_endline")

    # Alcohol
    async def state_alcohol_assessment_endline(self):
        self.save_metadata("assessment_name", "alcohol_endline")
        self.save_metadata(
            "assessment_end_state", "state_alcohol_assessment_endline_end"
        )

        await self.set_endline_reminder_timer()
        return await self.go_to_state(AssessmentApplication.START_STATE)

    async def state_alcohol_assessment_endline_end(self):
        score = self.user.metadata.get("assessment_score", 0)
        # score of 13-20 high risk
        # score of 4-12 low risk
        risk = "high_risk" if score >= 13 else "low_risk"

        msisdn = normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.removeprefix("+")
        data = {
            "alcohol_risk": risk,
            "alcohol_score": score,
        }
        self.save_answer("state_alcohol_endline_risk", risk)
        self.save_answer("state_alcohol_endline_score", str(score))
        error = await rapidpro.update_profile(whatsapp_id, data, self.user.metadata)
        if error:
            return await self.go_to_state("state_error")

        return await self.go_to_state("state_platform_review_assessment_endline")

    # Platform Review
    async def state_platform_review_assessment_endline(self):
        self.save_metadata("assessment_name", "platform_review_endline")
        self.save_metadata("assessment_end_state", "state_submit_endline_completed")

        await self.set_endline_reminder_timer()
        return await self.go_to_state(AssessmentApplication.START_STATE)

    # Endline Airtime Incentive
    async def state_submit_endline_completed(self):
        msisdn = normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.removeprefix("+")
        data = {
            "endline_survey_completed": "True",
            "ejaf_endline_airtime_incentive_sent": "False",
            "ejaf_endline_completed_on": get_current_datetime().isoformat(),
            "endline_survey_started": "",
            "endline_reminder": "",
        }
        self.save_answer("endline_survey_completed", "True")
        self.save_answer("endline_survey_started", "False")
        self.save_answer("endline_reminder", "False")

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
                        "for some helpful messages or to ask any questions.",
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

    async def state_survey_validation(self):
        """
        Validates survey keywords from RapidPro
        """
        random_error = get_generic_error_options()

        return FreeText(self, question=random_error, next=None)
