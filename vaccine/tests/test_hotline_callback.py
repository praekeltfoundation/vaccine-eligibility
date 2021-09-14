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
async def test_menu(tester: AppTester):
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

    await tester.user_input("call me back")
    tester.assert_state("state_full_name")


@pytest.mark.asyncio
async def test_full_name(tester: AppTester):
    tester.setup_state("state_menu")
    await tester.user_input("call me back")
    tester.assert_message(
        "\n".join(
            [
                "Please type your NAME",
                "(This will be given to the hotline team to use when they call you "
                "back)",
            ]
        )
    )
    tester.assert_state("state_full_name")

    await tester.user_input("")
    tester.assert_message(
        "\n".join(
            [
                "Please type your NAME",
                "(This will be given to the hotline team to use when they call you "
                "back)",
            ]
        )
    )
    tester.assert_state("state_full_name")

    await tester.user_input("test name")
    tester.assert_state("state_select_number")


@pytest.mark.asyncio
async def test_select_number(tester: AppTester):
    tester.setup_state("state_full_name")
    await tester.user_input("test name")
    tester.assert_message(
        "Can the hotline team call you back on 082 000 1001?",
        buttons=["Use this number", "Use a different number"],
    )
    tester.assert_state("state_select_number")

    await tester.user_input("invalid")
    tester.assert_message(
        "Can the hotline team call you back on 082 000 1001?",
        buttons=["Use this number", "Use a different number"],
    )
    tester.assert_state("state_select_number")

    await tester.user_input("use this number")
    # tester.assert_state("state_enter_number")
