import asyncio
import logging

from vaccine.base_application import BaseApplication
from vaccine.states import Choice, FreeText, WhatsAppButtonState, WhatsAppListState
from vaccine.utils import get_display_choices
from yal import rapidpro, utils
from yal.askaquestion import Application as AAQApplication
from yal.change_preferences import Application as ChangePreferencesApplication
from yal.mainmenu import Application as MainMenuApplication
from yal.utils import (
    BACK_TO_MAIN,
    GENDERS,
    GET_HELP,
    get_current_datetime,
    get_generic_error,
)

logger = logging.getLogger(__name__)


class Application(BaseApplication):
    START_STATE = "state_optout"
    reminders_to_be_cleared = {
        "last_main_time": "",
        "last_mainmenu_time": "",
        "last_onboarding_time": "",
        "callback_check_time": "",
        "feedback_timestamp": "",
        "feedback_timestamp_2": "",
        "feedback_type": "",
        "push_message_opt_in": "False",
    }

    async def state_optout(self):
        inbound = utils.clean_inbound(self.inbound.content)
        question = self._(
            "\n".join(
                [
                    "[persona_emoji] *Hi!*",
                    "",
                    f"I just received a message from you saying *{inbound}*.",
                    "",
                    "*What would you like to do?*",
                    "",
                    "*1.* Stop receiving notifications",
                    "*2.* Delete all data saved about me.",
                    "*3.* No change, thanks",
                ]
            )
        )
        return WhatsAppListState(
            self,
            question=question,
            button="Opt Out",
            choices=[
                Choice("stop notifications", self._("Stop notifications")),
                Choice("delete saved", self._("Delete all save data")),
                Choice("skip", self._("No change")),
            ],
            next={
                "stop notifications": "state_submit_optout",
                "delete saved": "state_delete_saved",
                "skip": "state_opt_out_no_changes",
            },
            error=self._(get_generic_error()),
        )

    async def state_opt_out_no_changes(self):
        choices = [
            Choice("main_menu", "Go to the menu"),
            Choice("aaq", "Ask a question"),
        ]
        question = self._(
            "\n".join(
                [
                    "✅ *Cool - I'll keep sending you notifications.*",
                    "",
                    "*What would you like to do now?*",
                    "",
                    get_display_choices(choices),
                ]
            )
        )

        return WhatsAppButtonState(
            self,
            question=question,
            choices=choices,
            error=self._(get_generic_error()),
            next={
                "main_menu": MainMenuApplication.START_STATE,
                "aaq": AAQApplication.START_STATE,
            },
        )

    async def state_submit_optout(self):
        """Opt user out of the requested messages/campaigns"""
        msisdn = utils.normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.removeprefix("+")
        data = self.reminders_to_be_cleared

        error = await rapidpro.update_profile(
            whatsapp_id,
            data,
            self.user.metadata,
        )
        if error:
            return await self.go_to_state("state_error")

        return await self.go_to_state("state_stop_notifications")

    async def state_stop_notifications(self):
        msg = self._(
            "\n".join(
                [
                    "✅ *No problem, I'll stop sending you notifications.*",
                    "",
                    "Remember, you can still use the menu to get the info you need.",
                    "",
                    "💡if you change your mind and want to get to pick up your messages "
                    "where you left off, "
                    "just go to your ⚙️ chat settings from the main menu.",
                ]
            )
        )
        await self.worker.publish_message(self.inbound.reply(msg))
        await asyncio.sleep(0.5)
        return await self.go_to_state("state_optout_survey")

    async def state_optout_survey(self):
        async def _next(choice: Choice):
            if choice.value == "other":
                return "state_tell_us_more"
            return "state_farewell_optout"

        question = self._(
            "\n".join(
                [
                    "🛑 STOP MESSAGING ME / *What can we do better?*",
                    "------",
                    "",
                    "[persona_emoji] *We are always trying to improve.*",
                    "*Could you tell us why you want to stop getting these messages?*",
                    "",
                    "Your answer will help us make this service better.",
                    "",
                    "1 - Getting too many notifications",
                    "2 - Getting notifications too often",
                    "3 - Notifications are not useful",
                    "4 - Don't remember asking for notifications",
                    "6 - Other",
                    "7 - Rather not say",
                ]
            )
        )
        return WhatsAppListState(
            self,
            question=question,
            button="Opt Out",
            choices=[
                Choice("notification_volume", self._("Too many notifications")),
                Choice("notification_frequency", self._("I get them too often")),
                Choice("irrelevant", self._("Content irrelevant")),
                Choice("useless", self._("I don't find them useful")),
                Choice("useless", self._("I didn't sign up for them")),
                Choice("other", self._("Other issues")),
                Choice("none", self._("Rather not say")),
                Choice("skip", self._("Skip")),
            ],
            next=_next,
            error=self._(get_generic_error()),
        )

    async def state_delete_saved(self):
        msisdn = utils.normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.removeprefix("+")

        rp_fields = await rapidpro.get_instance_fields()
        rp_field_keys = {rp_field["key"] for rp_field in rp_fields}
        fields_to_update_and_retain = {
            "opted_out": "True",
            "opted_out_timestamp": get_current_datetime().isoformat(),
            "push_message_opt_in": "False",
        }

        for key in fields_to_update_and_retain:
            rp_field_keys.discard(key)

        update_rp_fields_dict = dict.fromkeys(rp_field_keys, "")
        combined_update_dict = fields_to_update_and_retain | update_rp_fields_dict
        old_details = self._get_user_details(self.user.metadata)

        batch_size = 100
        items = list(combined_update_dict.items())
        batches = []

        sorted_fields = sorted(items)

        sorted_field_dict = {}
        for key, value in sorted_fields:
            sorted_field_dict[key] = value

        # splitting combined dictionary into batches off 100
        # RapidPro can only update 100 fields at a time
        for i in range(0, len(sorted_field_dict), batch_size):
            batch = list(sorted_field_dict.items())[i : i + batch_size]  # noqa
            batches.append(batch)

        for batch in batches:
            batch_dict = dict(batch)

            error = await rapidpro.update_profile(
                whatsapp_id, batch_dict, self.user.metadata
            )
            if error:
                return await self.go_to_state("state_error")

        question = self._(
            "\n".join(
                [
                    "✅ *We've deleted all your saved personal data including:*",
                    "",
                    f"*- Age:* {old_details['age']}",
                    f"*- Relationship Status:* {old_details['relationship_status']}",
                    f"*- Location:* {old_details['location']}",
                    f"*- Gender:* {old_details['gender']}",
                    "",
                    "*------*",
                    "*Reply:*",
                    "1 - to see your personal data",
                    BACK_TO_MAIN,
                    GET_HELP,
                ]
            )
        )
        return WhatsAppButtonState(
            self,
            question=question,
            choices=[
                Choice("see", "See personal data"),
            ],
            error=self._(get_generic_error()),
            next={
                "see": ChangePreferencesApplication.START_STATE,
            },
        )

    async def state_tell_us_more(self):
        return FreeText(
            self,
            question=self._(
                "\n".join(
                    [
                        "🛑 STOP MESSAGING ME / Please tell us more*",
                        "------",
                        "",
                        "[persona_emoji] Thanks.",
                        "",
                        "Please share your reason by replying with a few words about "
                        "why you want to stop receiving messages, "
                        "I'd be so grateful 🙂.",
                    ]
                )
            ),
            next="state_farewell_optout",
        )

    async def state_farewell_optout(self):
        choices = [
            Choice("main_menu", "Go to the menu"),
            Choice("aaq", "Ask a question"),
        ]
        question = self._(
            "\n".join(
                [
                    "🛑 STOP MESSAGING ME",
                    "*Goodbye* 👋🏾",
                    "-",
                    "",
                    "[persona_emoji] *Thanks so much for your help.*",
                    "",
                    "*What would you like to do now?*",
                    get_display_choices(choices),
                ]
            )
        )

        return WhatsAppButtonState(
            self,
            question=question,
            choices=choices,
            error=self._(get_generic_error()),
            next={
                "main_menu": MainMenuApplication.START_STATE,
                "aaq": AAQApplication.START_STATE,
            },
        )

    def _get_user_details(self, fields):
        def get_field(name):
            value = fields.get(name)
            if not value or value == "skip":
                return "Empty"
            if name == "gender":
                return GENDERS.get(value, "Empty")
            return value

        relationship_status = get_field("relationship_status").title()
        gender = get_field("gender")
        location_description = get_field("location_description")
        age = get_field("age")

        result = {
            "age": f"{age}",
            "relationship_status": f"{relationship_status}",
            "location": location_description,
            "gender": f"{gender}",
        }
        return result
