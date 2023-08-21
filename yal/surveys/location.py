import asyncio

from vaccine.base_application import BaseApplication
from vaccine.states import (
    Choice,
    EndState,
    FreeText,
    WhatsAppButtonState,
    WhatsAppListState,
)
from vaccine.validators import nonempty_validator
from yal import config, contentrepo, rapidpro
from yal.askaquestion import Application as AAQApplication
from yal.change_preferences import Application as ChangePreferencesApplication
from yal.utils import get_generic_error, normalise_phonenumber


class Application(BaseApplication):
    START_STATE = "state_location_introduction"

    async def state_location_introduction(self):
        survey_status = self.user.metadata.get(
            "ejaf_location_survey_status", "not_invited"
        )
        survey_group = self.user.metadata.get("ejaf_location_survey_group")
        error, group_count = await rapidpro.get_group_membership_count(
            group_name=f"EJAF location survey completed {survey_group}"
        )
        if error:
            return await self.go_to_state("state_error")

        if survey_status in ("completed", "airtime_sent"):
            return await self.go_to_state("state_location_already_completed")
        elif (
            group_count >= config.LOCATION_STUDY_GROUP_LIMIT
            or survey_status != "pending"
        ):
            return await self.go_to_state("state_location_not_invited")

        choices = [
            Choice("yes", self._("Yes, I agree")),
            Choice("no", self._("No, I don't agree")),
            Choice("question", self._("I have a question")),
        ]

        question = self._(
            "\n".join(
                [
                    "*Fantastic! 👏🏾 🎉 And thank you 🙏🏽*",
                    "",
                    "*Before we start, here are a few important notes.* 📈",
                    "",
                    "This survey is just to understand who may be interested in "
                    "joining a focus group discussion in September and where would be "
                    "convenient for those users to meet. You do not have to be "
                    "interested in participating in focus groups to complete this "
                    "survey. If you indicate that you`re interested, we may phone you "
                    "about being part of a focus group in the future, however you do "
                    "not need to agree to participate in any future discussion.",
                    "",
                    "*It should only take 3 mins and we'll give you R10 airtime at the "
                    "end.*",
                    "",
                    "👤 Your answers are anonymous and confidential. In order to "
                    "respect your privacy we only ask about which city or town you "
                    "live in. We won`t share data outside the BWise WhatsApp Chatbot "
                    "team.",
                    "",
                    "✅ This study is voluntary and you can leave at any time by "
                    "responding with the keyword *“menu”* however, if you exit before "
                    "completing the survey, you will *not* be able to receive the R10 "
                    "airtime voucher.",
                    "",
                    "🔒 You`ve seen and agreed to the BWise privacy policy. Just a "
                    "reminder that we promise to keep all your info private and "
                    "secure.",
                    "",
                    "Are you comfortable for us to continue? Otherwise you can leave "
                    "the survey at any time by responding with the keyword “menu”. If "
                    "you have any questions, please email bwise@praekelt.org",
                ]
            )
        )
        return WhatsAppButtonState(
            self,
            question=question,
            choices=choices,
            error=self._(get_generic_error()),
            next={
                "yes": "state_location_province",
                "no": "state_location_decline",
                "question": "state_send_consent_pdf",
            },
        )

    async def state_location_not_invited(self):
        return EndState(
            self,
            self._(
                "Unfortunately it looks like we already have enough people answering "
                "this survey, but thank you for your interest."
            ),
            next=self.START_STATE,
        )

    async def state_location_already_completed(self):
        return EndState(
            self,
            self._("This number has already completed the location survey."),
            next=self.START_STATE,
        )

    async def state_location_decline(self):
        return EndState(
            self,
            self._(
                "That's completely okay, there are no consequences to not taking part "
                "in this study. Please enjoy the BWise tool and stay safe."
            ),
            next=self.START_STATE,
        )

    async def state_send_consent_pdf(self):
        await self.worker.publish_message(
            self.inbound.reply(
                None,
                helper_metadata={"document": contentrepo.get_privacy_policy_url()},
            )
        )
        await asyncio.sleep(1.5)
        return await self.go_to_state("state_location_question")

    async def state_location_question(self):
        async def _next(choice: Choice):
            if choice.value == "decline":
                return "state_location_decline"
            return "state_location_province"

        return WhatsAppButtonState(
            self,
            question=self._(
                "\n".join(
                    [
                        "You should be able to find the answer to any questions you "
                        "have in the consent doc we sent you. If you still have "
                        "questions, please email bwise@praekelt.org",
                        "",
                        "Would you like to continue?",
                    ]
                )
            ),
            choices=[
                Choice("continue", "Continue"),
                Choice("decline", "No, thank you"),
            ],
            next=_next,
            error=self._(get_generic_error()),
        )

    async def state_location_province(self):
        async def _next(choice: Choice):
            if choice.value == "other":
                return "state_location_not_recruiting"
            return "state_location_name_city"

        question = "*What province do you live in?*"

        return WhatsAppListState(
            self,
            question=question,
            button="Province",
            choices=[
                Choice("GT", "Gauteng"),
                Choice("NL", "Kwazulu-Natal"),
                Choice("WC", "Western Cape"),
                Choice("other", "None of the above"),
            ],
            next=_next,
            error=self._(get_generic_error()),
        )

    async def state_location_not_recruiting(self):
        return EndState(
            self,
            self._(
                "\n".join(
                    [
                        "Sorry, we`re only recruiting people for group discussions in "
                        "Gauteng, KZN and the Western Cape."
                        "",
                        "Reply with “menu” to return to the main menu",
                    ]
                )
            ),
            next=self.START_STATE,
        )

    async def state_location_name_city(self):
        question = self._(
            "\n".join(
                [
                    "*What is the name of the city or town you live in or live closest "
                    "to?*",
                    "",
                    "Please *TYPE* in the name of the city or town.",
                ]
            )
        )
        return FreeText(
            self,
            question=question,
            next="state_location_area_type",
            check=nonempty_validator(question),
        )

    async def state_location_area_type(self):
        question = "What type of area are you living in?"

        return WhatsAppListState(
            self,
            question=question,
            button="Area type",
            choices=[
                Choice("traditional", "Traditional/chiefdom"),
                Choice("urban", "Urban/town"),
                Choice("farm", "Farm/rural"),
                Choice("dont_understand", "I don't understand"),
            ],
            next="state_location_group_invite",
            error=self._(get_generic_error()),
        )

    async def state_location_group_invite(self):
        choices = [
            Choice("yes", self._("Yes, I am interested")),
            Choice("no", self._("No, thank you")),
            Choice("dont_understand", self._("I don’t understand")),
        ]
        question = self._(
            "\n".join(
                [
                    "All good, thank you! 🙌🏾",
                    "",
                    "We are organising group discussions for BWise users in September. "
                    "The focus groups will be with other users aged 15-24 years.",
                    "",
                    "We'd ask about your experiences on the platform and how feasible, "
                    "usable and effective the BWise chatbot is as a mobile health "
                    "platform for young South Africans.",
                    "",
                    "*Remember that you do not have to be interested in joining the "
                    "focus groups to complete this survey. If you indicate you are "
                    "interested you can still reject any invitation if we do contact "
                    "you.*",
                    "",
                    "Are you interested in being invited to one of these discussions "
                    "in the future?",
                ]
            )
        )
        return WhatsAppButtonState(
            self,
            question=question,
            choices=choices,
            error=self._(get_generic_error()),
            next="state_location_update_status",
        )

    async def state_location_update_status(self):
        msisdn = normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.lstrip(" + ")

        optin = self.user.answers["state_location_group_invite"]

        error = await rapidpro.update_profile(
            whatsapp_id,
            {
                "ejaf_location_survey_status": "completed",
                "ejaf_location_survey_optin": optin,
            },
            self.user.metadata,
        )
        if error:
            return await self.go_to_state("state_error")

        return await self.go_to_state("state_location_end")

    async def state_location_end(self):
        optin = self.user.answers["state_location_group_invite"]

        if optin == "dont_understand":
            question = self._(
                "\n".join(
                    [
                        "No problem! If you would like to learn more about the "
                        "platform, please email the Bwise team at bwise@praekelt.org",
                        "",
                        "Thank you for taking part in our survey 🙏🏽",
                        "",
                        "*You will get your R10 airtime within 24 hours*",
                        "",
                        "You can engage with the B-Wise chatbot at any time for some "
                        "helpful messages or to ask any questions.",
                    ]
                )
            )
        else:
            question = self._(
                "\n".join(
                    [
                        "*And that's a wrap!*",
                        "",
                        "Thank you for taking part in our survey 🙏🏽",
                        "",
                        "*You will get your R10 airtime within 24 hours.*",
                        "",
                        "You can engage with the B-Wise chatbot at any time for some "
                        "helpful messages or to ask any questions.",
                    ]
                )
            )
        return WhatsAppButtonState(
            self,
            question=question,
            choices=[
                Choice("menu", self._("Go to the menu")),
                Choice("aaq", self._("Ask a question")),
                Choice("update_settings", self._("Update Settings")),
            ],
            next={
                "menu": "state_pre_mainmenu",
                "aaq": AAQApplication.START_STATE,
                "update_settings": ChangePreferencesApplication.START_STATE,
            },
            error=self._(get_generic_error()),
        )
