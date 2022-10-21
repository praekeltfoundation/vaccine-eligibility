from datetime import datetime, timedelta

from vaccine.base_application import BaseApplication
from vaccine.states import Choice, FreeText, WhatsAppButtonState
from vaccine.utils import get_display_choices
from yal import rapidpro, utils
from yal.askaquestion import Application as AAQApplication
from yal.pleasecallme import Application as PCMApplication
from yal.servicefinder import Application as SFApplication


class ServiceFinderFeedbackSurveyApplication(BaseApplication):
    START_STATE = "state_servicefinder_feedback_survey_start"
    CALLBACK_2_STATE = "state_servicefinder_feedback_survey_2_start"
    CALLBACK_2_DELAY = timedelta(days=14)
    APPOINTMENT_TIPS_CONTENT_ID = 494
    APPOINTMENT_TIPS_MENU_LEVEL = 2

    async def state_servicefinder_feedback_survey_start(self):
        msisdn = utils.normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.lstrip("+")
        # Reset this, so that we only get the survey once after a push
        await rapidpro.update_profile(whatsapp_id, {"feedback_survey_sent": ""})
        return await self.go_to_state("state_process_servicefinder_feedback_trigger")

    async def state_process_servicefinder_feedback_trigger(self):
        # Mirror the message here, for response and error handling
        choices = [
            Choice("yes", self._("Yes, thanks")),
            Choice("no", self._("No, not helpful")),
            Choice("already_know", self._("I knew this before")),
        ]
        question = "\n".join(
            [
                "[persona_emoji] *Did you find the clinic finder helpful?*",
                "",
                get_display_choices(choices, bold_numbers=True),
                "",
                "-----",
                utils.BACK_TO_MAIN,
                utils.GET_HELP,
            ]
        )
        return WhatsAppButtonState(
            self,
            question=question,
            choices=choices,
            error=utils.get_generic_error(),
            next={
                "yes": "state_servicefinder_positive_feedback",
                "no": "state_servicefinder_negative_feedback",
                "already_know": "state_servicefinder_already_know_feedback",
            },
        )

    async def state_servicefinder_positive_feedback(self):
        buttons = [Choice("skip", self._("Skip"))]
        question = "\n".join(
            [
                "*That's great news* 🙌🏾",
                "",
                "Do you have any feedback on how we could make the clinic finder even "
                "better?",
                "",
                "_Just type and send your answer, or reply *SKIP* if you have no "
                "feedback._",
                "",
                "--",
                "",
                utils.BACK_TO_MAIN,
                utils.GET_HELP,
            ]
        )
        return FreeText(
            self,
            question=question,
            next="state_save_servicefinder_callback_2",
            buttons=buttons,
        )

    async def state_servicefinder_negative_feedback(self):
        question = "\n".join(
            [
                "*I'm sorry I couldn't help you this time.*",
                "",
                "Please tell me a bit more about what went wrong with the clinic "
                "finder so I can help you next time.",
                "",
                "_Just type and send_",
                "",
                "--",
                "",
                utils.BACK_TO_MAIN,
                utils.GET_HELP,
            ]
        )
        return FreeText(
            self, question=question, next="state_servicefinder_feedback_confirmation"
        )

    async def state_servicefinder_already_know_feedback(self):
        choices = [
            Choice("aaq", self._("Ask a question")),
            Choice("pleasecallme", self._("Talk to a counsellor")),
        ]
        question = "\n".join(
            [
                "We're so glad you know about the clinics close by. Knowledge is power "
                "🙌🏾",
                "",
                "If you'd like to find alternative clinics just try the clinic finder "
                "again.",
                "",
                "*What would you like to do now?*",
                "",
                get_display_choices(choices),
                "",
                "--",
                "*Or reply*",
                utils.BACK_TO_MAIN,
                utils.GET_HELP,
            ]
        )
        return WhatsAppButtonState(
            self,
            question=question,
            choices=choices,
            error=utils.get_generic_error(),
            next={
                "aaq": AAQApplication.START_STATE,
                "pleasecallme": PCMApplication.START_STATE,
            },
        )

    async def state_save_servicefinder_callback_2(self):
        timestamp = utils.get_current_datetime() + self.CALLBACK_2_DELAY
        whatsapp_id = utils.normalise_phonenumber(self.inbound.from_addr).lstrip("+")
        await rapidpro.update_profile(
            whatsapp_id=whatsapp_id,
            fields={
                "feedback_timestamp": timestamp.isoformat(),
                "feedback_type": "servicefinder_2",
            },
        )
        return await self.go_to_state("state_servicefinder_feedback_confirmation")

    async def state_servicefinder_feedback_confirmation(self):
        choices = [
            Choice("aaq", self._("Ask a question")),
            Choice("pleasecallme", self._("Talk to a counsellor")),
        ]
        question = "\n".join(
            [
                "Thank you for this. Your feedback helps me make this experience "
                "better every time👍🏾",
                "",
                "*What would you like to do now?*",
                "",
                "",
                get_display_choices(choices),
                "",
                "-----",
                "*Or reply*",
                utils.BACK_TO_MAIN,
                utils.GET_HELP,
            ]
        )
        return WhatsAppButtonState(
            self,
            question=question,
            choices=choices,
            error=utils.get_generic_error(),
            next={
                "aaq": AAQApplication.START_STATE,
                "pleasecallme": PCMApplication.START_STATE,
            },
        )

    async def state_servicefinder_feedback_survey_2_start(self):
        # Repeat the question here for error and selection handling
        whatsapp_id = utils.normalise_phonenumber(self.inbound.from_addr).lstrip("+")
        error, fields = await rapidpro.get_profile(whatsapp_id)
        if error:
            return await self.go_to_state("state_error")
        feedback_datetime = datetime.fromisoformat(fields["feedback_timestamp"])
        choices = [
            Choice("yes", self._("Yes, I went")),
            Choice("no", self._("No, I didn't go")),
        ]
        question = "\n".join(
            [
                "Hi, it's me again [persona_emoji]",
                "",
                "Just wanted to find out if you went to the health facility you were "
                f"looking for on {feedback_datetime.strftime('%d/%m/%Y')}?",
                "",
                get_display_choices(choices, bold_numbers=True),
                "",
                "--",
                "",
                utils.BACK_TO_MAIN,
                utils.GET_HELP,
            ]
        )
        return WhatsAppButtonState(
            self,
            question=question,
            choices=choices,
            error=utils.get_generic_error(),
            next={
                "yes": "state_went_to_service",
                "no": "state_did_not_go_to_service",
            },
        )

    async def state_went_to_service(self):
        choices = [
            Choice("helped", self._("They helped me")),
            Choice("no_help_needed", self._("I didn't need help")),
            Choice("no_help", self._("They didn't help me")),
        ]
        question = "\n".join(
            [
                "I'm glad to hear that. Well done for taking care of your health 👏🏾",
                "",
                "Did a health worker treat your condition, give you advice or give you "
                "medication?",
                "",
                get_display_choices(choices, bold_numbers=True),
                "",
                "--",
                "",
                utils.BACK_TO_MAIN,
                utils.GET_HELP,
            ]
        )
        return WhatsAppButtonState(
            self,
            question=question,
            choices=choices,
            error=utils.get_generic_error(),
            next={
                "helped": "state_service_helped",
                "no_help_needed": "state_service_no_help_needed",
                "no_help": "state_service_no_help",
            },
        )

    async def state_did_not_go_to_service(self):
        choices = [
            Choice("changed_mind", self._("I changed my mind")),
            Choice("will_go", self._("I still plan to go")),
            Choice("elsewhere", self._("I got help somewhere else")),
            Choice("other", self._("Another reason")),
        ]
        question = "\n".join(
            [
                "Was there a reason you didn't go to the clinic?",
                "",
                get_display_choices(choices, bold_numbers=True),
                "",
                "--",
                "",
                utils.BACK_TO_MAIN,
                utils.GET_HELP,
            ]
        )
        return WhatsAppButtonState(
            self,
            question=question,
            choices=choices,
            error=utils.get_generic_error(),
            next={
                "changed_mind": "state_have_information_needed",
                "will_go": "state_have_information_needed",
                "elsewhere": "state_service_finder_offer_aaq",
                "other": "state_service_finder_offer_aaq",
            },
        )

    async def state_service_helped(self):
        choices = [
            Choice("yes", self._("Yes, I have all the info I need")),
            Choice("no", self._("No, I don't know what to do")),
            Choice("not_sure", self._("I'm not sure")),
        ]
        question = "\n".join(
            [
                "Do you have enough info on how to manage your situation?",
                "",
                get_display_choices(choices, bold_numbers=True),
                "",
                "-----",
                "*Or reply:*",
                utils.BACK_TO_MAIN,
                utils.GET_HELP,
            ]
        )
        return WhatsAppButtonState(
            self,
            question=question,
            choices=choices,
            error=utils.get_generic_error(),
            next={
                "yes": "state_service_finder_survey_complete",
                "no": "state_service_finder_offer_aaq",
                "not_sure": "state_service_finder_offer_aaq",
            },
        )

    async def state_service_no_help_needed(self):
        choices = [
            Choice("good", self._("Good")),
            Choice("ok", self._("Just ok")),
            Choice("bad", self._("Bad")),
        ]
        question = "\n".join(
            [
                "I'm glad to hear that you're in good health.",
                "",
                "How would you rate the service you received at the clinic?",
                "",
                get_display_choices(choices, bold_numbers=True),
                "",
                "--",
                "*Or reply*",
                utils.BACK_TO_MAIN,
                utils.GET_HELP,
            ]
        )
        return WhatsAppButtonState(
            self,
            question=question,
            choices=choices,
            error=utils.get_generic_error(),
            next={
                "good": "state_offer_appointment_tips",
                "ok": "state_offer_appointment_tips_bad_experience",
                "bad": "state_offer_appointment_tips_bad_experience",
            },
        )

    async def state_service_no_help(self):
        choices = [
            Choice("queue", self._("Queue was too long")),
            Choice("other_help", self._("Got other help")),
            Choice("other", self._("Another reason")),
        ]
        question = "\n".join(
            [
                "Eish... Was there a reason you didn't get to see a health worker?",
                "",
                get_display_choices(choices, bold_numbers=True),
                "",
                "--",
                "*Or reply*",
                utils.BACK_TO_MAIN,
                utils.GET_HELP,
            ]
        )
        return WhatsAppButtonState(
            self,
            question=question,
            choices=choices,
            error=utils.get_generic_error(),
            next={
                "queue": "state_offer_clinic_finder",
                "other_help": "state_got_other_help",
                "other": "state_other_reason_for_no_service",
            },
        )

    async def state_have_information_needed(self):
        choices = [
            Choice("yes", self._("Yes")),
            Choice("no", self._("No")),
            Choice("not_sure", self._("I'm not sure")),
        ]
        question = "\n".join(
            [
                "Do you have the information you need to manage your situation?",
                "",
                get_display_choices(choices, bold_numbers=True),
                "",
                "--",
                "",
                utils.BACK_TO_MAIN,
                utils.GET_HELP,
            ]
        )
        return WhatsAppButtonState(
            self,
            question=question,
            choices=choices,
            error=utils.get_generic_error(),
            next={
                "yes": "state_service_finder_survey_complete_2",
                "no": "state_offer_aaq",
                "not_sure": "state_offer_aaq",
            },
        )

    async def state_service_finder_survey_complete(self):
        choices = [
            Choice("aaq", self._("Ask a question")),
            Choice("pleasecallme", self._("Talk to a counsellor")),
        ]
        question = "\n".join(
            [
                "That's great. Thanks for letting me know👌🏾",
                "",
                "What would you like to do now?",
                "",
                get_display_choices(choices, bold_numbers=True),
                "",
                "-----",
                "*Or reply:*",
                utils.BACK_TO_MAIN,
                utils.GET_HELP,
            ]
        )
        return WhatsAppButtonState(
            self,
            question=question,
            choices=choices,
            error=utils.get_generic_error(),
            next={
                "aaq": AAQApplication.START_STATE,
                "pleasecallme": PCMApplication.START_STATE,
            },
        )

    async def state_service_finder_offer_aaq(self):
        choices = [
            Choice("yes", self._("Yes, please!")),
            Choice("no", self._("Maybe later")),
        ]
        question = "\n".join(
            [
                "No worries! Maybe I can help...",
                "",
                "Would you like to ask me your questions now?",
                "",
                get_display_choices(choices, bold_numbers=True),
                "",
                "-----",
                "*Or reply:*",
                utils.BACK_TO_MAIN,
                utils.GET_HELP,
            ]
        )
        return WhatsAppButtonState(
            self,
            question=question,
            choices=choices,
            error=utils.get_generic_error(),
            next={
                "yes": AAQApplication.START_STATE,
                "no": "state_service_finder_survey_complete_3",
            },
        )

    async def state_get_appointment_tips(self):
        metadata = self.user.metadata
        self.save_metadata("selected_page_id", self.APPOINTMENT_TIPS_CONTENT_ID)
        self.save_metadata("current_menu_level", self.APPOINTMENT_TIPS_MENU_LEVEL)
        self.save_metadata("current_message_id", 1)
        return await self.go_to_state("state_contentrepo_page")

    async def state_offer_appointment_tips(self):
        choices = [
            Choice("yes", self._("Yes, please")),
            Choice("no", self._("No, thanks")),
        ]
        question = "\n".join(
            [
                "That's great news 👌🏾",
                "",
                "Would you like some tips on preparing for your next appointment?",
                "",
                get_display_choices(choices, bold_numbers=False),
                "",
                "--",
                "*Or reply*",
                utils.BACK_TO_MAIN,
                utils.GET_HELP,
            ]
        )
        return WhatsAppButtonState(
            self,
            question=question,
            choices=choices,
            error=utils.get_generic_error(),
            next={
                "yes": "state_get_appointment_tips",
                "no": "state_service_finder_survey_complete_4",
            },
        )

    async def state_offer_appointment_tips_bad_experience(self):
        choices = [
            Choice("yes", self._("Yes, please")),
            Choice("no", self._("No, thanks")),
        ]
        question = "\n".join(
            [
                "I'm sorry about your bad experience.",
                "",
                "Would you like some tips that might help you prepare for your next "
                "appointment?",
                "",
                get_display_choices(choices, bold_numbers=False),
                "",
                "--",
                "*Or reply*",
                utils.BACK_TO_MAIN,
                utils.GET_HELP,
            ]
        )
        return WhatsAppButtonState(
            self,
            question=question,
            choices=choices,
            error=utils.get_generic_error(),
            next={
                "yes": "state_get_appointment_tips",
                "no": "state_service_finder_survey_complete_4",
            },
        )

    async def state_offer_clinic_finder(self):
        choices = [
            Choice("yes", self._("Yes, please")),
            Choice("no", self._("No, thanks")),
        ]
        question = "\n".join(
            [
                "Would you like to search for a different clinic that's also nearby?",
                "",
                get_display_choices(choices, bold_numbers=False),
                "",
                "--",
                "*Or reply:*",
                utils.BACK_TO_MAIN,
                utils.GET_HELP,
            ]
        )
        return WhatsAppButtonState(
            self,
            question=question,
            choices=choices,
            error=utils.get_generic_error(),
            next={
                "yes": AAQApplication.START_STATE,
                "no": "state_service_finder_survey_complete_3",
            },
        )

    async def state_got_other_help(self):
        choices = [
            Choice("yes", self._("Yes, thanks")),
            Choice("no", self._("No, I need info")),
            Choice("not_sure", self._("I'm not sure")),
        ]
        question = "\n".join(
            [
                "Awesome! Do you have the information you need to manage your "
                "condition?",
                "",
                get_display_choices(choices, bold_numbers=False),
                "--",
                "*Or reply*",
                utils.BACK_TO_MAIN,
                utils.GET_HELP,
            ]
        )
        return WhatsAppButtonState(
            self,
            question=question,
            choices=choices,
            error=utils.get_generic_error(),
            next={
                "yes": "state_service_finder_survey_complete_5",
                "no": "state_offer_aaq",
                "not_sure": "state_offer_aaq",
            },
        )

    async def state_other_reason_for_no_service(self):
        question = "\n".join(
            [
                "Please let me know why you didn't go to the clinic?",
                "",
                "_Just type and send your reply_",
                "",
                "--",
                "*Or reply:*",
                utils.BACK_TO_MAIN,
                utils.GET_HELP,
            ]
        )
        return FreeText(
            self, question=question, next="state_service_finder_survey_complete_2"
        )

    async def state_service_finder_survey_complete_2(self):
        choices = [
            Choice("aaq", self._("Ask a question")),
            Choice("pleasecallme", self._("Talk to a counsellor")),
        ]
        question = "\n".join(
            [
                "Thank you for the feedback, you're helping this service improve👍🏾",
                "",
                "What would you like to do now?",
                "",
                get_display_choices(choices, bold_numbers=True),
                "",
                "-----",
                "*Or reply:*",
                utils.BACK_TO_MAIN,
                utils.GET_HELP,
            ]
        )
        return WhatsAppButtonState(
            self,
            question=question,
            choices=choices,
            error=utils.get_generic_error(),
            next={
                "aaq": AAQApplication.START_STATE,
                "pleasecallme": PCMApplication.START_STATE,
            },
        )

    async def state_offer_aaq(self):
        choices = [
            Choice("yes", self._("Yes, please!")),
            Choice("no", self._("Maybe later")),
        ]
        question = "\n".join(
            [
                "No worries! Maybe I can help...",
                "",
                "Would you like to ask me your questions now?",
                "",
                get_display_choices(choices, bold_numbers=True),
                "",
                "-----",
                "*Or reply:*",
                utils.BACK_TO_MAIN,
                utils.GET_HELP,
            ]
        )
        return WhatsAppButtonState(
            self,
            question=question,
            choices=choices,
            error=utils.get_generic_error(),
            next={
                "yes": AAQApplication.START_STATE,
                "no": "state_service_finder_survey_complete_3",
            },
        )

    async def state_service_finder_survey_complete_3(self):
        choices = [
            Choice("aaq", self._("Ask a question")),
            Choice("pleasecallme", self._("Talk to a counsellor")),
            Choice("servicefinder", self._("Find a clinic")),
        ]
        question = "\n".join(
            [
                "Shap 👍🏾",
                "",
                "If you change your mind, you know what to do.",
                "",
                "What would you like to do now?",
                "",
                get_display_choices(choices, bold_numbers=True),
                "",
                "-----",
                "*Or reply:*",
                utils.BACK_TO_MAIN,
                utils.GET_HELP,
            ]
        )
        return WhatsAppButtonState(
            self,
            question=question,
            choices=choices,
            error=utils.get_generic_error(),
            next={
                "aaq": AAQApplication.START_STATE,
                "pleasecallme": PCMApplication.START_STATE,
                "servicefinder": SFApplication.START_STATE,
            },
        )

    async def state_service_finder_survey_complete_4(self):
        choices = [
            Choice("aaq", self._("Ask a question")),
            Choice("pleasecallme", self._("Talk to a counsellor")),
        ]
        question = "\n".join(
            [
                "Cool 👍🏾 No problem.",
                "",
                "What would you like to do now?",
                "",
                get_display_choices(choices, bold_numbers=True),
                "",
                "--",
                "*Or reply*",
                utils.BACK_TO_MAIN,
                utils.GET_HELP,
            ]
        )
        return WhatsAppButtonState(
            self,
            question=question,
            choices=choices,
            error=utils.get_generic_error(),
            next={
                "aaq": AAQApplication.START_STATE,
                "pleasecallme": PCMApplication.START_STATE,
            },
        )

    async def state_service_finder_survey_complete_5(self):
        choices = [
            Choice("yes", self._("Yes, please!")),
            Choice("no", self._("Maybe later")),
        ]
        question = "\n".join(
            [
                "No worries! Maybe I can help...",
                "",
                "Would you like to ask me your questions now?",
                "",
                get_display_choices(choices, bold_numbers=True),
                "",
                "-----",
                "*Reply:*",
                utils.BACK_TO_MAIN,
                utils.GET_HELP,
            ]
        )
        return WhatsAppButtonState(
            self,
            question=question,
            choices=choices,
            error=utils.get_generic_error(),
            next={
                "yes": AAQApplication.START_STATE,
                "no": "state_service_finder_survey_complete_3",
            },
        )
