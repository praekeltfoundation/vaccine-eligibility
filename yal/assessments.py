import asyncio

from vaccine.base_application import BaseApplication
from vaccine.states import (
    Choice,
    ChoiceState,
    FreeText,
    WhatsAppButtonState,
    WhatsAppListState,
)
from yal import rapidpro, utils
from yal.askaquestion import Application as AAQApplication

# Assessments currently part of main flow
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
from yal.assessment_data.reengagement import REENGAGEMENT
from yal.assessment_data_V2.alcohol import ASSESSMENT_QUESTIONS as ALCOHOL_QUESTIONS_V2
from yal.assessment_data_V2.anxiety import ASSESSMENT_QUESTIONS as ANXIETY_QUESTIONS_V2
from yal.assessment_data_V2.body_image import (
    ASSESSMENT_QUESTIONS as BODY_IMAGE_QUESTIONS_V2,
)
from yal.assessment_data_V2.connectedness import (
    ASSESSMENT_QUESTIONS as CONNECTEDNESS_QUESTIONS_V2,
)
from yal.assessment_data_V2.depression import (
    ASSESSMENT_QUESTIONS as DEPRESSION_QUESTIONS_V2,
)
from yal.assessment_data_V2.gender_attitude import (
    ASSESSMENT_QUESTIONS as GENDER_ATTITUDE_QUESTIONS_V2,
)

# Assessments that form part of the Baseline study
from yal.assessment_data_V2.self_esteem import (
    ASSESSMENT_QUESTIONS as SELF_ESTEEM_QUESTIONS_V2,
)
from yal.assessment_data_V2.self_perceived_healthcare import (
    ASSESSMENT_QUESTIONS as SELF_PERCEIVED_HEALTHCARE_QUESTIONS_V2,
)
from yal.assessment_data_V2.sexual_consent import (
    ASSESSMENT_QUESTIONS as SEXUAL_CONSENT_QUESTIONS_V2,
)
from yal.assessment_data_V2.sexual_health_literacy import (
    ASSESSMENT_QUESTIONS as SEXUAL_HEALTH_LITERACY_QUESTIONS_V2,
)
from yal.question_sets.endline.alcohol_endline import (
    ASSESSMENT_QUESTIONS as ALCOHOL_QUESTIONS_ENDLINE,
)
from yal.question_sets.endline.anxiety_endline import (
    ASSESSMENT_QUESTIONS as ANXIETY_QUESTIONS_ENDLINE,
)
from yal.question_sets.endline.body_image_endline import (
    ASSESSMENT_QUESTIONS as BODY_IMAGE_QUESTIONS_ENDLINE,
)
from yal.question_sets.endline.connectedness_endline import (
    ASSESSMENT_QUESTIONS as CONNECTEDNESS_QUESTIONS_ENDLINE,
)
from yal.question_sets.endline.depression_endline import (
    ASSESSMENT_QUESTIONS as DEPRESSION_QUESTIONS_ENDLINE,
)
from yal.question_sets.endline.gender_attitude_endline import (
    ASSESSMENT_QUESTIONS as GENDER_ATTITUDE_QUESTIONS_ENDLINE,
)
from yal.question_sets.endline.locus_of_control_endline import (
    ASSESSMENT_QUESTIONS as LOCUS_OF_CONTROL_QUESTIONS_ENDLINE,
)
from yal.question_sets.endline.platform_review_endline import (
    ASSESSMENT_QUESTIONS as PLATFORM_REVIEW_QUESTIONS_ENDLINE,
)
from yal.question_sets.endline.self_esteem_endline import (
    ASSESSMENT_QUESTIONS as SELF_ESTEEM_QUESTIONS_ENDLINE,
)
from yal.question_sets.endline.self_perceived_healthcare_endline import (
    ASSESSMENT_QUESTIONS as SELF_PERCEIVED_HEALTHCARE_QUESTIONS_ENDLINE,
)
from yal.question_sets.endline.sexual_consent_endline import (
    ASSESSMENT_QUESTIONS as SEXUAL_CONSENT_QUESTIONS_ENDLINE,
)
from yal.question_sets.endline.sexual_health_literacy_endline import (
    ASSESSMENT_QUESTIONS as SEXUAL_HEALTH_LITERACY_QUESTIONS_ENDLINE,
)
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
    "body_image": BODY_IMAGE_QUESTIONS,
    "self_esteem_v2": SELF_ESTEEM_QUESTIONS_V2,
    "connectedness_v2": CONNECTEDNESS_QUESTIONS_V2,
    "body_image_v2": BODY_IMAGE_QUESTIONS_V2,
    "depression_v2": DEPRESSION_QUESTIONS_V2,
    "anxiety_v2": ANXIETY_QUESTIONS_V2,
    "self_perceived_healthcare_v2": SELF_PERCEIVED_HEALTHCARE_QUESTIONS_V2,
    "sexual_health_lit_v2": SEXUAL_HEALTH_LITERACY_QUESTIONS_V2,
    "gender_attitude_v2": GENDER_ATTITUDE_QUESTIONS_V2,
    "sexual_consent_v2": SEXUAL_CONSENT_QUESTIONS_V2,
    "alcohol_v2": ALCOHOL_QUESTIONS_V2,
    "self_esteem_endline": SELF_ESTEEM_QUESTIONS_ENDLINE,
    "connectedness_endline": CONNECTEDNESS_QUESTIONS_ENDLINE,
    "body_image_endline": BODY_IMAGE_QUESTIONS_ENDLINE,
    "depression_endline": DEPRESSION_QUESTIONS_ENDLINE,
    "anxiety_endline": ANXIETY_QUESTIONS_ENDLINE,
    "self_perceived_healthcare_endline": SELF_PERCEIVED_HEALTHCARE_QUESTIONS_ENDLINE,
    "sexual_health_literacy_endline": SEXUAL_HEALTH_LITERACY_QUESTIONS_ENDLINE,
    "gender_attitude_endline": GENDER_ATTITUDE_QUESTIONS_ENDLINE,
    "sexual_consent_endline": SEXUAL_CONSENT_QUESTIONS_ENDLINE,
    "alcohol_endline": ALCOHOL_QUESTIONS_ENDLINE,
    "platform_review_endline": PLATFORM_REVIEW_QUESTIONS_ENDLINE,
    "locus_of_control_endline": LOCUS_OF_CONTROL_QUESTIONS_ENDLINE,
}


