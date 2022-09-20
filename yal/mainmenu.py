import logging

from vaccine.base_application import BaseApplication
from vaccine.states import (
    Choice,
    CustomChoiceState,
    EndState,
    FreeText,
    WhatsAppButtonState,
)
from vaccine.utils import get_display_choices
from yal import contentrepo, rapidpro, turn, utils
from yal.askaquestion import Application as AskaQuestionApplication
from yal.change_preferences import Application as ChangePreferencesApplication
from yal.pleasecallme import Application as PleaseCallMeApplication
from yal.quiz import Application as QuizApplication
from yal.servicefinder import Application as ServiceFinderApplication
from yal.utils import BACK_TO_MAIN, GET_HELP, get_current_datetime, get_generic_error

logger = logging.getLogger(__name__)


class Application(BaseApplication):
    START_STATE = "state_pre_mainmenu"

    async def update_suggested_content_details(self, level, suggested_text=None):
        msisdn = utils.normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.lstrip(" + ")
        data = {f"last_{level}_time": get_current_datetime().isoformat()}
        if suggested_text:
            data["suggested_text"] = suggested_text

        return await rapidpro.update_profile(whatsapp_id, data)

    async def reset_suggested_content_details(self):
        msisdn = utils.normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.lstrip(" + ")
        data = {
            "last_mainmenu_time": "",
            "suggested_text": "",
        }
        return await rapidpro.update_profile(whatsapp_id, data)

    async def get_suggested_choices(self, parent_topic_links={}):
        if self.user.metadata["suggested_content"] == {}:
            topics_viewed = set(
                self.user.metadata.get(
                    "topics_viewed", list(parent_topic_links.values())[:1]
                )
            )
            error, suggested_choices = await contentrepo.get_suggested_choices(
                topics_viewed
            )
            if error:
                return await self.go_to_state("state_error")
            self.save_metadata(
                "suggested_content", {c.value: c.label for c in suggested_choices}
            )
        else:
            suggested_choices = [
                Choice(k, v) for k, v in self.user.metadata["suggested_content"].items()
            ]

        return suggested_choices

    async def state_pre_mainmenu(self):
        self.save_metadata("suggested_content", {})
        return await self.go_to_state("state_mainmenu")

    async def state_mainmenu(self):
        self.save_metadata("current_menu_level", 0)

        sections = [
            (
                "*🏥 NEED HELP?*",
                [
                    Choice(PleaseCallMeApplication.START_STATE, "Please call me!"),
                    Choice(
                        ServiceFinderApplication.START_STATE,
                        "Find clinics and services",
                    ),
                ],
            )
        ]

        error, choices = await contentrepo.get_choices_by_tag("mainmenu")
        if error:
            return await self.go_to_state("state_error")

        parent_topic_links = {}
        for choice in choices:
            error, sub_choices = await contentrepo.get_choices_by_parent(choice.value)
            if error:
                return await self.go_to_state("state_error")

            for sub_choice in sub_choices:
                parent_topic_links[sub_choice.value] = choice.value

            sections.append((f"*{choice.label}*", sub_choices))

        sections.append(
            (
                "🙋🏿‍♂️ *QUESTIONS?*",
                [Choice(AskaQuestionApplication.START_STATE, "Ask a Question")],
            )
        )
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

        async def next_(choice: Choice):
            error = await self.reset_suggested_content_details()
            if error:
                return await self.go_to_state("state_error")

            if choice.value.startswith("state_"):
                return choice.value
            else:
                topics_viewed = set(self.user.metadata.get("topics_viewed", []))
                if choice.value in parent_topic_links:
                    topics_viewed.add(parent_topic_links[choice.value])
                    self.save_metadata("topics_viewed", list(topics_viewed))
                    self.save_metadata(
                        "last_topic_viewed", parent_topic_links[choice.value]
                    )

                suggested = False
                if choice.value in self.user.metadata.get("suggested_choices", {}):
                    self.save_metadata("suggested_content", {})
                    suggested = True

                self.save_metadata("is_suggested_page", suggested)

                self.save_metadata("selected_page_id", choice.value)
                self.save_metadata("current_message_id", 1)
                return "state_contentrepo_page"

        choices = []
        menu_lines = []

        i = 1
        for section_name, section_choices in sections:
            menu_lines.append(section_name)

            for choice in section_choices:
                choices.append(choice)
                menu_lines.append(f"{i}. {choice.label}")
                i += 1

            menu_lines.append("-----")

        suggested_choices = await self.get_suggested_choices(parent_topic_links)
        choices.extend(suggested_choices)
        suggested_text = "\n".join(
            [f"*{i+k}* - {c.label}" for k, c in enumerate(suggested_choices)]
        )
        error = await self.update_suggested_content_details("mainmenu", suggested_text)
        if error:
            return await self.go_to_state("state_error")

        question = self._(
            "\n".join(
                [
                    "🏡 *MAIN MENU*",
                    "How can I help you today?",
                    "-----",
                    "Send me the number of the topic you're interested in.",
                    "",
                    "\n".join(menu_lines),
                    "💡 TIP: Jump back to this menu at any time by replying 0 or MENU.",
                ]
            )
        )

        return CustomChoiceState(
            self,
            question=question,
            error=self._(
                "⚠️ This service works best when you use the numbered options "
                "available\n\n"
                "-----\n"
                "Or reply 📌 *0* to end this session and return to the main *MENU*"
            ),
            choices=choices,
            next=next_,
        )

    async def state_contentrepo_page(self):
        metadata = self.user.metadata
        page_id = metadata["selected_page_id"]
        message_id = metadata["current_message_id"]

        error, page_details = await contentrepo.get_page_details(
            self.user, page_id, message_id, metadata.get("is_suggested_page")
        )
        if error:
            return await self.go_to_state("state_error")

        self.save_metadata("title", page_details["title"])
        self.save_metadata("body", page_details["body"])
        self.save_metadata("image_path", page_details.get("image_path"))
        self.save_metadata("next_prompt", page_details.get("next_prompt"))
        self.save_metadata("parent_id", page_details["parent_id"])
        self.save_metadata("parent_title", page_details["parent_title"])
        self.save_metadata("related_pages", page_details.get("related_pages"))
        self.save_metadata("quiz_tag", page_details.get("quiz_tag"))
        self.save_metadata("quick_replies", page_details.get("quick_replies", []))
        self.save_metadata(
            "feature_redirects", page_details.get("feature_redirects", [])
        )

        menu_level = metadata["current_menu_level"] + 1
        self.save_metadata("current_menu_level", menu_level)

        if page_details["has_children"]:
            self.save_metadata("page_type", "submenu")
        else:
            self.save_metadata("page_type", "detail")

        await self.get_suggested_choices()

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
            elif choice.value == "feature_servicefinder":
                return ServiceFinderApplication.START_STATE
            elif choice.value == "feature_aaq":
                return AskaQuestionApplication.START_STATE
            elif choice.value == "feature_pleasecallme":
                return PleaseCallMeApplication.START_STATE
            elif choice.value == "feedback":
                return "state_prompt_info_found"
            elif choice.value.startswith("no"):
                return "state_get_suggestions"

            suggested = False
            if choice.value in self.user.metadata.get("suggested_choices", {}):
                self.save_metadata("suggested_content", {})
                suggested = True

            self.save_metadata("is_suggested_page", suggested)
            self.save_metadata("selected_page_id", choice.value)
            self.save_metadata("current_message_id", 1)
            return "state_contentrepo_page"

        metadata = self.user.metadata
        choices = []
        buttons = []

        if metadata["page_type"] == "submenu":
            page_id = metadata["selected_page_id"]
            error, choices = await contentrepo.get_choices_by_parent(page_id)
            buttons += choices
            if error:
                return await self.go_to_state("state_error")

        title = metadata["title"]
        body = metadata["body"]
        next_prompt = metadata.get("next_prompt")
        quiz_tag = metadata.get("quiz_tag")
        quick_replies = metadata.get("quick_replies", [])

        parts = [
            title,
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
                buttons.append(Choice(value, label))
        elif quiz_tag:
            choices.append(Choice("quiz", "Yes (take the quiz)"))
            buttons.append(Choice("quiz", "Yes (take the quiz)"))

        for quick_reply in quick_replies:
            stub = quick_reply.replace(" ", "-").lower()
            choices.append(Choice(stub, quick_reply))
            buttons.append(Choice(stub, quick_reply))

        feature_redirects = metadata.get("feature_redirects", [])
        if "servicefinder" in feature_redirects:
            choices.append(Choice("feature_servicefinder", "Find a clinic"))
            buttons.append(Choice("feature_servicefinder", "Find a clinic"))
        if "aaq" in feature_redirects:
            choices.append(Choice("feature_aaq", "Ask a Question"))
            buttons.append(Choice("feature_aaq", "Ask a Question"))
        if "pleasecallme" in feature_redirects:
            choices.append(Choice("feature_pleasecallme", "Call Lovelife"))
            buttons.append(Choice("feature_pleasecallme", "Call Lovelife"))

        if next_prompt is None and metadata["page_type"] == "detail":
            choices.append(Choice("feedback", "Pls give us feedback"))
            buttons.append(Choice("feedback", "Pls give us feedback"))

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
        if menu_level >= 2:
            back_title = metadata["parent_title"]
            back_menu_item = f"{len(choices) + 1}. ⬅️ {back_title}"

            choices.append(Choice("back", f"⬅️ {back_title}"))

        parts.extend(
            [
                "-----",
                "*Or reply:*",
                back_menu_item,
                BACK_TO_MAIN,
                GET_HELP,
            ]
        )
        question = self._("\n".join([part for part in parts if part is not None]))

        i = len(choices) + 1
        suggested_choices = await self.get_suggested_choices()
        choices.extend(suggested_choices)
        suggested_text = "\n".join(
            [f"*{i+k}* - {c.label}" for k, c in enumerate(suggested_choices)]
        )
        self.save_metadata(
            "suggested_choices", [str(i + k) for k in range(len(suggested_choices))]
        )

        error = await self.update_suggested_content_details("main", suggested_text)
        if error:
            return await self.go_to_state("state_error")

        helper_metadata = {}
        if "image_path" in metadata and metadata["image_path"]:
            helper_metadata["image"] = metadata["image_path"]
            buttons = None
        else:
            buttons = [Choice(c.value, c.label[:20]) for c in buttons]

        return CustomChoiceState(
            self,
            question=question,
            error=self._(get_generic_error()),
            choices=choices,
            next=next_,
            helper_metadata=helper_metadata,
            button="See my options",
            buttons=buttons,
        )

    async def state_get_suggestions(self):
        topics_viewed = [self.user.metadata["last_topic_viewed"]]
        error, suggested_choices = await contentrepo.get_suggested_choices(
            topics_viewed
        )
        if error:
            return await self.go_to_state("state_error")
        self.save_metadata(
            "suggested_content", {c.value: c.label for c in suggested_choices}
        )
        return await self.go_to_state("state_display_suggestions")

    async def state_display_suggestions(self):
        async def next_(choice: Choice):
            if choice.value == "back":
                return "state_back"
            self.save_metadata("selected_page_id", choice.value)
            self.save_metadata("current_message_id", 1)
            return "state_contentrepo_page"

        metadata = self.user.metadata

        choices = [
            Choice(k, v) for k, v in self.user.metadata["suggested_content"].items()
        ]

        parts = [
            "Okay, what would you like to talk about?",
            "",
            get_display_choices(choices),
        ]

        back_menu_item = None
        menu_level = metadata["current_menu_level"]
        if menu_level >= 2:
            back_title = metadata["parent_title"]
            back_menu_item = f"{len(choices) + 1}. ⬅️ {back_title}"

            choices.append(Choice("back", f"⬅️ {back_title}"))

        parts.extend(
            [
                "-----",
                "*Or reply:*",
                back_menu_item,
                BACK_TO_MAIN,
                GET_HELP,
            ]
        )

        question = self._("\n".join([part for part in parts if part is not None]))

        return CustomChoiceState(
            self,
            question=question,
            error=self._(
                "⚠️ This service works best when you use the numbered options "
                "available\n"
            ),
            choices=choices,
            next=next_,
            button="See my options",
            buttons=[
                Choice(k, v) for k, v in self.user.metadata["suggested_content"].items()
            ],
        )

    async def state_back(self):
        menu_level = self.user.metadata["current_menu_level"]
        page_id = self.user.metadata["parent_id"]

        self.save_metadata("selected_page_id", page_id)
        self.save_metadata("current_message_id", 1)
        self.save_metadata("current_menu_level", menu_level - 2)

        return await self.go_to_state("state_contentrepo_page")

    async def state_prompt_info_found(self):
        question = self._(
            "\n".join(
                [
                    "Did you find the info you were looking for?",
                    "",
                    "Reply:",
                    "1. 👍🏾 Yes",
                    "2. 👎🏾 No",
                    "",
                    "--",
                    "",
                    BACK_TO_MAIN,
                    GET_HELP,
                ]
            )
        )
        return WhatsAppButtonState(
            self,
            question=question,
            choices=[
                Choice("yes", "Yes", additional_keywords="👍🏾"),
                Choice("no", "No", additional_keywords="👎🏾"),
            ],
            error=self._(get_generic_error()),
            next={
                "yes": "state_prompt_info_useful",
                "no": "state_prompt_not_found_comment",
            },
        )

    async def state_prompt_not_found_comment(self):
        return FreeText(
            self,
            question=self._(
                "\n".join(
                    [
                        "Hmm, I'm sorry about that.😕",
                        "Please tell me a bit more about what info you're looking for "
                        "so that I can help you next time.",
                    ]
                )
            ),
            next="state_label_comment",
        )

    async def state_label_comment(self):
        error = await turn.label_message(self.inbound.message_id, "Priority Question")
        if error:
            return await self.go_to_state("state_error")
        return await self.go_to_state("state_feedback_completed")

    async def state_feedback_completed(self):
        return EndState(
            self,
            text=self._(
                "Ok got it. Thank you for the feedback, I'm working on it already👍🏾."
            ),
        )

    async def state_prompt_info_useful(self):
        question = self._(
            "\n".join(
                [
                    "Great.😊 Was the info useful?",
                    "",
                    "Reply:",
                    "1. 👍🏾 Yes",
                    "2. 👎🏾 No",
                    "",
                    "--",
                    "",
                    BACK_TO_MAIN,
                    GET_HELP,
                ]
            )
        )
        return WhatsAppButtonState(
            self,
            question=question,
            choices=[
                Choice("yes", "Yes", additional_keywords="👍🏾"),
                Choice("no", "No", additional_keywords="👎🏾"),
            ],
            error=self._(get_generic_error()),
            next={
                "yes": "state_submit_feedback",
                "no": "state_prompt_feedback_comment",
            },
        )

    async def state_prompt_feedback_comment(self):
        return FreeText(
            self,
            question=self._(
                "\n".join(
                    [
                        "Hmm, I'm sorry about that.😕",
                        "Please tell me a bit more about what info you're looking for "
                        "so that I can help you next time.",
                    ]
                )
            ),
            next="state_submit_feedback",
        )

    async def state_submit_feedback(self):
        metadata = self.user.metadata
        helpful = self.user.answers["state_prompt_info_useful"] == "yes"
        comment = (
            "" if helpful else self.user.answers.get("state_prompt_feedback_comment")
        )

        error = await contentrepo.add_page_rating(
            self.user, metadata["selected_page_id"], helpful, comment
        )
        if error:
            return await self.go_to_state("state_error")

        if not helpful:
            return await self.go_to_state("state_label_comment")

        return EndState(
            self,
            text=self._(
                "\n".join(
                    [
                        "I'm so happy I could help you learn more about you sexual "
                        "health and pleasure. 🙌🏾😎",
                        "",
                        "--",
                        "",
                        BACK_TO_MAIN,
                        GET_HELP,
                    ]
                )
            ),
        )
