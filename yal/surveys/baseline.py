# import asyncio
import logging

from vaccine.base_application import BaseApplication
from vaccine.states import Choice, WhatsAppButtonState
from yal import rapidpro
from yal.assessments import Application as AssessmentApplication
from yal.utils import normalise_phonenumber

logger = logging.getLogger(__name__)

# TODO:
# Check reason for text cutoff
# Add combined calc for dep and anxiety
# Fix interference for skip response


class Application(BaseApplication):
    START_STATE = "state_baseline_start"

    # Baseline start - Use this to link to survey from other areas
    async def state_baseline_start(self):
        return await self.go_to_state("state_self_esteem_assessment_v2")

    # TEMP TEST SPECIFIC QUESTION SET
    async def state_test_qset(self):
        self.save_metadata("assessment_name", "depression_v2")
        self.save_metadata("assessment_end_state", "state_depression_assessment_v2_end")
        return await self.go_to_state(AssessmentApplication.START_STATE)

    # Self Esteem
    async def state_self_esteem_assessment_v2(self):
        self.save_metadata("assessment_name", "self_esteem_v2")
        self.save_metadata(
            "assessment_end_state", "state_self_esteem_assessment_v2_end"
        )
        return await self.go_to_state(AssessmentApplication.START_STATE)

    async def state_self_esteem_assessment_v2_end(self):
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
            "self_esteem_v2_risk": risk,
            "self_esteem_v2_score": score,
        }
        self.save_answer("state_self_esteem_v2_risk", risk)
        self.save_answer("state_self_esteem_v2_score", str(score))
        error = await rapidpro.update_profile(whatsapp_id, data, self.user.metadata)
        if error:
            return await self.go_to_state("state_error")
        self.save_metadata("assessment_name", "connectedness_v2")
        self.save_metadata(
            "assessment_end_state", "state_connectedness_assessment_v2_end"
        )
        return await self.go_to_state(AssessmentApplication.START_STATE)

    # Connectedness
    async def state_connectedness_assessment_v2_end(self):
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
            "connectedness_v2_risk": risk,
            "connectedness_v2_score": score,
        }
        self.save_answer("state_connectedness_v2_risk", risk)
        self.save_answer("state_connectedness_v2_score", str(score))
        error = await rapidpro.update_profile(whatsapp_id, data, self.user.metadata)
        if error:
            return await self.go_to_state("state_error")
        self.save_metadata("assessment_name", "body_image_v2")
        self.save_metadata("assessment_end_state", "state_body_image_assessment_v2_end")
        return await self.go_to_state(AssessmentApplication.START_STATE)

    # Body Image
    async def state_body_image_assessment_v2_end(self):
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
            "body_image_v2_risk": risk,
            "body_image_v2_score": score,
        }
        self.save_answer("state_body_image_risk", risk)
        self.save_answer("state_body_image_score", str(score))
        error = await rapidpro.update_profile(whatsapp_id, data, self.user.metadata)
        if error:
            return await self.go_to_state("state_error")
        self.save_metadata("assessment_name", "depression_v2")
        self.save_metadata("assessment_end_state", "state_depression_assessment_v2_end")
        return await self.go_to_state(AssessmentApplication.START_STATE)

    # Depression
    async def state_depression_assessment_v2_end(self):
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
            "depression_v2_risk": risk,
            "depression_v2_score": score,
        }
        self.save_answer("depression_v2_risk", risk)
        self.save_answer("depression_v2_score", str(score))
        error = await rapidpro.update_profile(whatsapp_id, data, self.user.metadata)
        if error:
            return await self.go_to_state("state_error")
        self.save_metadata("assessment_name", "anxiety_v2")
        self.save_metadata("assessment_end_state", "state_anxiety_assessment_v2_end")
        return await self.go_to_state(AssessmentApplication.START_STATE)

    # Anxiety
    async def state_anxiety_assessment_v2_end(self):
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
            "anxiety_v2_risk": risk,
            "anxiety_v2_score": score,
        }
        self.save_answer("anxiety_v2_risk", risk)
        self.save_answer("anxiety_v2_score", str(score))
        error = await rapidpro.update_profile(whatsapp_id, data, self.user.metadata)
        if error:
            return await self.go_to_state("state_error")
        return await self.go_to_state("state_depression_and_anxiety_v2_end")

    # Depression & Anxiety - This is not a question set, but rather a piece of
    # logic to work out a combined "depression_and_anxiety" score

    async def state_depression_and_anxiety_v2_end(self):
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
            "depression_and_anxiety_v2_risk": risk,
            "depression_and_anxiety_v2_score": score,
        }
        self.save_answer("depression_and_anxiety_v2_risk", risk)
        self.save_answer("depression_and_anxiety_v2_score", str(score))
        error = await rapidpro.update_profile(whatsapp_id, data, self.user.metadata)
        if error:
            return await self.go_to_state("state_error")
        return await self.go_to_state("state_baseline_halfway_msg")

    # HALF WAY MESSAGE
    async def state_baseline_halfway_msg(self):
        msg = self._(
            "\n".join(
                [
                    "*We’re getting there! you’re doing great!* 🎉",
                    "",
                    "Just a few more questions to go and your R30 airtime will "
                    "be sent to you! 🤑",
                ]
            )
        )
        return WhatsAppButtonState(
            self,
            question=msg,
            choices=[Choice("OK", "OK Let's do it")],
            error=self.go_to_state("state_error"),
            next="state_self_perceived_healthcare_assessment_v2",
        )

    # Self Perceived Healthcare
    async def state_self_perceived_healthcare_assessment_v2(self):
        self.save_metadata("assessment_name", "self_perceived_healthcare_v2")
        self.save_metadata(
            "assessment_end_state", "state_self_perceived_healthcare_assessment_v2_end"
        )
        return await self.go_to_state(AssessmentApplication.START_STATE)

    async def state_self_perceived_healthcare_assessment_v2_end(self):
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
            "self_perceived_healthcare_v2_risk": risk,
            "self_perceived_healthcare_v2_score": score,
        }
        self.save_answer("self_perceived_healthcare_v2_risk", risk)
        self.save_answer("self_perceived_healthcare_V2_score", str(score))
        error = await rapidpro.update_profile(whatsapp_id, data, self.user.metadata)
        if error:
            return await self.go_to_state("state_error")
        self.save_metadata("assessment_name", "sexual_health_literacy_v2")
        self.save_metadata(
            "assessment_end_state", "state_sexual_health_lit_assessment_v2_end"
        )
        return await self.go_to_state(AssessmentApplication.START_STATE)

    # Sexual Health Literacy
    async def state_sexual_health_lit_assessment_v2_end(self):
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
            "sexual_health_lit_v2_risk": risk,
            "sexual_health_lit_v2_score": score,
        }
        self.save_answer("sexual_health_lit_v2_risk", risk)
        self.save_answer("sexual_health_lit_v2_score", str(score))
        error = await rapidpro.update_profile(whatsapp_id, data, self.user.metadata)
        if error:
            return await self.go_to_state("state_error")
        self.save_metadata("assessment_name", "gender_attitude_v2")
        self.save_metadata(
            "assessment_end_state", "state_gender_attitude_assessment_v2_end"
        )
        return await self.go_to_state(AssessmentApplication.START_STATE)

    # Gender Attitudes
    async def state_gender_attitude_assessment_v2_end(self):
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
            "gender_attitude_v2_risk": risk,
            "gender_attitude_v2_score": score,
        }
        self.save_answer("gender_attitude_v2_risk", risk)
        self.save_answer("gender_attitude_V2_score", str(score))
        error = await rapidpro.update_profile(whatsapp_id, data, self.user.metadata)
        if error:
            return await self.go_to_state("state_error")
        self.save_metadata("assessment_name", "sexual_consent_v2")
        self.save_metadata(
            "assessment_end_state", "state_sexual_consent_assessment_v2_end"
        )
        return await self.go_to_state(AssessmentApplication.START_STATE)

    # Sexual Consent
    async def state_sexual_consent_assessment_v2_end(self):
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
            "sexual_consent_v2_risk": risk,
            "sexual_consent_v2_score": score,
        }
        self.save_answer("sexual_consent_v2_risk", risk)
        self.save_answer("sexual_consent_V2_score", str(score))
        error = await rapidpro.update_profile(whatsapp_id, data, self.user.metadata)
        if error:
            return await self.go_to_state("state_error")
        self.save_metadata("assessment_name", "alcohol_v2")
        self.save_metadata("assessment_end_state", "state_alcohol_assessment_v2_end")
        return await self.go_to_state(AssessmentApplication.START_STATE)

    # Alcohol
    async def state_alcohol_assessment_v2_end(self):
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
            "alcohol_v2_risk": risk,
            "alcohol_v2_score": score,
        }
        self.save_answer("alcohol_v2_risk", risk)
        self.save_answer("alcohol_V2_score", str(score))
        error = await rapidpro.update_profile(whatsapp_id, data, self.user.metadata)
        if error:
            return await self.go_to_state("state_error")
        return await self.go_to_state("state_baseline_end")

    # Baseline End
    # TODO: Rememeber to check for survey complete variable.

    async def state_baseline_end(self):
        msg = self._(
            "\n".join(
                [
                    "Thank you for taking our survey",
                ]
            )
        )

        await self.publish_message(msg)
