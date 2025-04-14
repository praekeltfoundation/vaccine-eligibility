from typing import Optional

from vaccine.base_application import BaseApplication
from vaccine.models import Message
from vaccine.states import (
    Choice,
    EndState,
    ErrorMessage,
    FreeText,
    WhatsAppButtonState,
    WhatsAppListState,
)


class Application(BaseApplication):
    START_STATE = "state_start"

    async def process_message(self, message: Message) -> list[Message]:
        if message.session_event == Message.SESSION_EVENT.CLOSE:
            self.user.session_id = None
            return [
                message.reply(
                    content="\n".join(
                        [
                            "We're sorry, but you've taken too long to reply and your "
                            "session has expired.",
                            "If you would like to continue, you can at anytime by "
                            "typing the word *VACCINE*.",
                            "",
                            "Reply *MENU* to return to the main menu",
                        ]
                    ),
                    continue_session=False,
                )
            ]
        return await super().process_message(message)

    async def state_start(self):
        self.send_message(
            "Thank you for your interest in the getting the COVID-19 vaccine. The "
            "South African national vaccine rollout is being done over 3 phases. "
            "Answer these questions to find out which phase you are in:"
        )
        return await self.go_to_state("state_occupation")

    async def state_occupation(self):
        not_sure = "\n".join(
            [
                "*Health Care Workers* include doctors, nurses, dentists, pharmacists, "
                "medical specialists and all people involved in providing health "
                "services such as cleaning, security, medical waste disposal and "
                "administrative work.",
                "",
                "*Essential Workers* include police officers, miners, teachers, people "
                "working in security, retail, food, funeral, banking and essential "
                "muncipal and home affairs, border control and port health services.",
            ]
        )

        async def next_state(choice: Choice):
            if choice.value == "not_sure":
                self.send_message(not_sure)
                return "state_occupation"
            return "state_congregate"

        return WhatsAppListState(
            self,
            question="\n".join(
                [
                    "◼️◻️◻️◻️◻️",
                    "",
                    "Which of these positions or job titles describes your current "
                    "employment:",
                ]
            ),
            button="Select Employment",
            choices=[
                Choice("hcw", "Health Care Worker"),
                Choice("essential", "Essential Worker"),
                Choice("other", "Other"),
                Choice("not_sure", "Not Sure"),
            ],
            error="⚠️ This service works best when you use the numbered options "
            "available\n",
            next=next_state,
        )

    async def state_congregate(self):
        not_sure = (
            "Examples of places where you may be exposed to large numbers of people "
            "include care homes, detention centers, shelters, prisons, hospitality "
            "settings, tourism settings and educational institutions"
        )

        async def next_state(choice: Choice):
            if choice.value == "not_sure":
                self.send_message(not_sure)
                return "state_congregate"
            return "state_age"

        return WhatsAppButtonState(
            self,
            question="\n".join(
                [
                    "◼️◼️◻️◻️◻️",
                    "",
                    "Are you often in contact with lots of people or are you often in "
                    "a closed space with lots of people?",
                ]
            ),
            choices=[
                Choice("yes", "Yes"),
                Choice("no", "No"),
                Choice("not_sure", "Not Sure"),
            ],
            error="⚠️ This service works best when you use the numbered options "
            "available\n",
            next=next_state,
        )

    async def state_age(self):
        async def check_age(content: Optional[str]):
            try:
                age = int(content or "")
                assert age >= 0
            except (ValueError, TypeError, AssertionError) as e:
                raise ErrorMessage("⚠️  Reply using numbers only. Example *27*") from e

        progress_bar = "◼️◼️◼️◻️◻️"
        return FreeText(
            self,
            question="\n".join(
                [progress_bar, "", "How old are you? (Reply with a number)"]
            ),
            next="state_location",
            check=check_age,
        )

    async def state_location(self):
        async def store_location_coords(content: Optional[str]):
            if not self.inbound:  # pragma: no cover
                return
            loc = self.inbound.transport_metadata.get("msg", {}).get("location", {})
            latitude = loc.get("latitude")
            longitude = loc.get("longitude")
            if isinstance(latitude, float) and isinstance(longitude, float):
                self.save_answer("location_geopoint", [latitude, longitude])

        return FreeText(
            self,
            question="\n".join(
                [
                    "◼️◼️◼️◼️◻️",
                    "",
                    "Please tell us where you live.",
                    "",
                    "You can share your location 📍 using WhatsApp by following these "
                    "steps:",
                    "",
                    "Tap the attach icon (+ or 📎) on the bottom of WhatsApp.",
                    "Select location",
                    "This will bring up a map with a pin showing your current "
                    "location. Tap Send Your Current Location if this is your address.",
                    "You can also choose from various other nearby locations if you "
                    "think that the GPS is a bit off.",
                    "Or TYPE the name of your Suburb, Township, Town or Village (or "
                    "nearest)?",
                ]
            ),
            next="state_comorbidities",
            check=store_location_coords,
        )

    async def state_comorbidities(self):
        not_sure = "\n".join(
            [
                "Having one or more specific chronic conditions could impact which "
                "phase you are in. These conditions include:",
                "Chronic Lung Disease (such as Emphysema or Chronic Bronchitis)",
                "Cardiovascular disease / Heart Disease",
                "Renal Disease / Chronic Kidney Disease",
                "HIV",
                "TB (Turboculosis)",
                "Obesity (diagnosed overweight)",
            ]
        )

        async def next_state(choice: Choice):
            if choice.value == "not_sure":
                self.send_message(not_sure)
                return "state_comorbidities"
            return "state_result"

        return WhatsAppButtonState(
            self,
            question="\n".join(
                [
                    "◼️◼️◼️◼️◼️",
                    "",
                    "Has a doctor ever diagnosed you with diabetes, chronic lung "
                    "disease, cardiovascular(heart) disease, renal disease, HIV, TB, "
                    "or Obesity?",
                ]
            ),
            choices=[
                Choice("yes", "Yes"),
                Choice("no", "No"),
                Choice("not_sure", "Not Sure"),
            ],
            error="⚠️ This service works best when you use the numbered options "
            "available\n",
            next=next_state,
        )

    async def state_result(self):
        if int(self.user.answers["state_age"]) < 18:
            self.save_answer("phase", "ineligible")
            return await self.go_to_state("state_result_ineligible")
        elif self.user.answers["state_occupation"] == "hcw":
            self.save_answer("phase", "1")
            return await self.go_to_state("state_result_1")
        elif (
            self.user.answers["state_occupation"] == "essential"
            or self.user.answers["state_congregate"] == "yes"
            or int(self.user.answers["state_age"]) >= 60
            or self.user.answers["state_comorbidities"] == "yes"
        ):
            self.save_answer("phase", "2")
            return await self.go_to_state("state_result_2")
        else:
            self.save_answer("phase", "3")
            return await self.go_to_state("state_result_3")

    async def state_result_ineligible(self):
        return EndState(
            self,
            text="\n".join(
                [
                    "Based on your age you are currently NOT able to get the vaccine. "
                    "This may change when more vaccine trials are completed.",
                    "",
                    "----",
                    "Reply:",
                    "💉 *VACCINE* for info and updates",
                    "📌 *0* to go to the main *MENU*",
                ]
            ),
            next=self.START_STATE,
        )

    async def state_result_1(self):
        return EndState(
            self,
            text="\n".join(
                [
                    "✅ *PHASE 1*",
                    "🟥 *PHASE 2*",
                    "🟥 *PHASE 3*",
                    "",
                    "*Congratulations!* Based on your responses you could be in "
                    "*PHASE 1* and possibly get vaccinated now.",
                    "",
                    "*What to do next:*",
                    "To confirm this and get an appointment, you need to register "
                    "online at https://vaccine.enroll.health.gov.za",
                    "",
                    "Registration does not guarentee that you will get the vaccine "
                    "immediately. It helps us check that you fall into this phase and "
                    "plan for your vaccine appointment.",
                    "",
                    "*To register, you will need:* ",
                    "👉🏽 Access to the internet on any device ",
                    "👉🏽 Your ID number or Passport (non-RSA)",
                    "👉🏽 General contact information (your cellphone number will be "
                    "used as the primary mode of communication).",
                    "👉🏽 Employment information (who you work for and where)",
                    "👉🏽 Where relevant, your professional registration details, and "
                    "medical aid are also requested.",
                    "",
                    "If you have all this information available, the 3-step "
                    "registration should take 2-3 minutes.",
                    "",
                    "----",
                    "Reply:",
                    "💉 *VACCINE* for info and updates",
                    "📌 *0* to go to the main *MENU*",
                ]
            ),
            next=self.START_STATE,
        )

    async def state_result_2(self):
        return WhatsAppButtonState(
            self,
            question="\n".join(
                [
                    "🟥 *PHASE 1*",
                    "✅ *PHASE 2*",
                    "🟥 *PHASE 3*",
                    "",
                    "Your answers show that you could be part of *PHASE 2*.",
                    "",
                    "Would you like to be notified when registration for *PHASE 2* is "
                    "available?",
                ]
            ),
            choices=[Choice("yes", "Yes"), Choice("no", "No")],
            error="⚠️ This service works best when you use the numbered options "
            "available",
            next="state_confirm_notification",
        )

    async def state_result_3(self):
        return WhatsAppButtonState(
            self,
            question="\n".join(
                [
                    "🟥 *PHASE 1*",
                    "🟥 *PHASE 2*",
                    "✅ *PHASE 3*",
                    "",
                    "Your answers show that you could be part of *PHASE 3*.",
                    "",
                    "Would you like to be notified when registration for *PHASE 3* is "
                    "available?",
                ]
            ),
            choices=[Choice("yes", "Yes"), Choice("no", "No")],
            error="⚠️ This service works best when you use the numbered options "
            "available",
            next="state_confirm_notification",
        )

    async def state_confirm_notification(self):
        if (
            self.user.answers.get("state_result_2") == "yes"
            or self.user.answers.get("state_result_3") == "yes"
        ):
            verb = "will"
        else:
            verb = "won't"
        return EndState(
            self,
            text="\n".join(
                [
                    f"Thank you for confirming. We {verb} contact you.",
                    "",
                    "----",
                    "Reply:",
                    "💉 *VACCINE* for info and updates",
                    "📌 *0* to go to the main *MENU*",
                ]
            ),
            next=self.START_STATE,
        )
