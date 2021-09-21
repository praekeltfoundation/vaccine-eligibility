import pytest

from vaccine.models import Message
from vaccine.real411 import Application
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
async def test_timeout(tester: AppTester):
    await tester.user_input(session=Message.SESSION_EVENT.CLOSE)
    tester.assert_message("We haven't heard from you in while.")


@pytest.mark.asyncio
async def test_start(tester: AppTester):
    await tester.user_input(session=Message.SESSION_EVENT.NEW)
    tester.assert_message(
        "\n".join(
            [
                "*REPORT* 📵 Powered by ```Real411```",
                "",
                "There is a lot of information going around related to the COVID-19 "
                "pandemic. Some of this information may be false and potentially "
                "harmful. Help to stop the spread of inaccurate or misleading "
                "information by reporting it here.",
            ]
        ),
        buttons=["Tell me more", "View and Accept T&Cs"],
    )

    await tester.user_input("View and Accept T&Cs")
    tester.assert_state("state_terms")


@pytest.mark.asyncio
async def test_terms(tester: AppTester):
    await tester.user_input("View and Accept T&Cs")
    tester.assert_state("state_terms")
    tester.assert_message(
        "\n".join(
            [
                "*REPORT* 📵 Powered by ```Real411```",
                "",
                "Your information is kept private and confidential and only used with "
                "your consent for the purpose of reporting disinformation.",
                "",
                "Do you agree to the attached PRIVACY POLICY?",
            ]
        ),
        buttons=["I agree", "No thanks"],
    )
