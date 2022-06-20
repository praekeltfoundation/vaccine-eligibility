import asyncio
import logging

from vaccine.base_application import BaseApplication
from vaccine.states import Choice, ChoiceState, EndState
from yal import contentrepo

logger = logging.getLogger(__name__)


class Application(BaseApplication):
    START_STATE = "state_quiz_start"

    async def state_quiz_start(self):
        self.save_metadata("quiz_sequence", 1)
        self.save_metadata("quiz_score", 0)
        return await self.go_to_state("state_quiz_question")

    async def state_quiz_question(self):
        async def next_(choice: Choice):
            if choice.value == "callme":
                return await self.go_to_state("state_please_call")
            elif choice.value == "menu":
                return await self.go_to_state("state_mainmenu")
            elif choice.value == "redo":
                return await self.go_to_state("state_quiz_start")

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
            # TODO - send results message here
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
        subtitle = page_details["subtitle"]
        body = page_details["body"]

        parts = [
            f"*{title}*",
            subtitle,
            "-----",
            "",
            body,
            "",
        ]
        question = self._("\n".join([part for part in parts if part is not None]))

        helper_metadata = {}
        if page_details.get("image_path"):
            helper_metadata["image"] = contentrepo.get_url(metadata["image_path"])

        return ChoiceState(
            self,
            question=question,
            choices=choices,
            footer=self._(
                "\n".join(
                    [
                        "",
                        "-----",
                        "*Or reply:*",
                        "0. 🏠 Back to Main MENU",
                        "# 🆘 Get HELP",
                    ]
                )
            ),
            next=next_,
            error=self._("TODO"),
            error_footer=self._("\n" "todo."),
            helper_metadata=helper_metadata,
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
            helper_metadata["image"] = contentrepo.get_url(metadata["image_path"])

        await self.worker.publish_message(
            self.inbound.reply(
                self._(page_details["body"]),
                helper_metadata=helper_metadata,
            )
        )
        await asyncio.sleep(0.5)

        self.save_metadata("quiz_sequence", metadata["quiz_sequence"] + 1)

        return await self.go_to_state("state_quiz_question")

    async def state_please_call(self):
        return EndState(
            self,
            self._("TODO: Please Call Me"),
            next=self.START_STATE,
        )
