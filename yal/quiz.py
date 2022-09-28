import asyncio
import logging

from vaccine.base_application import BaseApplication
from vaccine.states import Choice, CustomChoiceState, WhatsAppButtonState
from vaccine.utils import get_display_choices
from yal import contentrepo
from yal.pleasecallme import Application as PleaseCallMeApplication
from yal.utils import BACK_TO_MAIN, GET_HELP, get_generic_error

logger = logging.getLogger(__name__)


class Application(BaseApplication):
    START_STATE = "state_quiz_start"

    async def state_quiz_start(self):
        self.save_metadata("quiz_sequence", 1)
        self.save_metadata("quiz_score", 0)
        self.save_metadata("quiz_result_sent", False)
        return await self.go_to_state("state_quiz_question")

    async def state_quiz_question(self):
        async def next_(choice: Choice):
            if choice.value == "callme":
                return PleaseCallMeApplication.START_STATE
            elif choice.value == "menu":
                return "state_pre_mainmenu"
            elif choice.value == "redo":
                return "state_quiz_start"

            self.save_metadata("selected_answer_id", choice.value)
            return "state_quiz_answer"

        metadata = self.user.metadata

        quiz_tag = metadata["quiz_tag"]
        quiz_sequence = metadata["quiz_sequence"]

        tag = f"{quiz_tag}_{quiz_sequence}"

        error, page_details = await contentrepo.get_page_detail_by_tag(self.user, tag)
        if error:
            return await self.go_to_state("state_error")

        if "quiz_end" in page_details["tags"]:
            if not metadata.get("quiz_result_sent"):
                pass_percentage = 70
                for tag in page_details["tags"]:
                    if tag.startswith("pass_percentage_"):
                        pass_percentage = int(tag.replace("pass_percentage_", ""))

                score = metadata["quiz_score"]
                total = metadata["quiz_sequence"] - 1

                result_tag = f"{quiz_tag}_pass"
                if (score / total) * 100 < pass_percentage:
                    result_tag = f"{quiz_tag}_fail"

                error, result_page_details = await contentrepo.get_page_detail_by_tag(
                    self.user, result_tag
                )
                if error:
                    return await self.go_to_state("state_error")

                helper_metadata = {}
                if result_page_details.get("image_path"):
                    helper_metadata["image"] = result_page_details["image_path"]

                result_msg = result_page_details["body"].replace("[SCORE]", str(score))
                await self.worker.publish_message(
                    self.inbound.reply(
                        self._(result_msg),
                        helper_metadata=helper_metadata,
                    )
                )
                await asyncio.sleep(0.5)
                self.save_metadata("quiz_result_sent", True)

            choices = [
                Choice("callme", "Chat with a loveLife counsellor"),
                Choice("menu", "Not right now"),
                Choice("redo", "Redo Quiz"),
            ]
        else:
            error, choices = await contentrepo.get_choices_by_parent(
                page_details["page_id"]
            )
            if error:
                return await self.go_to_state("state_error")

        title = page_details["title"]
        body = page_details["body"]

        parts = [
            title,
            "-----",
            "",
            body,
            "",
            get_display_choices(choices),
            "",
            "-----",
            "*Or reply:*",
            BACK_TO_MAIN,
            GET_HELP,
        ]

        question = self._("\n".join([part for part in parts if part is not None]))

        helper_metadata = {}
        if page_details.get("image_path"):
            helper_metadata["image"] = page_details["image_path"]

        buttons = [Choice(c.value, c.label[:20]) for c in choices]

        return CustomChoiceState(
            self,
            question=question,
            choices=choices,
            next=next_,
            error=self._(get_generic_error()),
            helper_metadata=helper_metadata,
            button="Answer",
            buttons=buttons,
        )

    async def state_quiz_answer(self):
        metadata = self.user.metadata
        page_id = metadata["selected_answer_id"]
        error, page_details = await contentrepo.get_page_details(self.user, page_id, 1)
        if error:
            return await self.go_to_state("state_error")

        score = metadata["quiz_score"]
        for tag in page_details["tags"]:
            if tag.startswith("score_"):
                score += int(tag.replace("score_", ""))
        self.save_metadata("quiz_score", score)

        helper_metadata = {}
        if page_details.get("image_path"):
            helper_metadata["image"] = page_details["image_path"]

        self.save_metadata("quiz_sequence", metadata["quiz_sequence"] + 1)

        return WhatsAppButtonState(
            self,
            question=page_details["body"],
            choices=[
                Choice("next_question", "Next question"),
            ],
            error=self._(get_generic_error()),
            next="state_quiz_question",
        )
