import logging

from vaccine.states import Choice, ChoiceState, EndState, SectionedChoiceState
from yal import contentrepo
from yal.yal_base_application import YalBaseApplication

logger = logging.getLogger(__name__)


class Application(YalBaseApplication):
    START_STATE = "state_mainmenu"

    async def state_mainmenu(self):
        async def next_(choice: Choice):
            if choice.value.startswith("state_"):
                return choice.value
            else:
                self.save_answer("selected_page_id", choice.value)
                return "state_contentrepo_page"

        sections = [
            (
                "*NEED HELP OR ADVICE?*",
                [
                    Choice("state_please_call_me", "📞 Please call me!"),
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

        sections.append(
            ("*WHAT's EVERYONE ELSE ASKING?*", [Choice("state_faqs", "🤔 FAQs")])
        )
        sections.append(
            (
                "*CHAT SETTINGS*",
                [
                    Choice("state_change_info", "⚙️ Change/Update Your Personal Info"),
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
        error, page_details = await contentrepo.get_page_details(page_id)
        if error:
            return await self.go_to_state("state_error")

        self.save_answer("title", page_details["title"])
        self.save_answer("body", page_details["body"])

        if page_details["has_children"]:
            return await self.go_to_state("state_submenu")
        else:
            return await self.go_to_state("state_detail")

    async def state_submenu(self):
        async def next_(choice: Choice):
            self.save_answer("selected_page_id", choice.value)
            return "state_contentrepo_page"

        page_id = self.user.answers["selected_page_id"]
        error, choices = await contentrepo.get_choices_by_parent(page_id)
        if error:
            return await self.go_to_state("state_error")

        title = self.user.answers["title"]
        body = self.user.answers["body"]
        question = self._("\n".join([f"*{title}*", "-----", "", body, ""]))

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
        )

    async def state_detail(self):
        title = self.user.answers["title"]
        body = self.user.answers["body"]
        question = self._(
            "\n".join(
                [
                    f"*{title}*",
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
            )
        )

        return EndState(
            self,
            question,
            next=self.START_STATE,
        )

    async def state_please_call_me(self):
        return EndState(
            self,
            self._("TODO: Please Call Me"),
            next=self.START_STATE,
        )

    async def state_change_info(self):
        return EndState(
            self,
            self._("TODO: Change info/preferences"),
            next=self.START_STATE,
        )
