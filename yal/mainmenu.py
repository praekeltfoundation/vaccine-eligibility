import logging
from datetime import timedelta

from vaccine.base_application import BaseApplication
from vaccine.states import Choice, CustomChoiceState, WhatsAppListState
from vaccine.utils import get_display_choices
from yal import contentrepo, rapidpro, utils
from yal.askaquestion import Application as AskaQuestionApplication
from yal.change_preferences import Application as ChangePreferencesApplication
from yal.pleasecallme import Application as PleaseCallMeApplication
from yal.quiz import Application as QuizApplication
from yal.servicefinder import Application as ServiceFinderApplication
from yal.utils import BACK_TO_MAIN, GET_HELP, get_current_datetime, get_generic_error

logger = logging.getLogger(__name__)


class Application(BaseApplication):
    START_STATE = "state_pre_mainmenu"
    PUSH_MESSAGE_RELATED_STATE = "state_prep_push_msg_related_page"

    async def update_suggested_content_details(self, level, suggested_text=None):
        msisdn = utils.normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.lstrip(" + ")
        data = {f"last_{level}_time": get_current_datetime().isoformat()}
        if suggested_text:
            data["suggested_text"] = suggested_text

        return await rapidpro.update_profile(whatsapp_id, data, self.user.metadata)

    async def reset_suggested_content_details(self):
        msisdn = utils.normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.lstrip(" + ")
        data = {
            "last_mainmenu_time": "",
            "suggested_text": "",
        }
        return await rapidpro.update_profile(whatsapp_id, data, self.user.metadata)

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

    async def get_privacy_reminder_sent(self, whatsapp_id):
        privacy_reminder_sent = self.user.metadata.get("privacy_reminder_sent")
        if not privacy_reminder_sent:
            error = await rapidpro.update_profile(
                whatsapp_id, {"privacy_reminder_sent": "True"}, self.user.metadata
            )
            if error:
                return await self.go_to_state("state_error")
        return bool(privacy_reminder_sent)

    async def state_pre_mainmenu(self):
        self.save_metadata("suggested_content", {})
        return await self.go_to_state("state_mainmenu")

    async def state_mainmenu(self):
        self.save_metadata("current_menu_level", 0)

        error, submenu_choices = await contentrepo.get_choices_by_tag("help_submenu")
        if error:
            return await self.go_to_state("state_error")

        sections = [
            (
                "🏥 *NEED HELP?*",
                [
                    Choice(PleaseCallMeApplication.START_STATE, "Talk to a counsellor"),
                    Choice(
                        ServiceFinderApplication.START_STATE,
                        "Find clinics and services",
                    ),
                ]
                + submenu_choices,
            )
        ]

        error, choices = await contentrepo.get_choices_by_tag("mainmenu")
        if error:
            return await self.go_to_state("state_error")

        parent_topic_links = {}
        relationship_topic_links = {}
        for choice in choices:
            error, sub_choices = await contentrepo.get_choices_by_parent(choice.value)
            if error:
                return await self.go_to_state("state_error")

            for sub_choice in sub_choices:
                parent_topic_links[sub_choice.value] = choice.value

                if "relationship" in choice.label.lower():
                    relationship_topic_links[sub_choice.value] = choice.label

            sections.append((f"*{choice.label}*", sub_choices))

        sections.append(
            (
                "🙋🏿‍♂️ *QUESTIONS?*",
                [Choice(AskaQuestionApplication.START_STATE, "Ask your own question")],
            )
        )
        sections.append(
            (
                "⚙️ *CHAT SETTINGS*",
                [
                    Choice(
                        ChangePreferencesApplication.START_STATE,
                        "Update your information",
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
                if choice.value in relationship_topic_links:
                    self.save_metadata(
                        "relationship_section_title",
                        relationship_topic_links[choice.value],
                    )
                    return "state_check_relationship_status_set"
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
                    "💡 *TIP:* _Jump back to this menu at any time by replying_ *0* or "
                    "*MENU*.",
                ]
            )
        )

        additional_messages = []
        # We ignore errors here, because if there's an error they just won't get the
        # banner, we can still carry on and not go to the error state
        _, banner_choices = await contentrepo.get_choices_by_tag("banner")
        banner_messages = []
        # Get all the content pages that have the banner tag
        for choice in banner_choices:
            # Get all the messages for this content page
            message_id = 1
            while message_id is not None:
                error, page_details = await contentrepo.get_page_details(
                    self.user, choice.value, message_id
                )
                if error:
                    message_id = None
                else:
                    banner_messages.append(page_details["body"])
                    if page_details.get("next_prompt"):
                        message_id += 1
                    else:
                        message_id = None

        msisdn = utils.normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.lstrip("+")

        if len(banner_messages) > 0:
            timestamp = get_current_datetime() + timedelta(hours=2)
            # We ignore this error, as it just means they won't get the reminder
            await rapidpro.update_profile(
                whatsapp_id,
                {
                    "feedback_timestamp": timestamp.isoformat(),
                    "feedback_type": "facebook_banner",
                },
                self.user.metadata,
            )
            additional_messages.extend(banner_messages)

        # Check if user is a first time user to be sent a privacy policy message
        privacy_reminder_sent = await self.get_privacy_reminder_sent(whatsapp_id)
        if not privacy_reminder_sent:
            privacy_reminder_messages = [
                "\n".join(
                    [
                        "*This conversation is completely private and confidential.* 🤐",
                        "-----",
                        "",
                        "⚠️ If you think someone else could have access to the phone "
                        "you're using to chat, remember to *delete these messages* "
                        "at the end of our chat.",
                    ]
                )
            ]
            additional_messages.extend(privacy_reminder_messages)

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
            additional_messages=additional_messages,
        )

    async def state_check_relationship_status_set(self):
        rel_status = self.user.metadata.get("relationship_status")
        if not rel_status or rel_status == "" or rel_status.lower() == "skip":
            return await self.go_to_state("state_relationship_status")
        return await self.go_to_state("state_contentrepo_page")

    async def state_relationship_status(self):
        rel_section_title = self.user.metadata["relationship_section_title"]
        question = self._(
            "\n".join(
                [
                    f"*{rel_section_title}*",
                    "-----",
                    "",
                    "Before we get into relationship talk, I just wanted to find "
                    "out...",
                    "",
                    "[persona_emoji] *Are you currently in a relationship or seeing "
                    "someone special right now?*",
                    "",
                    "1. Yes, in a relationship",
                    "2. It's complicated",
                    "3. Not seeing anyone",
                    "4. Skip",
                ]
            )
        )
        return WhatsAppListState(
            self,
            question=question,
            button="Relationship Status",
            choices=[
                Choice("yes", self._("In a relationship")),
                Choice("complicated", self._("It's complicated")),
                Choice("no", self._("Not seeing anyone")),
                Choice("skip", self._("Skip")),
            ],
            next="state_relationship_status_submit",
            error=self._(get_generic_error()),
        )

    async def state_relationship_status_submit(self):
        rel_status = self.user.answers.get("state_relationship_status")
        if rel_status != "skip":
            msisdn = utils.normalise_phonenumber(self.inbound.from_addr)
            whatsapp_id = msisdn.lstrip(" + ")
            data = {
                "relationship_status": rel_status,
            }

            await rapidpro.update_profile(whatsapp_id, data, self.user.metadata)

        return await self.go_to_state("state_contentrepo_page")

    async def state_contentrepo_page(self):
        msisdn = utils.normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.lstrip("+")
        timestamp = utils.get_current_datetime() + timedelta(minutes=10)
        # We ignore this error, as it just means they won't get the reminder
        await rapidpro.update_profile(
            whatsapp_id,
            {
                "feedback_timestamp": timestamp.isoformat(),
                "feedback_type": "content",
            },
            self.user.metadata,
        )

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

        # If a user loads a content repo page from somewhere other than the main menu
        # then we need to infer the menu level and the topics they've seen
        inferred_menu_level = len(page_details["title"].split("/")) - 1

        if not metadata.get("suggested_content") and not metadata.get("topics_viewed"):
            self.save_metadata("topics_viewed", [str(page_details["parent_id"])])

        # do not increment menu level when retrieving the next whatsapp message,
        # only when going to a child page in content repo
        if message_id > 1:
            menu_level = metadata.get("current_menu_level", inferred_menu_level)
        else:
            menu_level = (
                metadata.get("current_menu_level", (inferred_menu_level - 1)) + 1
            )
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

        parts = []

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
        error_parts = [get_generic_error(), ""] + parts
        parts = [
            title,
            "-----",
            "",
            body,
            "",
        ] + parts
        question = self._("\n".join([part for part in parts if part is not None]))
        error_text = self._(
            "\n".join([part for part in error_parts if part is not None])
        )

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
            error=error_text,
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

    async def state_prep_push_msg_related_page(self):
        push_related_page_id = self.user.metadata.get("push_related_page_id", None)

        if not push_related_page_id:
            return await self.go_to_state("state_error")

        msisdn = utils.normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.lstrip(" + ")
        error = await rapidpro.update_profile(
            whatsapp_id, {"push_related_page_id": ""}, self.user.metadata
        )
        if error:
            return await self.go_to_state("state_error")

        self.save_metadata("selected_page_id", push_related_page_id)
        self.save_metadata("current_message_id", 1)
        self.save_metadata("is_suggested_page", False)
        self.save_metadata("suggested_content", {})

        return await self.go_to_state("state_contentrepo_page")
