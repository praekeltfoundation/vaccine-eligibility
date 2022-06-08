import logging

from vaccine.base_application import BaseApplication
from vaccine.states import Choice, ChoiceState, EndState, SectionedChoiceState
from yal import contentrepo
from yal.change_preferences import Application as ChangePreferencesApplication

logger = logging.getLogger(__name__)


class Application(BaseApplication):
    START_STATE = "state_mainmenu"

    async def state_mainmenu(self):
        async def next_(choice: Choice):
            if choice.value.startswith("state_"):
                return choice.value
            else:
                self.save_answer("selected_page_id", choice.value)
                self.save_answer("current_message_id", 1)
                return "state_contentrepo_page"

        sections = [
            (
                "*🏥 NEED HELP?*",
                [
                    Choice("state_please_call_me", "Please call me!"),
                    Choice("state_clinic_finder", "Find clinics and services"),
                ],
            )
        ]

        error, choices = await contentrepo.get_choices_by_tag("mainmenu")
        if error:
            return await self.go_to_state("state_error")

        for choice in choices:
            error, sub_choices = await contentrepo.get_choices_by_parent(choice.value)
            if error:
                return await self.go_to_state("state_error")

            sections.append((f"*{choice.label}*", sub_choices))

        sections.append(("🙋🏿‍♂️ *QUESTIONS?*", [Choice("state_faqs", "FAQs")]))
        sections.append(
            (
                "*⚙️ CHAT SETTINGS*",
                [
                    Choice(
                        ChangePreferencesApplication.START_STATE,
                        "Change Profile",
                    ),
                ],
            )
        )

        question = self._(
            "\n".join(
                [
                    "🏡 *MAIN MENU*",
                    "How can I help you today?",
                    "-----",
                    "Send me the number of the topic you're interested in.",
                    "",
                ]
            )
        )

        return SectionedChoiceState(
            self,
            question=question,
            footer="💡 TIP: Jump back to this menu at any time by replying 0 or MENU.",
            error=self._(
                "⚠️ This service works best when you use the numbered options "
                "available\n"
            ),
            error_footer=self._(
                "\n"
                "-----\n"
                "Or reply 📌 *0* to end this session and return to the main *MENU*"
            ),
            next=next_,
            sections=sections,
            separator="-----",
        )

    async def state_contentrepo_page(self):
        page_id = self.user.answers["selected_page_id"]
        message_id = self.user.answers["current_message_id"]
        error, page_details = await contentrepo.get_page_details(
            self.user, page_id, message_id
        )
        if error:
            return await self.go_to_state("state_error")

        self.save_answer("title", page_details["title"])
        self.save_answer("subtitle", page_details["subtitle"])
        self.save_answer("body", page_details["body"])
        self.save_answer("image_path", page_details.get("image_path"))

        if page_details["has_children"]:
            return await self.go_to_state("state_submenu")
        elif "next_prompt" in page_details:
            self.save_answer("next_prompt", page_details["next_prompt"])
            return await self.go_to_state("state_detail_with_next")
        else:
            return await self.go_to_state("state_detail")

    async def state_submenu(self):
        async def next_(choice: Choice):
            self.save_answer("selected_page_id", choice.value)
            self.save_answer("current_message_id", 1)
            return "state_contentrepo_page"

        answers = self.user.answers

        page_id = answers["selected_page_id"]
        error, choices = await contentrepo.get_choices_by_parent(page_id)
        if error:
            return await self.go_to_state("state_error")

        title = answers["title"]
        subtitle = answers["subtitle"]
        body = answers["body"]

        parts = [f"*{title}*", subtitle, "-----", "", body, ""]
        question = self._("\n".join([part for part in parts if part is not None]))

        metadata = {}
        if "image_path" in answers and answers["image_path"]:
            metadata["image"] = contentrepo.get_url(answers["image_path"])

        return ChoiceState(
            self,
            question=question,
            error=self._(
                "⚠️ This service works best when you use the numbered options "
                "available\n"
            ),
            choices=choices,
            next=next_,
            footer=self._(
                "\n".join(
                    [
                        "",
                        "-----",
                        "Or reply:",
                        "",
                        "0. 🏠 Back to Main MENU",
                        "# 🆘 Get HELP",
                    ]
                )
            ),
            helper_metadata=metadata,
        )

    async def state_detail_with_next(self):
        async def next_(choice: Choice):
            message_id = self.user.answers["current_message_id"]
            self.save_answer("current_message_id", message_id + 1)
            return "state_contentrepo_page"

        answers = self.user.answers
        title = answers["title"]
        subtitle = answers["subtitle"]
        body = answers["body"]
        next_prompt = answers["next_prompt"]

        parts = [f"*{title}*", subtitle, "-----", "", body, ""]
        question = self._("\n".join([part for part in parts if part is not None]))

        metadata = {}
        if "image_path" in answers and answers["image_path"]:
            metadata["image"] = contentrepo.get_url(answers["image_path"])

        return ChoiceState(
            self,
            question=question,
            error=self._(
                "⚠️ This service works best when you use the numbered options "
                "available\n"
            ),
            choices=[Choice("next", next_prompt)],
            buttons=[Choice("next", next_prompt)],
            next=next_,
            footer=self._(
                "\n".join(
                    [
                        "",
                        "-----",
                        "Or reply:",
                        "",
                        "0. 🏠 Back to Main MENU",
                        "# 🆘 Get HELP",
                    ]
                )
            ),
            helper_metadata=metadata,
        )

    async def state_detail(self):
        answers = self.user.answers
        title = answers["title"]
        subtitle = answers["subtitle"]
        body = answers["body"]

        parts = [
            f"*{title}*",
            subtitle,
            "-----",
            "",
            body,
            "",
            "-----",
            "Or reply:",
            "",
            "0. 🏠 Back to Main MENU",
            "# 🆘 Get HELP",
        ]
        question = self._("\n".join([part for part in parts if part is not None]))

        metadata = {}
        if "image_path" in answers and answers["image_path"]:
            metadata["image"] = contentrepo.get_url(answers["image_path"])

        return EndState(self, question, next=self.START_STATE, helper_metadata=metadata)

    async def state_please_call_me(self):
        return EndState(
            self,
            self._("TODO: Please Call Me"),
            next=self.START_STATE,
        )

    async def state_clinic_finder(self):
        return EndState(
            self,
            self._("TODO: Clinic finder"),
            next=self.START_STATE,
        )
