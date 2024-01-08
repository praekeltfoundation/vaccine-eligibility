from vaccine.base_application import BaseApplication
from vaccine.states import Choice, EndState, WhatsAppButtonState
from yal import config
from yal.utils import get_generic_error


class Application(BaseApplication):
    START_STATE = "state_facebook_member"
    NOT_INTERESTED_STATE = "state_facebook_invite_decline"

    async def state_facebook_member(self):
        async def _next(choice: Choice):
            if choice.value == "no":
                return "state_not_a_member"
            return "state_was_a_member"

        return WhatsAppButtonState(
            self,
            question=self._(
                "Great! Before we get started, have you been a member of the B-Wise "
                "Facebook page since before June 2023?"
            ),
            choices=[
                Choice("yes", "Yes"),
                Choice("no", "No"),
            ],
            next=_next,
            error=self._(get_generic_error()),
        )

    async def state_was_a_member(self):
        return EndState(
            self,
            self._(
                "\n".join(
                    [
                        "Excellent! Thank you for being a valuable member of our "
                        "Facebook community.",
                        "",
                        "To do the survey, click on the link below, answer the "
                        "questions and you’re all done!",
                        "",
                        config.FACEBOOK_SURVEY_INVITE_MEMBERS_URL,
                    ]
                )
            ),
            next=self.START_STATE,
        )

    async def state_not_a_member(self):
        async def _next(choice: Choice):
            if choice.value == "no":
                return "state_fb_feed_not_seen"
            return "state_fb_feed_seen"

        return WhatsAppButtonState(
            self,
            question=self._("Have you seen a post by B-Wise on your Facebook feed?"),
            choices=[
                Choice("yes", "Yes"),
                Choice("no", "No"),
            ],
            next=_next,
            error=self._(get_generic_error()),
        )

    async def state_fb_feed_seen(self):
        return EndState(
            self,
            self._(
                "\n".join(
                    [
                        "That’s great! The B-Wise Facebook community is a great place "
                        "for cheeky memes and thought-provoking posts.",
                        "",
                        "Now on to the survey! Click on the link below, answer the "
                        "questions and you’re all done!",
                        "",
                        config.FACEBOOK_SURVEY_INVITE_SEEN_FEED_URL,
                    ]
                )
            ),
            next=self.START_STATE,
        )

    async def state_fb_feed_not_seen(self):
        return EndState(
            self,
            self._(
                "\n".join(
                    [
                        "No sweat! We won’t ask you to do the survey though, since we "
                        "are only looking for people who are members of the B-Wise "
                        "Facebook community or who have seen B-Wise posts on Facebook.",
                        "",
                        "Please enjoy the B-Wise tool and stay safe.",
                    ]
                )
            ),
            next=self.START_STATE,
        )

    async def state_facebook_invite_decline(self):
        return EndState(
            self,
            self._(
                "\n".join(
                    [
                        "That's completely okay! This won’t affect your experience on "
                        "the B-Wise chatbot.",
                        "",
                        "Please enjoy the B-Wise tool and stay safe.",
                    ]
                )
            ),
            next=self.START_STATE,
        )
