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
    await tester.user_input("I agree")
    tester.assert_state("state_province")


@pytest.mark.asyncio
async def test_province(tester: AppTester):
    tester.setup_state("state_terms")
    await tester.user_input("I agree")
    tester.assert_state("state_province")
    tester.assert_message(
        "\n".join(
            [
                "*REPORT* 📵 Powered by ```Real411```",
                "",
                "Which province are you reporting this from?",
            ]
        )
    )
    assert tester.application.messages[0].helper_metadata["button"] == "Select province"

    assert [
        r["title"]
        for r in tester.application.messages[0].helper_metadata["sections"][0]["rows"]
    ] == [
        "Gauteng",
        "Western Cape",
        "KwaZulu-Natal",
        "Freestate",
        "Eastern Cape",
        "Limpopo",
        "Mpumalanga",
        "Northern Cape",
        "North West",
    ]
    await tester.user_input("western cape")
    tester.assert_state("state_first_name")


@pytest.mark.asyncio
async def test_first_name(tester: AppTester):
    tester.setup_state("state_province")
    await tester.user_input("western cape")
    tester.assert_state("state_first_name")
    tester.assert_message(
        "\n".join(
            ["*REPORT* 📵 Powered by ```Real411```", "", "Reply with your FIRST NAME:"]
        )
    )

    await tester.user_input("test name")
    tester.assert_state("state_surname")


@pytest.mark.asyncio
async def test_surname(tester: AppTester):
    tester.setup_state("state_first_name")
    await tester.user_input("test name")
    tester.assert_state("state_surname")
    tester.assert_message(
        "\n".join(
            ["*REPORT* 📵 Powered by ```Real411```", "", "Reply with your SURNAME:"]
        )
    )

    await tester.user_input("test surname")
    tester.assert_state("state_email")


@pytest.mark.asyncio
async def test_email(tester: AppTester):
    tester.setup_state("state_email")
    await tester.user_input("invalid email")
    tester.assert_state("state_email")
    tester.assert_message(
        "\n".join(
            [
                "*REPORT* 📵 Powered by ```Real411```",
                "",
                "Please TYPE your EMAIL address. (Or type SKIP if you are unable to "
                "share an email address.)",
            ]
        )
    )

    await tester.user_input("skip")
    tester.assert_state("state_source_type")

    tester.setup_state("state_email")
    await tester.user_input("valid@example.org")
    tester.assert_state("state_source_type")


@pytest.mark.asyncio
async def test_source_type(tester: AppTester):
    tester.setup_state("state_email")
    await tester.user_input("skip")
    tester.assert_state("state_source_type")
    tester.assert_message(
        "\n".join(
            [
                "*REPORT* 📵 Powered by ```Real411```",
                "",
                "Please tell us where you saw/heard the information being reported",
            ]
        )
    )

    assert tester.application.messages[0].helper_metadata["button"] == "Source type"

    assert [
        r["title"]
        for r in tester.application.messages[0].helper_metadata["sections"][0]["rows"]
    ] == [
        "WhatsApp",
        "Facebook",
        "Twitter",
        "Instagram",
        "Youtube",
        "Website",
        "Radio",
        "TV",
        "Political Ad",
        "Other",
    ]

    await tester.user_input("whatsapp")
    tester.assert_state("state_description")


@pytest.mark.asyncio
async def test_description(tester: AppTester):
    tester.setup_state("state_source_type")
    await tester.user_input("whatsapp")
    tester.assert_state("state_description")
    tester.assert_message(
        "\n".join(
            [
                "*REPORT* 📵 Powered by ```Real411```",
                "",
                "Please describe the information being reported in your own words:",
            ]
        )
    )

    await tester.user_input("test description")
    tester.assert_state("state_media")


@pytest.mark.asyncio
async def test_media(tester: AppTester):
    tester.setup_state("state_description")
    await tester.user_input("test description")
    tester.assert_state("state_media")
    tester.assert_message(
        "\n".join(
            [
                "*REPORT* 📵 Powered by ```Real411```",
                "",
                "Please share any additional information such as screenshots, photos, "
                "voicenotes or links (or type SKIP)",
            ]
        )
    )