class Application(BaseApplication):
    START_STATE = "state_survey_start"
    LATER_STATE = "state_assessment_later_submit"
    REMINDER_STATE = "state_handle_assessment_reminder_response"

    def clean_name(self, name):
        return name.removeprefix("state_").removesuffix("_assessment")

    async def state_survey_start(self):
        self.delete_metadata("assessment_section")
        self.delete_metadata("assessment_question")
        self.delete_metadata("assessment_question_nr")
        self.delete_metadata("assessment_score")

        metadata = self.user.metadata
        assessment_name = self.clean_name(
            metadata.get("assessment_name", "locus_of_control")
        )
        self.save_answer("assessment_started", assessment_name)

        return await self.go_to_state("state_survey_question")

    async def state_survey_question(self):
        metadata = self.user.metadata

        section = str(metadata.get("assessment_section", "1"))

        assessment_name = self.clean_name(
            metadata.get("assessment_name", "locus_of_control")
        )

        msisdn = utils.normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.lstrip(" + ")
        data = {
            "assessment_reminder": get_current_datetime().isoformat(),
            "assessment_reminder_name": assessment_name,
            "assessment_reminder_type": "reengagement 30min",
        }

        error = await rapidpro.update_profile(whatsapp_id, data, self.user.metadata)
        if error:
            return await self.go_to_state("state_error")

        questions = QUESTIONS[assessment_name]

        if section not in questions:
            self.delete_metadata("assessment_section")
            self.delete_metadata("assessment_question")
            self.delete_metadata("assessment_question_nr")
            # clear assessment reminder info
            if self.user.metadata.get("assessment_reminder") or self.user.metadata.get(
                "assessment_reminder_type"
            ):
                data = {
                    "assessment_reminder": "",
                    "assessment_reminder_type": "",
                }
                error = await rapidpro.update_profile(
                    whatsapp_id, data, self.user.metadata
                )
                if error:
                    return await self.go_to_state("state_error")
            self.save_answer("assessment_completed", assessment_name)
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

        assessment_name = self.clean_name(
            metadata.get("assessment_name", "locus_of_control")
        )
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
            question_type = question.get("type", "choice")

            if question_type != "info":
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

        assessment_name = self.clean_name(
            self.user.metadata.get("assessment_name", "locus_of_control")
        )

        data = {
            "assessment_reminder": get_current_datetime().isoformat(),
            "assessment_reminder_name": assessment_name,
            "assessment_reminder_type": "later 1hour",
        }

        await rapidpro.update_profile(whatsapp_id, data, self.user.metadata)
        return await self.go_to_state("state_assessment_later")

    async def state_assessment_later(self):
        question = self._(
            "\n".join(
                [
                    "[persona_emoji] No worries, we get it!",
                    "",
                    "I'll send you a reminder message in 1 hour, so you can come back "
                    "and answer these questions.",
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
            next="state_pre_mainmenu",
        )

    async def state_handle_assessment_reminder_response(self):
        inbound = utils.clean_inbound(self.inbound.content)
        if inbound in [
            "continue now",
            "let s do it",
            "ask away",
            "start the questions",
            "Yes, I want to answer",
        ]:
            msisdn = utils.normalise_phonenumber(self.inbound.from_addr)
            whatsapp_id = msisdn.lstrip(" + ")
            data = {
                "assessment_reminder_sent": "",  # Reset the field
            }
            assessment_name = self.clean_name(
                self.user.metadata["assessment_reminder_name"]
            )
            # send reengagement message
            if REENGAGEMENT.get(assessment_name):
                await self.publish_message(REENGAGEMENT.get(assessment_name))
                await asyncio.sleep(0.5)

            error = await rapidpro.update_profile(whatsapp_id, data, self.user.metadata)
            if error:
                return await self.go_to_state("state_error")
            if "v2" in assessment_name:
                # for v2 names we have to move _v2 to the end to get the state name
                return await self.go_to_state(
                    f"state_{assessment_name.replace('_v2', '')}_assessment_v2"
                )
            if "endline" in assessment_name:
                assessment_name_replace = assessment_name.replace("_endline", "")
                return await self.go_to_state(
                    f"state_{assessment_name_replace}_assessment_endline"
                )

            return await self.go_to_state(f"state_{assessment_name}_assessment")

        if inbound == "skip":
            return await self.go_to_state("state_stop_assessment_reminders_confirm")

        if inbound == "remind me in 1 hour":
            self.save_metadata("assessment_reminder_hours", "1hour")
            return await self.go_to_state("state_reschedule_assessment_reminder")

        if inbound == "remind me tomorrow":
            self.save_metadata("assessment_reminder_hours", "23hours")
            return await self.go_to_state("state_reschedule_assessment_reminder")

        if inbound == "i m not interested":
            msisdn = utils.normalise_phonenumber(self.inbound.from_addr)
            whatsapp_id = msisdn.lstrip(" + ")
            data = {
                "assessment_reminder_name": "",
                "assessment_reminder_sent": "",
                "assessment_reminder_type": "",
            }  # Reset the fields

            error = await rapidpro.update_profile(whatsapp_id, data, self.user.metadata)
            if error:
                return await self.go_to_state("state_error")
            # TODO: Hlami, check if the the survey is endline.
            # if "endline" in assessment_name:
            #     return self.go_to_state("state_not_interested")

            return await self.go_to_state("state_pre_mainmenu")

    async def state_not_interested(self):
        return FreeText(
            self,
            question=self._(
                "\n".join(
                    [
                        "That's completely okay, there are no consequences "
                        "to not taking part in this study. Please enjoy the "
                        "BWise tool and stay safe. If you change your mind, "
                        "please send *Answer* to this number",
                    ]
                )
            ),
        )

    async def state_stop_assessment_reminders_confirm(self):
        assessment_reminder_name = self.user.metadata["assessment_reminder_name"]

        if assessment_reminder_name == "locus_of_control":
            return WhatsAppButtonState(
                self,
                question=self._(
                    "\n".join(
                        [
                            "Please take note👆🏽 you can't access all parts of the "
                            "Bwise bot if you don't complete the questions first.",
                            "",
                            "You can still use the menu and ask questions, but I "
                            "can't give you a personalised journey.",
                            "",
                            "*Are you sure you want to skip?*",
                        ]
                    )
                ),
                choices=[
                    Choice("skip", self._("Yes, skip it")),
                    Choice("start", self._("Start questions")),
                ],
                next={
                    "skip": "state_stop_assessment_reminders",
                    "start": f"state_{assessment_reminder_name}_assessment",
                },
                error=self._(get_generic_error()),
            )
        else:
            return WhatsAppButtonState(
                self,
                question=self._(
                    "\n".join(
                        [
                            "Just a heads up, you'll get the best info for *YOU* if "
                            "you complete the questions first.",
                            "",
                            "*Are you sure you want to skip this step?*",
                        ]
                    )
                ),
                choices=[
                    Choice("skip", self._("Yes, skip it")),
                    Choice("start", self._("Start questions")),
                ],
                next={
                    "skip": "state_stop_assessment_reminders",
                    "start": f"state_{assessment_reminder_name}_assessment",
                },
                error=self._(get_generic_error()),
            )

    async def state_stop_assessment_reminders(self):
        msisdn = utils.normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.lstrip(" + ")
        assessment_name = self.clean_name(
            self.user.metadata.get("assessment_reminder_name")
        )
        assessment_risk = (
            f"{assessment_name}_risk"
            if assessment_name != "sexual_health_literacy"
            else "sexual_health_lit_risk"
        )
        data = {
            "assessment_reminder_name": "",
            "assessment_reminder_sent": "",
            "assessment_reminder_type": "",
            assessment_risk: "high_risk",
        }  # Reset the fields

        error = await rapidpro.update_profile(whatsapp_id, data, self.user.metadata)
        if error:
            return await self.go_to_state("state_error")

        if assessment_name != "locus_of_control":
            return WhatsAppButtonState(
                self,
                question=self._(
                    "\n".join(
                        [
                            "Cool-cool.",
                            "",
                            "*What would you like to do now?*",
                        ]
                    )
                ),
                choices=[
                    Choice("menu", self._("Go to the menu")),
                    Choice("aaq", self._("Ask a question")),
                ],
                next={
                    "menu": "state_pre_mainmenu",
                    "aaq": AAQApplication.START_STATE,
                },
                error=self._(get_generic_error()),
            )
        else:
            # TODO: set push notification to no
            return WhatsAppButtonState(
                self,
                question=self._(
                    "\n".join(
                        [
                            "No problem.",
                            "",
                            "*What would you like to do now?*",
                        ]
                    )
                ),
                choices=[
                    Choice("menu", self._("Go to the menu")),
                    Choice("aaq", self._("Ask a question")),
                ],
                next={
                    "menu": "state_pre_mainmenu",
                    "aaq": AAQApplication.START_STATE,
                },
                error=self._(get_generic_error()),
            )

    async def state_reschedule_assessment_reminder(self):
        msisdn = utils.normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.lstrip(" + ")
        assessment_reminder_sent = self.user.metadata["assessment_reminder_sent"]

        assessment_name = self.clean_name(
            self.user.metadata["assessment_reminder_name"]
        )
        assessment_reminder_hours = self.user.metadata["assessment_reminder_hours"]
        assessment_reminder_type = self.user.metadata["assessment_reminder_type"]

        if (
            assessment_reminder_sent
            and assessment_name == "locus_of_control"
            and assessment_reminder_hours == "23hours"
        ):
            data = {
                "assessment_reminder_sent": "",  # Reset the field
                "assessment_reminder": get_current_datetime().isoformat(),
                "assessment_reminder_type": f"later_2 {assessment_reminder_hours}",
            }
        elif "reengagement" in assessment_reminder_type:
            data = {
                "assessment_reminder_sent": "",  # Reset the field
                "assessment_reminder": get_current_datetime().isoformat(),
                # only the reengagement flow allows the user to be reminded in 1h
                "assessment_reminder_type": f"reengagement {assessment_reminder_hours}",
            }
        else:
            data = {
                "assessment_reminder_sent": "",  # Reset the field
                "assessment_reminder": get_current_datetime().isoformat(),
                "assessment_reminder_type": f"later {assessment_reminder_hours}",
            }

        error = await rapidpro.update_profile(whatsapp_id, data, self.user.metadata)
        if error:
            return await self.go_to_state("state_error")
        if assessment_reminder_hours in ["23hours"]:
            return await self.go_to_state("state_remind_tomorrow")
        return await self.go_to_state("state_generic_what_would_you_like_to_do")

    async def state_remind_tomorrow(self):
        return WhatsAppButtonState(
            self,
            question=self._("No problem! I'll remind you tomorrow"),
            choices=[Choice("menu", "Go to main menu")],
            next="state_pre_mainmenu",
            error=self._(get_generic_error()),
        )
