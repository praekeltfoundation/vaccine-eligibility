import asyncio

from vaccine.base_application import BaseApplication
from vaccine.states import (
    Choice,
    ChoiceState,
    FreeText,
    WhatsAppButtonState,
    WhatsAppListState,
)
from yal.data.seqmentation_survey_questions import SURVEY_QUESTIONS
from yal.utils import get_generic_error


class Application(BaseApplication):
    START_STATE = "state_survey_question"

    async def state_survey_question(self):
        metadata = self.user.metadata

        section = str(metadata.get("segment_section", "1"))
        print("state_survey_question", section, SURVEY_QUESTIONS.keys())

        if section not in SURVEY_QUESTIONS:
            self.delete_metadata("segment_section")
            self.delete_metadata("segment_question")
            self.delete_metadata("segment_question_nr")
            return await self.go_to_state(metadata["assessment_end_state"])

        current_question = metadata.get("segment_question")

        if not current_question:
            current_question = SURVEY_QUESTIONS[section]["start"]
            self.save_metadata("segment_question", current_question)

        question_number = metadata.get("segment_question_nr", 1)

        questions = SURVEY_QUESTIONS[section]["questions"]
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

        section = metadata.get("segment_section", 1)
        current_question = metadata.get("segment_question")
        answer = answers.get(current_question)
        question_number = metadata.get("segment_question_nr", 1)

        question = SURVEY_QUESTIONS[str(section)]["questions"][current_question]

        next = None

        if question["next"]:
            if type(question["next"]) == dict:
                next = question["next"][answer]
            else:
                next = question["next"]

        if next:
            self.save_metadata("segment_question", next)
            self.save_metadata("segment_question_nr", question_number + 1)
        else:
            self.save_metadata("segment_section", section + 1)
            self.save_metadata("segment_question_nr", 1)
            self.delete_metadata("segment_question")

        return await self.go_to_state("state_survey_question")
