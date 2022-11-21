import asyncio

from vaccine.base_application import BaseApplication
from vaccine.states import (
    Choice,
    ChoiceState,
    CustomChoiceState,
    EndState,
    FreeText,
    WhatsAppButtonState,
)
from yal import config, rapidpro, utils
from yal.data.seqmentation_survey_questions import SURVEY_QUESTIONS
from yal.utils import BACK_TO_MAIN, GET_HELP, get_generic_error


class Application(BaseApplication):
    START_STATE = "state_start_survey"
    DECLINE_STATE = "state_survey_decline"
    COMPLETED_STATE = "state_survey_already_completed"

    async def state_survey_already_completed(self):
        def _next(choice: Choice):
            return choice.value

        choices = [
            Choice("state_aaq_start", self._("Ask a question")),
            Choice("state_pre_mainmenu", self._("Go to Main Menu")),
        ]
        question = "\n".join(
            [
                "Hmm, 🤔 looks like you've already completed this survey.",
                "",
                "Thanks for your input, we really appreciate it.",
                "",
                "What would you like to do next?",
                "",
                "1. Ask a question",
                "2. Go to Main Menu",
            ]
        )
        return CustomChoiceState(
            self,
            question=self._(question),
            error=self._(get_generic_error()),
            choices=choices,
            next=_next,
            button="See my options",
            buttons=choices,
        )

    async def state_survey_decline(self):
        def _next(choice: Choice):
            return choice.value

        choices = [
            Choice("state_aaq_start", self._("Ask a question")),
            Choice("state_pre_mainmenu", self._("Go to Main Menu")),
        ]
        question = "\n".join(
            [
                "*No problem and no pressure!* 😎",
                "",
                "What would you like to do next?",
                "",
                "1. Ask a question",
                "2. Go to Main Menu",
                "-----",
                "*Or reply:*",
                BACK_TO_MAIN,
            ]
        )
        return CustomChoiceState(
            self,
            question=self._(question),
            error=self._(get_generic_error()),
            choices=choices,
            next=_next,
            button="See my options",
            buttons=choices,
        )

    async def state_start_survey(self):
        msg = self._(
            "\n".join(
                [
                    "*Awesome, let's get straight into it.*",
                    "",
                    "There are 4 sections to the survey. Each section should take "
                    "around *5-10 min* to complete.",
                    "",
                    "-----",
                    "*Or reply:*",
                    BACK_TO_MAIN,
                ]
            )
        )
        await self.publish_message(msg)
        await asyncio.sleep(0.5)

        return await self.go_to_state("state_survey_question")

    async def state_survey_question(self):
        metadata = self.user.metadata

        section = str(metadata.get("segment_section", "1"))

        if section not in SURVEY_QUESTIONS:
            self.delete_metadata("segment_section")
            self.delete_metadata("segment_question")
            self.delete_metadata("segment_question_nr")
            return await self.go_to_state("state_survey_done")

        current_question = metadata.get("segment_question")

        if not current_question:
            current_question = SURVEY_QUESTIONS[section]["start"]
            self.save_metadata("segment_question", current_question)

        question_number = metadata.get("segment_question_nr", 1)

        total_questions = len(SURVEY_QUESTIONS[section]["questions"])

        question = SURVEY_QUESTIONS[section]["questions"][current_question]
        question_type = question.get("type", "choice")

        if question_type == "info":
            await self.publish_message(question["text"])
            await asyncio.sleep(0.5)
            return await self.go_to_state("state_survey_process_answer")

        header = "\n".join(
            [
                "*BWise / Survey*",
                "-----",
                f"Section {section}",
                f"{question_number}/{total_questions}",
                "",
            ]
        )
        footer = "\n".join(
            [
                "",
                "-----",
                "*Or reply:*",
                BACK_TO_MAIN,
                GET_HELP,
            ]
        )

        if question_type == "choice":
            choices = []
            for option in question["options"]:
                if isinstance(option, tuple):
                    stub, option = option
                else:
                    stub = option.replace(" ", "_").lower()
                choices.append(Choice(stub, option))

            return ChoiceState(
                self,
                question=question["text"] + "\n",
                header=header,
                footer=footer,
                error=get_generic_error() + "\n",
                error_footer=footer,
                choices=choices,
                next="state_survey_process_answer",
                override_answer_name=current_question,
            )
        else:
            return FreeText(
                self,
                question=question["text"],
                header=header,
                footer=footer,
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

    async def state_survey_done(self):
        question = self._(
            "\n".join(
                [
                    "*BWise / Survey*",
                    "-----",
                    "",
                    "🥳 *CONGRATULATIONS! YOU'RE 💯DONE!*",
                    "",
                    "Thank you so much for helping us out. All that's left to do now "
                    "is for you to *grab your R30 airtime!* 📲",
                    "",
                    "We'll send you a message once the airtime has been sent. This "
                    "may take a few minutes.",
                    "",
                    "-----",
                    "*Or reply:*",
                    BACK_TO_MAIN,
                    GET_HELP,
                ]
            )
        )
        return WhatsAppButtonState(
            self,
            question=question,
            choices=[
                Choice("get_airtime", self._("Get Airtime")),
            ],
            error=get_generic_error(),
            next={"get_airtime": "state_trigger_airtime_flow"},
        )

    async def state_trigger_airtime_flow(self):
        msisdn = utils.normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.lstrip(" + ")
        error = await rapidpro.start_flow(whatsapp_id, config.SEGMENT_AIRTIME_FLOW_UUID)
        if error:
            return await self.go_to_state("state_error")

        return await self.go_to_state("state_prompt_next_action")

    async def state_prompt_next_action(self):
        def _next(choice: Choice):
            return choice.value

        choices = [
            Choice("state_aaq_start", self._("Ask a question")),
            Choice("state_pre_mainmenu", self._("Go to Main Menu")),
            Choice("state_no_airtime", self._("I didn't receive airtime")),
        ]
        header = "\n".join(["*BWise / Survey*", "-----", ""])
        question = "\n".join(
            [
                "We've just sent you your airtime. Please check your airtime balance "
                "now.",
                "",
                "*What would you like to do next?*",
                "",
            ]
        )
        footer = "\n".join(
            [
                "",
                "-----",
                "*Or reply:*",
                "*0* - 🏠Back to Main *MENU*",
                "*#* - 🆘Get *HELP*",
            ]
        )
        return ChoiceState(
            self,
            header=header,
            question=self._(question),
            footer=footer,
            error=self._(get_generic_error()),
            choices=choices,
            next=_next,
        )

    async def state_no_airtime(self):
        # TODO: label question for helpdesk ??
        return EndState(
            self,
            text=self._(
                "\n".join(
                    [
                        "*BWise / Survey*",
                        "-----",
                        "",
                        "Thank you for letting us know. We'll look into it and get "
                        "back to you.",
                        "-----",
                        "*Or reply:*",
                        BACK_TO_MAIN,
                        GET_HELP,
                    ]
                )
            ),
        )
