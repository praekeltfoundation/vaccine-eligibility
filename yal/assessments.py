import asyncio
from datetime import timedelta

from vaccine.base_application import BaseApplication
from vaccine.states import (
    Choice,
    ChoiceState,
    FreeText,
    WhatsAppButtonState,
    WhatsAppListState,
)
from yal import rapidpro
from yal.assessment_data.A1_sexual_health_literacy import (
    ASSESSMENT_QUESTIONS as SEXUAL_HEALTH_LITERACY_QUESTIONS,
)
from yal.assessment_data.A2_locus_of_control import (
    ASSESSMENT_QUESTIONS as LOCUS_OF_CONTROL_QUESTIONS,
)
from yal.assessment_data.A3_depression_and_anxiety import (
    ASSESSMENT_QUESTIONS as DEPRESSION_AND_ANXIETY_QUESTIONS,
)
from yal.assessment_data.A4_connectedness import (
    ASSESSMENT_QUESTIONS as CONNECTEDNESS_QUESTIONS,
)
from yal.assessment_data.A5_gender_attitude import (
    ASSESSMENT_QUESTIONS as GENDER_ATTITUDE,
)
from yal.assessment_data.A6_body_image import (
    ASSESSMENT_QUESTIONS as BODY_IMAGE_QUESTIONS,
)
from yal.assessment_data.A7_self_perceived_healthcare import (
    ASSESSMENT_QUESTIONS as SELF_PERCEIVED_HEALTHCARE_QUESTIONS,
)
from yal.assessment_data.A8_self_esteem import (
    ASSESSMENT_QUESTIONS as SELF_ESTEEM_QUESTIONS,
)
from yal.mainmenu import Application as MainMenuApplication
from yal.utils import get_current_datetime, get_generic_error, normalise_phonenumber

QUESTIONS = {
    "sexual_health_literacy": SEXUAL_HEALTH_LITERACY_QUESTIONS,
    "locus_of_control": LOCUS_OF_CONTROL_QUESTIONS,
    "depression_and_anxiety": DEPRESSION_AND_ANXIETY_QUESTIONS,
    "connectedness": CONNECTEDNESS_QUESTIONS,
    "gender_attitude": GENDER_ATTITUDE,
    "body_image": BODY_IMAGE_QUESTIONS,
    "self_perceived_healthcare": SELF_PERCEIVED_HEALTHCARE_QUESTIONS,
    "self_esteem": SELF_ESTEEM_QUESTIONS,
}


class Application(BaseApplication):
    START_STATE = "state_survey_start"
    LATER_STATE = "state_assessment_later_submit"

    async def state_survey_start(self):
        self.delete_metadata("assessment_section")
        self.delete_metadata("assessment_question")
        self.delete_metadata("assessment_question_nr")
        return await self.go_to_state("state_survey_question")

    async def state_survey_question(self):
        metadata = self.user.metadata

        section = str(metadata.get("assessment_section", "1"))

        assessment_name = metadata.get("assessment_name", "locus_of_control")
        questions = QUESTIONS[assessment_name]

        if section not in questions:
            self.delete_metadata("assessment_section")
            self.delete_metadata("assessment_question")
            self.delete_metadata("assessment_question_nr")
            return await self.go_to_state(metadata["assessment_end_state"])

        current_question = metadata.get("assessment_question")

        if not current_question:
            current_question = questions[section]["start"]
            self.save_metadata("assessment_question", current_question)

        question_number = metadata.get("assessment_question_nr", 1)

        questions = questions[section]["questions"]
        total_questions = sum(1 for q in questions.values() if q.get("type") != "info")
        progress_bar = (
            (question_number - 1) * "✅"
            + "◼️"
            + (total_questions - question_number) * "◽️"
        )

        question = questions[current_question]
        question_type = question.get("type", "choice")

        if question_type == "info":
            await self.publish_message(question["text"])
            await asyncio.sleep(0.5)
            return await self.go_to_state("state_survey_process_answer")

        header = "\n".join(
            [
                f"{progress_bar}",
                "-----",
                "",
            ]
        )

        choices = []
        for option in question.get("options", []):
            if isinstance(option, tuple):
                stub, option = option
            else:
                stub = option.replace(" ", "_").lower()
            choices.append(Choice(stub, option))

        if question_type == "choice":
            return ChoiceState(
                self,
                question=question["text"] + "\n",
                header=header,
                error=get_generic_error() + "\n",
                choices=choices,
                next="state_survey_process_answer",
                override_answer_name=current_question,
            )
        elif question_type == "list":
            return WhatsAppListState(
                self,
                question=f"{header}\n{question['text']}",
                error=get_generic_error(),
                choices=choices,
                button=question.get("button", "Choose option"),
                next="state_survey_process_answer",
                override_answer_name=current_question,
            )
        elif question_type == "button":
            return WhatsAppButtonState(
                self,
                question=f"{header}\n{question['text']}",
                error=get_generic_error(),
                choices=choices,
                next="state_survey_process_answer",
                override_answer_name=current_question,
            )
        else:
            return FreeText(
                self,
                question=question["text"],
                header=header,
                next="state_survey_process_answer",
                override_answer_name=current_question,
            )

    async def state_survey_process_answer(self):
        metadata = self.user.metadata
        answers = self.user.answers

        section = metadata.get("assessment_section", 1)
        current_question = metadata.get("assessment_question")
        answer = answers.get(current_question)
        question_number = metadata.get("assessment_question_nr", 1)

        assessment_name = metadata.get("assessment_name", "locus_of_control")
        questions = QUESTIONS[assessment_name]
        question = questions[str(section)]["questions"][current_question]

        next = None

        if question["next"]:
            if type(question["next"]) == dict:
                next = question["next"][answer]
            else:
                next = question["next"]

        if next:
            self.save_metadata("assessment_question", next)
            self.save_metadata("assessment_question_nr", question_number + 1)
        else:
            self.save_metadata("assessment_section", section + 1)
            self.save_metadata("assessment_question_nr", 1)
            self.delete_metadata("assessment_question")

        if question.get("scoring"):
            scoring = question["scoring"]
            if scoring.get(answer):
                score = metadata.get("assessment_score") or 0
                score += scoring[answer]
                self.save_metadata("assessment_score", score)

        return await self.go_to_state("state_survey_question")

    async def state_assessment_later_submit(self):
        msisdn = normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.lstrip(" + ")

        reminder_time = get_current_datetime() + timedelta(hours=23)
        assessment_name = self.user.metadata.get("assessment_name", "locus_of_control")

        data = {
            "assessment_reminder": reminder_time.isoformat(),
            "assessment_name": assessment_name,
        }

        await rapidpro.update_profile(whatsapp_id, data, self.user.metadata)
        return await self.go_to_state("state_assessment_later")

    async def state_assessment_later(self):
        question = self._(
            "\n".join(
                [
                    "[persona_emoji] No worries, we get it!",
                    "",
                    "I'll send you a reminder message tomorrow, so you can come back "
                    "and continue with these questions, then.",
                    "",
                    "Check you later 🤙🏾",
                ]
            )
        )
        return WhatsAppButtonState(
            self,
            question=question,
            choices=[Choice("menu", "Go to main menu")],
            error=get_generic_error(),
            next=MainMenuApplication.START_STATE,
        )
