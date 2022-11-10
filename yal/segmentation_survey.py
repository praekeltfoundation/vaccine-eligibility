from vaccine.base_application import BaseApplication
from vaccine.states import (
    Choice,
    CustomChoiceState,
    EndState,
    FreeText,
    MenuState,
    WhatsAppButtonState,
)
from vaccine.utils import get_display_choices
from yal.data.seqmentation_survey_questions import SURVEY_QUESTIONS
from yal.utils import BACK_TO_MAIN, GET_HELP, get_generic_error


class Application(BaseApplication):
    START_STATE = "state_start_survey"

    async def state_start_survey(self):
        question = "\n".join(
            [
                "Do you have a moment to help BWise  us with some research?",
                "*We'll give you a little something to say thanks - R30 airtime 😉💸*",
                "",
            ]
        )
        return MenuState(
            self,
            question=self._(question),
            error=self._(get_generic_error()),
            choices=[
                Choice("state_survey_question", self._("Hell yeah!")),
                Choice("state_gender", self._("Not interested")),
            ],
        )

    async def state_survey_question(self):
        metadata = self.user.metadata

        section = str(metadata.get("segment_section", "1"))

        if section not in SURVEY_QUESTIONS:
            self.save_metadata("segment_section", None)
            self.save_metadata("segment_question", None)
            self.save_metadata("segment_question_nr", None)
            return await self.go_to_state("state_survey_done")

        current_question = metadata.get("segment_question")

        if not current_question:
            current_question = SURVEY_QUESTIONS[section]["start"]
            self.save_metadata("segment_question", current_question)

        question_number = metadata.get("segment_question_nr", 1)

        total_questions = len(SURVEY_QUESTIONS[section]["questions"])

        question = SURVEY_QUESTIONS[section]["questions"][current_question]

        parts = [
            "*BWise / Survey*",
            "-----",
            f"Section {section}",
            f"{question_number}/{total_questions}",
            "",
            f"*{question['text']}*",
            "",
        ]

        if question.get("options"):
            choices = []
            for option in question["options"]:
                stub = option.replace(" ", "-").lower()
                choices.append(Choice(stub, option))

            parts.extend(
                [
                    get_display_choices(choices),
                    "",
                ]
            )

        parts.extend(
            [
                "-----",
                "*Or reply:*",
                BACK_TO_MAIN,
                GET_HELP,
            ]
        )
        question_text = self._("\n".join(parts))

        if question.get("options"):
            # TODO: Update this
            error_text = "Temp"

            return CustomChoiceState(
                self,
                question=question_text,
                error=error_text,
                choices=choices,
                next="state_survey_process_answer",
                button="See my options",
                buttons=choices,
            )
        else:
            return FreeText(
                self,
                question=question_text,
                next="state_survey_process_answer",
            )

    async def state_survey_process_answer(self):
        metadata = self.user.metadata
        answers = self.user.answers

        section = metadata.get("segment_section", 1)
        current_question = metadata.get("segment_question")
        answer = answers.get("state_survey_question")
        question_number = metadata.get("segment_question_nr", 1)

        self.save_answer(current_question, answer)

        question = SURVEY_QUESTIONS[str(section)]["questions"][current_question]

        # TODO: handle message that don't require a response

        if question["next"]:
            # TODO: handle next as a dict to branch off
            self.save_metadata("segment_question", question["next"])
            self.save_metadata("segment_question_nr", question_number + 1)
        else:
            self.save_metadata("segment_section", section + 1)
            self.save_metadata("segment_question", None)
            self.save_metadata("segment_question_nr", 1)

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
        # TODO: start the airtime flow in rapidpro
        return await self.go_to_state("state_prompt_next_action")

    async def state_prompt_next_action(self):
        def _next(choice: Choice):
            return choice.value

        choices = [
            Choice("state_aaq_start", self._("Ask a question")),
            Choice("state_pre_mainmenu", self._("Go to Main Menu")),
            Choice("state_no_airtime", self._("I didn't receive airtime")),
        ]
        question = "\n".join(
            [
                "*BWise / Survey*",
                "-----",
                "",
                "We've just sent you your airtime. Please check your airtime balance "
                "now.",
                "",
                "What would you like to do next?",
                "",
                "1. Ask a question",
                "2. Go to Main Menu",
                "3. I didn't receive airtime",
                "-----",
                "*Or reply:*",
                "*0* - 🏠Back to Main *MENU*",
                "*#* - 🆘Get *HELP*",
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
