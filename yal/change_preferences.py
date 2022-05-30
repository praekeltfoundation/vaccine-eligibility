import asyncio
import logging

from vaccine.states import Choice, WhatsAppListState
from vaccine.utils import normalise_phonenumber
from yal import turn
from yal.yal_base_application import YalBaseApplication

logger = logging.getLogger(__name__)


class Application(YalBaseApplication):
    START_STATE = "state_display_preferences"

    async def state_display_preferences(self):
        msisdn = normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.lstrip(" + ")

        error, fields = await turn.get_profile(whatsapp_id)
        if error:
            return await self.go_to_state("state_error")

        def get_field(name):
            value = fields.get(name)
            if value == "skip":
                return "Empty"

            if name == "gender" and value == "other":
                return get_field("gender_other")

            return value

        dob_year = fields.get("dob_year")
        dob_month = fields.get("dob_month")
        dob_day = fields.get("dob_day")
        relationship_status = get_field("relationship_status")
        gender = get_field("gender")

        dob = []
        if dob_day != "skip" and dob_month != "skip":
            dob.append(dob_day)
            dob.append(dob_month)
        elif dob_day != "skip":
            dob.append(dob_month)

        if dob_year != "skip":
            dob.append(dob_year)

        question = self._(
            "\n".join(
                [
                    "*CHAT SETTINGS*",
                    "⚙️ Change or update your info",
                    "-----",
                    "*👩🏾 No problem. Here's the info you've saved:*",
                    "",
                    "☑️ 🎂 *Birthday*",
                    "/".join(dob),
                    "",
                    "☑️ 💟 *In a Relationship?*",
                    relationship_status,
                    "",
                    "☑️ 📍 *Location*",
                    "[saved LOCATION]",
                    "",
                    "☑️ 🌈  *Identity*",
                    gender,
                ]
            )
        )

        await self.worker.publish_message(self.inbound.reply(question))
        await asyncio.sleep(0.5)

        return await self.go_to_state("state_change_info_prompt")

    async def state_change_info_prompt(self):
        async def next_(choice: Choice):
            return choice.value

        question = self._(
            "\n".join(
                [
                    "👩🏾 *What info would you like to change?*",
                    "",
                    "1. Birthday",
                    "2. Relationship Status",
                    "3. Location",
                    "4. Identity",
                    "-----",
                    "*Or reply:*",
                    "*0* - 🏠 Back to *Main MENU*",
                    "*#* - 🆘 Get *HELP*",
                ]
            )
        )

        return WhatsAppListState(
            self,
            question=question,
            choices=[
                Choice("state_update_dob_year", self._("Birthday")),
                Choice(
                    "state_update_relationship_status", self._("Relationship Status")
                ),
                Choice("state_update_location", self._("Location")),
                Choice("state_update_gender", self._("Identity")),
            ],
            next=next_,
            error=self._("TODO"),
            error_footer=self._("\n" "Reply with the number next to the month."),
            button="Change Preferences",
        )

    async def state_update_relationship_status(self):
        question = self._(
            "\n".join(
                [
                    "*CHAT SETTINGS*",
                    "⚙️ Change or update your info",
                    "-----",
                    "",
                    "*And what about love? Seeing someone special right now?*",
                    "",
                    "*1*. Yes",
                    "*2*. It's complicated",
                    "*3*. No",
                    "*4*. Skip",
                ]
            )
        )
        return WhatsAppListState(
            self,
            question=question,
            button="Relationship Status",
            choices=[
                Choice("yes", self._("Yes")),
                Choice("complicated", self._("It's complicated")),
                Choice("no", self._("No")),
                Choice("skip", self._("Skip")),
            ],
            next="state_update_relationship_status_submit",
            error=self._("TODO"),
        )

    async def state_update_relationship_status_submit(self):
        msisdn = normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.lstrip(" + ")

        status = self.user.answers.get("state_update_relationship_status")

        error = await turn.update_profile(whatsapp_id, {"relationship_status": status})
        if error:
            return await self.go_to_state("state_error")

        return await self.go_to_state("state_display_preferences")
