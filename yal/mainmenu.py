import logging

from vaccine.base_application import BaseApplication
from vaccine.states import Choice, ChoiceState, EndState, SectionedChoiceState
from vaccine.utils import get_display_choices
from yal import contentrepo
from yal.change_preferences import Application as ChangePreferencesApplication
from yal.quiz import Application as QuizApplication

logger = logging.getLogger(__name__)


class CustomChoiceState(ChoiceState):
    async def display(self, message):
        helper_metadata = self.helper_metadata or {}
        if self.buttons:
            helper_metadata["buttons"] = [choice.label for choice in self.buttons]

        return self.app.send_message(self.question, helper_metadata=helper_metadata)


class Application(BaseApplication):
    START_STATE = "state_mainmenu"

    async def state_mainmenu(self):
        async def next_(choice: Choice):
            if choice.value.startswith("state_"):
                return choice.value
            else:
                self.save_metadata("selected_page_id", choice.value)
                self.save_metadata("current_message_id", 1)
                return "state_contentrepo_page"

        self.save_metadata("current_menu_level", 0)

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
        metadata = self.user.metadata
        page_id = metadata["selected_page_id"]
        message_id = metadata["current_message_id"]

        error, page_details = await contentrepo.get_page_details(
            self.user, page_id, message_id
        )
        if error:
            return await self.go_to_state("state_error")

        self.save_metadata("title", page_details["title"])
        self.save_metadata("subtitle", page_details["subtitle"])
        self.save_metadata("body", page_details["body"])
        self.save_metadata("image_path", page_details.get("image_path"))
        self.save_metadata("next_prompt", page_details.get("next_prompt"))
        self.save_metadata("parent_id", page_details["parent_id"])
        self.save_metadata("parent_title", page_details["parent_title"])
        self.save_metadata("related_pages", page_details.get("related_pages"))
        self.save_metadata("quiz_tag", page_details.get("quiz_tag"))

        menu_level = metadata["current_menu_level"] + 1
        self.save_metadata("current_menu_level", menu_level)

        if page_details["has_children"]:
            self.save_metadata("page_type", "submenu")
        else:
            self.save_metadata("page_type", "detail")

        return await self.go_to_state("state_display_page")

    async def state_display_page(self):
        async def next_(choice: Choice):
            if choice.value == "back":
                return "state_back"
            elif choice.value == "next":
                message_id = self.user.metadata["current_message_id"]
                self.save_metadata("current_message_id", message_id + 1)
                return "state_contentrepo_page"
            elif choice.value == "quiz":
                return QuizApplication.START_STATE

            self.save_metadata("selected_page_id", choice.value)
            self.save_metadata("current_message_id", 1)
            return "state_contentrepo_page"

        metadata = self.user.metadata
        choices = []
        buttons = []

        if metadata["page_type"] == "submenu":
            page_id = metadata["selected_page_id"]
            error, choices = await contentrepo.get_choices_by_parent(page_id)
            if error:
                return await self.go_to_state("state_error")

        title = metadata["title"]
        subtitle = metadata["subtitle"]
        body = metadata["body"]
        next_prompt = metadata.get("next_prompt")
        quiz_tag = metadata.get("quiz_tag")

        parts = [
            f"*{title}*",
            subtitle,
            "-----",
            "",
            body,
            "",
        ]

        if next_prompt:
            choices.append(Choice("next", next_prompt))
            buttons.append(Choice("next", next_prompt))
        elif metadata["related_pages"]:
            for value, label in metadata["related_pages"].items():
                choices.append(Choice(value, label))
        elif quiz_tag:
            choices.append(Choice("quiz", "Yes (take the quiz)"))
            buttons.append(Choice("quiz", "Yes (take the quiz)"))

        if choices:
            parts.extend(
                [
                    get_display_choices(choices),
                    "",
                ]
            )
        elif quiz_tag:
            choices.append(Choice("quiz", "Yes (take the quiz)"))
            buttons.append(Choice("quiz", "Yes (take the quiz)"))

            parts.extend(
                [
                    get_display_choices(choices),
                    "",
                ]
            )

        back_menu_item = None
        menu_level = metadata["current_menu_level"]
        if menu_level > 2:
            back_title = metadata["parent_title"]
            back_menu_item = f"{len(choices) + 1}. ⬅️{back_title}"

            choices.append(Choice("back", f"⬅️ {back_title}"))

        parts.extend(
            [
                "-----",
                "*Or reply:*",
                back_menu_item,
                "0. 🏠 Back to Main MENU",
                "# 🆘 Get HELP",
            ]
        )
        question = self._("\n".join([part for part in parts if part is not None]))

        helper_metadata = {}
        if "image_path" in metadata and metadata["image_path"]:
            helper_metadata["image"] = contentrepo.get_url(metadata["image_path"])

        return CustomChoiceState(
            self,
            question=question,
            error=self._(
                "⚠️ This service works best when you use the numbered options "
                "available\n"
            ),
            choices=choices,
            next=next_,
            helper_metadata=helper_metadata,
        )

    async def state_back(self):
        menu_level = self.user.metadata["current_menu_level"]
        page_id = self.user.metadata["parent_id"]

        self.save_metadata("selected_page_id", page_id)
        self.save_metadata("current_message_id", 1)
        self.save_metadata("current_menu_level", menu_level - 2)

        return await self.go_to_state("state_contentrepo_page")

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
