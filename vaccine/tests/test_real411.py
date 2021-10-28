import pytest
from sanic import Sanic, response

from vaccine import real411_config as config
from vaccine.models import Message
from vaccine.real411 import Application
from vaccine.testing import AppTester


@pytest.fixture
def tester():
    return AppTester(Application)


@pytest.fixture
async def real411_mock(sanic_client):
    Sanic.test_mode = True
    app = Sanic("real411_mock")
    app.requests = []

    @app.route("/form-data", methods=["GET"])
    def check(request):
        app.requests.append(request)
        return response.file_stream(
            "vaccine/tests/real411.json", mime_type="application/json"
        )

    client = await sanic_client(app)
    url = config.REAL411_URL
    token = config.REAL411_TOKEN
    config.REAL411_URL = f"http://{client.host}:{client.port}"
    config.REAL411_TOKEN = "testtoken"
    yield client
    config.REAL411_URL = url
    config.REAL411_TOKEN = token


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
    tester.assert_state("state_first_name")


@pytest.mark.asyncio
async def test_first_name(tester: AppTester):
    tester.setup_state("state_terms")
    await tester.user_input("I agree")
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
async def test_email(tester: AppTester, real411_mock):
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
async def test_source_type(tester: AppTester, real411_mock):
    tester.setup_state("state_email")
    await tester.user_input("skip")
    tester.assert_state("state_source_type")
    tester.assert_message(
        "\n".join(
            [
                "*REPORT* 📵 Powered by ```Real411```",
                "",
                "Please tell us where you saw/heard the information being reported",
                "1. WhatsApp",
                "2. Facebook",
                "3. Twitter",
                "4. Instagram",
                "5. Youtube",
                "6. Other Website",
                "7. Radio / TV",
                "8. Political Ad",
                "9. Other",
            ]
        )
    )

    await tester.user_input("whatsapp")
    tester.assert_state("state_description")


@pytest.mark.asyncio
async def test_description(tester: AppTester, real411_mock):
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

    await tester.user_input("SKIP")
    tester.assert_state("state_opt_in")


@pytest.mark.asyncio
async def test_opt_in(tester: AppTester):
    tester.setup_state("state_media")
    await tester.user_input("SKIP")
    tester.assert_state("state_opt_in")
    tester.assert_message(
        "\n".join(
            [
                "*REPORT* 📵 Powered by ```Real411```",
                "",
                "To complete your report please confirm that all the information is "
                "accurate to the best of your knowledge and that you give ContactNDOH "
                "permission to send you message about the outcome of your report",
            ]
        ),
        buttons=["I agree", "No"],
    )


@pytest.mark.asyncio
async def test_success(tester: AppTester):
    tester.setup_state("state_opt_in")
    await tester.user_input("I agree")
    tester.assert_message(
        "\n".join(
            [
                "*REPORT* 📵 Powered by ```Real411```",
                "",
                "Thank you for helping to stop the spread of inaccurate or misleading "
                "information!",
                "",
                "Look out for messages from us in the next few days",
                "",
                "Reply 0 to return to the main MENU",
            ]
        ),
        session=Message.SESSION_EVENT.CLOSE,
    )
