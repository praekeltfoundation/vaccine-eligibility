import pytest

from vaccine.models import Message
from vaccine.testing import AppTester
# TODO: fix this import once this flow is hooked up in main application
from yal.surveys.location import Application


@pytest.fixture
def tester():
    return AppTester(Application)


@pytest.mark.asyncio
async def test_state_location_introduction_already_completed(tester: AppTester):
    tester.setup_state("state_location_introduction")
    tester.user.metadata["ejaf_location_survey_status"] = "completed"

    await tester.user_input(session=Message.SESSION_EVENT.NEW)

    tester.assert_state("state_location_introduction")

    tester.assert_message("This number has already completed the location survey.")


@pytest.mark.asyncio
async def test_state_location_introduction_not_invited(tester: AppTester):
    tester.setup_state("state_location_introduction")
    await tester.user_input(session=Message.SESSION_EVENT.NEW)

    tester.assert_state("state_location_introduction")

    tester.assert_message(
        "Unfortunately it looks like we already have enough people answering this "
        "survey, but thank you for your interest."
    )


@pytest.mark.asyncio
async def test_state_location_introduction_pending(tester: AppTester):
    tester.setup_state("state_location_introduction")
    tester.user.metadata["ejaf_location_survey_status"] = "pending"
    await tester.user_input(session=Message.SESSION_EVENT.NEW)

    tester.assert_state("state_location_introduction")

    tester.assert_message(
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
