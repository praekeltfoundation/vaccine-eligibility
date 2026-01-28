import logging

from vaccine.base_application import BaseApplication
from vaccine.states import (
    Choice,
    CustomChoiceState,
    EndState,
)

logger = logging.getLogger(__name__)


class Application(BaseApplication):
    START_STATE = "state_support_start"

    async def state_support_start(self):
        choices = [
            Choice("state_pregnancy_care", "🤰 Pregnancy care"),
            Choice("state_hiv_prevention", "🛡️ HIV prevention"),
            Choice("state_health_updates", "🗣️ Health updates"),
            Choice("state_sex_health_info", "💖 Sex health info"),
        ]

        async def next_(choice: Choice) -> str:
            if choice.value.startswith("state_"):
                return choice.value
            elif choice.value.isdigit() and 1 <= int(choice.value) <= len(choices):
                index = int(choice.value) - 1
                return choices[index].value

        question = self._(
            "\n".join(
                [
                    "What kind of support are you looking for right now?",
                    "",
                    "*Choose what fits you best* 👇",
                    "1. 🤰 Pregnancy care",
                    "2. 🛡️ HIV prevention",
                    "3. 🗣️ Health updates",
                    "4. 💖 Sex health info",
                ]
            )
        )

        return CustomChoiceState(
            self,
            question=question,
            error=self._(
                "⚠️ This service works best when you use the numbered options available"
            ),
            choices=choices,
            next=next_,
        )

    async def state_pregnancy_care(self):
        return EndState(
            self,
            text=self._(
                "\n".join(
                    [
                        "🤰 *You’ve got this 🤍*",
                        "",
                        "If you’re planning a pregnancy, pregnant, or a new mom, *MomConnect* is here for you.",
                        "",
                        "Get trusted info, reminders, and support for you and your baby.",
                        "",
                        "👉 Go to *MomConnect* 🔗 https://wa.me/27796312456?text=join",
                        "",
                        "_Reply ‘Support’ to find more options_",
                    ]
                )
            ),
        )

    async def state_hiv_prevention(self):
        return EndState(
            self,
            text=self._(
                "\n".join(
                    [
                        "*Staying safe is power* 💪",
                        "",
                        "*myPrep.co.za.* helps young people get real info about HIV prevention.",
                        "",
                        "Use the tool to see which prevention method could work for you.",
                        "",
                        "👉 Visit *myPrep* 🔗 https://www.myprep.co.za",
                        "OR👉 Take the *PrepMethod Quiz*",
                        "🔗 https://prepmethodquiz.web.app/#/",
                        "",
                        "_Reply ‘Support’ to find more options_",
                    ]
                )
            ),
        )

    async def state_health_updates(self):
        return EndState(
            self,
            text=self._(
                "\n".join(
                    [
                        "*Stay informed* 📰",
                        "",
                        "*ContactNDOH* shares official health info and updates from South Africa’s National Department of Health.",
                        "",
                        "Simple. Reliable. Straight from the source.",
                        "",
                        "👉 Go to *ContactNDOH.* 🔗"
                        "https://wa.me/27600123456?text=HiContactNdoh",
                        "",
                        "_Reply ‘Support’ to find more options_",
                    ]
                )
            ),
        )

    async def state_sex_health_info(self):
        return EndState(
            self,
            text=self._(
                "\n".join(
                    [
                        "*Curious is normal* 💖",
                        "",
                        "For sexual health, relationships, and HIV prevention options, check out *SelfCav*.",
                        "",
                        "Learn about PrEP, PEP, relationships, and mental health — all on WhatsApp. 👉"
                        "",
                        "Go to SelfCav🔗",
                        "https://wa.me/27873731548?text=BwiseBot",
                        "",
                        "_Reply ‘Support’ to find more options_",
                    ]
                )
            ),
        )
