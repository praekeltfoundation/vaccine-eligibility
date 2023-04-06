import asyncio
import logging

from vaccine.base_application import BaseApplication
from vaccine.states import Choice, FreeText, WhatsAppButtonState, WhatsAppListState
from yal import rapidpro
from yal.assessments import Application as AssessmentApplication
from yal.utils import normalise_phonenumber

logger = logging.getLogger(__name__)


class Application(BaseApplication):
    START_STATE = "state_invitation"

    async def state_invitation(self):
        msg = self._(
            "\n".join(
                [
                    "we're starting now",
                ]
            )
        )

        await self.publish_message(msg)
        self.save_metadata(
            "assessment_name", "connectedness_v2"
        )  # example name for the baseline assessments
        self.save_metadata(
            "assessment_end_state", "state_connectedness_assessment_v2_end"
        )
        return await self.go_to_state(AssessmentApplication.START_STATE)

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
            "connectedness_risk": risk,
            "connectedness_score": score,
        }
        self.save_answer("state_connectedness_risk", risk)
        self.save_answer("state_connectedness_score", str(score))
        error = await rapidpro.update_profile(whatsapp_id, data, self.user.metadata)
        if error:
            return await self.go_to_state("state_error")
        self.save_metadata("assessment_name", "body_image_v2")
        self.save_metadata("assessment_end_state", "state_body_image_assessment_v2_end")
        return await self.go_to_state(AssessmentApplication.START_STATE)

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
            "body_image_risk": risk,
            "body_image_score": score,
        }
        self.save_answer("state_body_image_risk", risk)
        self.save_answer("state_body_image_score", str(score))
        error = await rapidpro.update_profile(whatsapp_id, data, self.user.metadata)
        if error:
            return await self.go_to_state("state_error")
        self.save_metadata("assessment_name", "depression_v2")
        self.save_metadata("assessment_end_state", "state_depression_assessment_v2_end")
        return await self.go_to_state(AssessmentApplication.START_STATE)

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
            "depression_risk": risk,
            "depression_score": score,
        }
        self.save_answer("state_depression_risk", risk)
        self.save_answer("state_depression_score", str(score))
        error = await rapidpro.update_profile(whatsapp_id, data, self.user.metadata)
        if error:
            return await self.go_to_state("state_error")
        return await self.go_to_state("state_baseline_end")

    async def state_baseline_end(self):
        msg = self._(
            "\n".join(
                [
                    "Thank you for taking our survey",
                ]
            )
        )

        await self.publish_message(msg)


# Self Esteem

# Connectetedness

# Body Image

# Depression

##########    HALF WAY MESSAGE

# Self Perceived Health Care

# Sexual Health Literacy

# Gender Attitudes

# Sexual Consent
