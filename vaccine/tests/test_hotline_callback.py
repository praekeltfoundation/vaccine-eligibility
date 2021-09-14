import pytest

from vaccine.hotline_callback import Application
from vaccine.models import Message
from vaccine.testing import AppTester


@pytest.fixture
def tester():
    return AppTester(Application)


@pytest.mark.asyncio
async def test_exit_keywords(tester: AppTester):
    await tester.user_input("Main Menu")
    tester.assert_message("", session=Message.SESSION_EVENT.CLOSE)
    assert tester.application.messages[0].helper_metadata["automation_handle"] is True
    tester.assert_state(None)
    assert tester.user.answers == {}


@pytest.mark.asyncio
async def test_question(tester: AppTester):
    await tester.user_input("support", session=Message.SESSION_EVENT.NEW)
    tester.assert_message(
        "\n".join(
            [
                "The toll-free hotline is available for all your vaccination "
                "questions!",
                "Call 0800 029 999",
                "",
                "⏰ Operating hours for *Registration and appointment queries*",
                "Monday to Friday",
                "7am-8pm",
                "Saturdays, Sundays and Public Holidays",
                "8am-6pm",
                "",
                "---------------------",
                "",
                "The toll-free hotline is also available for you to call *24 hours a "
                "day*, every day for *Emergencies, health advice and post vaccination "
                "queries*",
            ]
        ),
        buttons=["Call me back", "Main Menu"],
        header="💉 *VACCINE SUPPORT*",
    )
    tester.assert_state("state_menu")
