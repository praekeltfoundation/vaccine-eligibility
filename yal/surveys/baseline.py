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

# TODO:
# Check flow results
# Get understanding of the content people get sent based on these answers
# specifically for the depression_and_anxiety one


class Application(BaseApplication):
    depression_score = 0
    anxiety_score = 0
    START_STATE = "state_baseline_start"

    async def set_reminder_timer(self):
        msisdn = normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.lstrip(" + ")

        assessment_name = self.user.metadata.get("assessment_name", "self_esteem_v2")
        data = {
            "assessment_reminder": get_current_datetime().isoformat(),
            "assessment_reminder_name": assessment_name,
            "assessment_reminder_type": "reengagement 30min",
        }

        return await rapidpro.update_profile(whatsapp_id, data, self.user.metadata)

    # Baseline start - Use this to link to survey from other areas
    async def state_baseline_start(self):
        return await self.go_to_state("state_self_esteem_assessment_v2")

    # Self Esteem
    async def state_self_esteem_assessment_v2(self):
        self.save_metadata("assessment_name", "self_esteem_v2")
        self.save_metadata(
            "assessment_end_state", "state_self_esteem_assessment_v2_end"
        )
        await self.set_reminder_timer()
        return await self.go_to_state(AssessmentApplication.START_STATE)

    async def state_self_esteem_assessment_v2_end(self):
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
        await self.set_reminder_timer()
        return await self.go_to_state(AssessmentApplication.START_STATE)

    # Connectedness
    async def state_connectedness_assessment_v2_end(self):
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

        await self.set_reminder_timer()
        return await self.go_to_state(AssessmentApplication.START_STATE)

    # Body Image
    async def state_body_image_assessment_v2_end(self):
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
            "body_image_v2_risk": risk,
            "body_image_v2_score": score,
        }
        self.save_answer("state_body_image_v2_risk", risk)
        self.save_answer("state_body_image_v2_score", str(score))
        error = await rapidpro.update_profile(whatsapp_id, data, self.user.metadata)
        if error:
            return await self.go_to_state("state_error")
        self.save_metadata("assessment_name", "depression_v2")
        self.save_metadata("assessment_end_state", "state_depression_assessment_v2_end")

        await self.set_reminder_timer()
        return await self.go_to_state(AssessmentApplication.START_STATE)

    # Depression
    async def state_depression_assessment_v2_end(self):
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
            "depression_v2_risk": risk,
            "depression_v2_score": score,
        }
        self.save_answer("state_depression_v2_risk", risk)
        self.save_answer("state_depression_v2_score", str(score))
        error = await rapidpro.update_profile(whatsapp_id, data, self.user.metadata)
        if error:
            return await self.go_to_state("state_error")
        self.save_metadata("assessment_name", "anxiety_v2")
        self.save_metadata("assessment_end_state", "state_anxiety_assessment_v2_end")

        await self.set_reminder_timer()
        return await self.go_to_state(AssessmentApplication.START_STATE)

    # Anxiety
    async def state_anxiety_assessment_v2_end(self):
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
            "anxiety_v2_risk": risk,
            "anxiety_v2_score": score,
        }
        self.save_answer("state_anxiety_v2_risk", risk)
        self.save_answer("state_anxiety_v2_score", str(score))
        error = await rapidpro.update_profile(whatsapp_id, data, self.user.metadata)
        if error:
            return await self.go_to_state("state_error")
        return await self.go_to_state("state_depression_and_anxiety_v2_end")

    # Depression & Anxiety - This is not a question set, but rather a piece of
    # logic to work out a combined "depression_and_anxiety" score

    async def state_depression_and_anxiety_v2_end(self):
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
            "state_depression_and_anxiety_v2_risk": risk,
            "state_depression_and_anxiety_v2_score": score,
        }
        self.save_answer("state_depression_and_anxiety_v2_risk", risk)
        self.save_answer("state_depression_and_anxiety_v2_score", str(score))
        error = await rapidpro.update_profile(whatsapp_id, data, self.user.metadata)
        if error:
            return await self.go_to_state("state_error")
        return await self.go_to_state("state_baseline_halfway_msg")

    # HALF WAY MESSAGE
    async def state_baseline_halfway_msg(self):
        msg = self._(
            "\n".join(
                [
                    "*We’re getting there! You’re doing great!* 🎉",
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
            error=self._(get_generic_error()),
            next="state_self_perceived_healthcare_assessment_v2",
        )

    # Self Perceived Healthcare
    async def state_self_perceived_healthcare_assessment_v2(self):
        self.save_metadata("assessment_name", "self_perceived_healthcare_v2")
        self.save_metadata(
            "assessment_end_state", "state_self_perceived_healthcare_assessment_v2_end"
        )

        await self.set_reminder_timer()
        return await self.go_to_state(AssessmentApplication.START_STATE)

    async def state_self_perceived_healthcare_assessment_v2_end(self):
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
            "self_perceived_healthcare_v2_risk": risk,
            "self_perceived_healthcare_v2_score": score,
        }
        self.save_answer("state_self_perceived_healthcare_v2_risk", risk)
        self.save_answer("state_self_perceived_healthcare_V2_score", str(score))
        error = await rapidpro.update_profile(whatsapp_id, data, self.user.metadata)
        if error:
            return await self.go_to_state("state_error")
        self.save_metadata("assessment_name", "sexual_health_literacy_v2")
        self.save_metadata(
            "assessment_end_state", "state_sexual_health_lit_assessment_v2_end"
        )

        await self.set_reminder_timer()
        return await self.go_to_state(AssessmentApplication.START_STATE)

    # Sexual Health Literacy
    async def state_sexual_health_lit_assessment_v2_end(self):
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
            "sexual_health_lit_v2_risk": risk,
            "sexual_health_lit_v2_score": score,
        }
        self.save_answer("state_sexual_health_lit_v2_risk", risk)
        self.save_answer("state_sexual_health_lit_v2_score", str(score))
        error = await rapidpro.update_profile(whatsapp_id, data, self.user.metadata)
        if error:
            return await self.go_to_state("state_error")
        self.save_metadata("assessment_name", "gender_attitude_v2")
        self.save_metadata(
            "assessment_end_state", "state_gender_attitude_assessment_v2_end"
        )

        await self.set_reminder_timer()
        return await self.go_to_state(AssessmentApplication.START_STATE)

    # Gender Attitudes
    async def state_gender_attitude_assessment_v2_end(self):
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
            "gender_attitude_v2_risk": risk,
            "gender_attitude_v2_score": score,
        }
        self.save_answer("state_gender_attitude_v2_risk", risk)
        self.save_answer("state_gender_attitude_V2_score", str(score))
        error = await rapidpro.update_profile(whatsapp_id, data, self.user.metadata)
        if error:
            return await self.go_to_state("state_error")
        self.save_metadata("assessment_name", "sexual_consent_v2")
        self.save_metadata(
            "assessment_end_state", "state_sexual_consent_assessment_v2_end"
        )

        await self.set_reminder_timer()
        return await self.go_to_state(AssessmentApplication.START_STATE)

    # Sexual Consent
    async def state_sexual_consent_assessment_v2_end(self):
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
            "sexual_consent_v2_risk": risk,
            "sexual_consent_v2_score": score,
        }
        self.save_answer("state_sexual_consent_v2_risk", risk)
        self.save_answer("state_sexual_consent_V2_score", str(score))
        error = await rapidpro.update_profile(whatsapp_id, data, self.user.metadata)
        if error:
            return await self.go_to_state("state_error")
        self.save_metadata("assessment_name", "alcohol_v2")
        self.save_metadata("assessment_end_state", "state_alcohol_assessment_v2_end")

        await self.set_reminder_timer()
        return await self.go_to_state(AssessmentApplication.START_STATE)

    # Alcohol
    async def state_alcohol_assessment_v2_end(self):
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
            "alcohol_v2_risk": risk,
            "alcohol_v2_score": score,
        }
        self.save_answer("state_alcohol_v2_risk", risk)
        self.save_answer("state_alcohol_V2_score", str(score))
        error = await rapidpro.update_profile(whatsapp_id, data, self.user.metadata)
        if error:
            return await self.go_to_state("state_error")

        return await self.go_to_state("state_baseline_end")

    # Baseline End
    # TODO: Rememeber to check for survey complete variable.

    async def state_baseline_end(self):
        return WhatsAppButtonState(
            self,
            question=self._(
                "\n".join(
                    [
                        "*And thats a wrap!*",
                        "",
                        "Thank you for taking part in our survey 🙏🏽",
                        "",
                        "*You will get your R30 airtime within 24 hours.*",
                        "",
                        "The B-Wise chatbot will send you some  helpful messages.",
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
