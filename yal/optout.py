import asyncio
import logging

from vaccine.base_application import BaseApplication
from vaccine.states import Choice, EndState, FreeText, WhatsAppListState
from yal import contentrepo, rapidpro, utils
from yal.change_preferences import Application as ChangePreferencesApplication
from yal.mainmenu import Application as MainMenuApplication
from yal.utils import (
    BACK_TO_MAIN,
    GENDERS,
    GENERIC_ERROR,
    GET_HELP,
    get_current_datetime,
)

logger = logging.getLogger(__name__)


class Application(BaseApplication):
    START_STATE = "state_optout"

    async def state_optout(self):

        inbound = utils.clean_inbound(self.inbound.content)
        question = self._(
            "\n".join(
                [
                    "*🙍🏾‍♀️Hi!*",
                    "",
                    f"I just received a message from you saying {inbound}.",
                    "",
                    "What would you like to do?",
                    "",
                    "1 - I  want to stop receiving notifications",
                    "2 - I  want to delete all data saved about me.",
                    "3 - No change. I still want to receive messages from B-Wise",
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
                "skip": MainMenuApplication.START_STATE,
            },
            error=self._(GENERIC_ERROR),
        )

    async def state_submit_optout(self):
        msisdn = utils.normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.lstrip(" + ")

        error = await rapidpro.update_profile(
            whatsapp_id,
            {
                "onboarding_completed": "",
                "opted_out": "TRUE",
                "opted_out_timestamp": get_current_datetime().isoformat(),
            },
        )
        if error:
            return await self.go_to_state("state_error")

        return await self.go_to_state("state_stop_notifications")

    async def state_stop_notifications(self):
        msg = self._(
            "\n".join(
                [
                    "✅ B-Wise by Young Africa Live will stop sending you messages.",
                    "------",
                    "",
                    "👩🏾 I'm sorry to see you go. It's been a pleasure talking to you.",
                ]
            )
        )
        self.worker.publish_message(self.inbound.reply(msg))
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
                    "🛑 STOP MESSAGING ME",
                    "*What can we do better?*",
                    "------",
                    "",
                    "*👩🏾 We are always trying to improve.*",
                    "*Could you tell us why you want to stop getting these messages?*",
                    "",
                    "Your answer will help us make this service better.",
                    "",
                    "1 - Getting too many messages",
                    "2 - Find the service difficult to use",
                    "3 - The messages are too long",
                    "4 - The messages are boring/unoriginal/repetitive",
                    "5 - The content is not relevant to me",
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
                Choice("message volume", self._("Too many messages")),
                Choice("user-friendliness", self._("Difficult to use")),
                Choice("irrelevant", self._("Content irrelevant")),
                Choice("boring", self._("Content is boring")),
                Choice("lengthy", self._("Messages too long")),
                Choice("other", self._("Other")),
                Choice("none", self._("Rather not say")),
                Choice("skip", self._("Skip")),
            ],
            next=_next,
            error=self._(GENERIC_ERROR),
        )

    async def state_delete_saved(self):
        msisdn = utils.normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.lstrip(" + ")

        data = {
            "dob_month": "",
            "dob_day": "",
            "dob_year": "",
            "relationship_status": "",
            "gender": "",
            "gender_other": "",
            "province": "",
            "suburb": "",
            "street_name": "",
            "street_number": "",
        }
        error, fields = await rapidpro.get_profile(whatsapp_id)
        if error:
            return await self.go_to_state("state_error")
        old_details = self.__get_user_details(fields)

        error = await rapidpro.update_profile(whatsapp_id, data)
        if error:
            return await self.go_to_state("state_error")

        await self.worker.publish_message(
            self.inbound.reply(
                self._(
                    "\n".join(
                        [
                            "✅ *We've deleted all your saved personal data including:*",
                            "",
                            f"- *{old_details['dob']}*",
                            f"- *{old_details['relationship_status']}*",
                            f"- *{old_details['location']}*",
                            f"- *{old_details['gender']}*",
                            "",
                            "*------*",
                            "*Reply:*",
                            "*1* - to see your personal data",
                            BACK_TO_MAIN,
                            GET_HELP,
                        ]
                    )
                ),
                helper_metadata={
                    "image": contentrepo.get_image_url("bwise_header.png")
                },
            )
        )

        return await self.go_to_state(ChangePreferencesApplication.START_STATE)

    async def state_tell_us_more(self):
        return FreeText(
            self,
            question=self._(
                "\n".join(
                    [
                        "🛑 STOP MESSAGING ME",
                        "*Please tell us more*",
                        "------",
                        "",
                        "🙍🏾‍♀️ *Thanks.*" "",
                        "If you could share your reason by replying with a ",
                        "few words about why you want to stop receiving messages,",
                        "I'd be so grateful 🙂.",
                    ]
                )
            ),
            next="state_farewell_optout",
        )

    async def state_farewell_optout(self):
        await self.worker.publish_message(
            self.inbound.reply(
                self._(
                    "\n".join(
                        [
                            "🛑 STOP MESSAGING ME",
                            "*Goodbye* 👋🏾",
                            "-",
                            "",
                            "🙍🏾‍♀️Thanks so much for your help.",
                            "",
                            "You won't get any more messages from us unless you *send "
                            "the word HI* to this number.",
                            "",
                            "For any medical issues, please visit your nearest clinic.",
                            "You're also welcome to visit us online, any time. 🙂👇🏾",
                            "",
                            "*Have a lovely day!* ☀️",
                        ]
                    )
                )
            )
        )
        # await asyncio.sleep(0.5)
        return EndState(
            self,
            text=self._(
                "\n".join(
                    [
                        "Need quick answers?",
                        "Check out B-Wise online!👆🏾",
                        "",
                        "https://bwisehealth.com/",
                        "",
                        "You'll find loads of sex, relationships",
                        "and health info there.",
                        "It's also my other virtual office.",
                    ]
                )
            ),
            helper_metadata={"image": contentrepo.get_image_url("bwise_header.png")},
        )

    def __get_user_details(self, fields):
        def get_field(name):
            value = fields.get(name)
            if value == "skip":
                return "Empty"
            if name == "gender":
                if value == "other":
                    return get_field("gender_other")
                return GENDERS[value]
            return value

        dob_year = fields.get("dob_year")
        dob_month = fields.get("dob_month")
        dob_day = fields.get("dob_day")
        relationship_status = get_field("relationship_status")
        gender = get_field("gender")

        province = fields.get("province")
        suburb = fields.get("suburb")
        street_name = fields.get("street_name")
        street_number = fields.get("street_number")

        result = {
            "dob": f"{dob_day} {dob_month} {dob_year}",
            "relationship_status": f"{relationship_status}",
            "location": f"{street_number}, {street_name}, {suburb}, {province}",
            "gender": f"{gender}",
        }
        return result
