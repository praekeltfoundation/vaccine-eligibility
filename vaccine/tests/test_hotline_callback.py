from datetime import date, datetime, timedelta, timezone
from unittest import mock

import pytest
from sanic import Sanic, response

from vaccine import hotline_callback_config as config
from vaccine.hotline_callback import Application, get_current_datetime, in_office_hours
from vaccine.models import Message
from vaccine.testing import AppTester


@pytest.fixture
def tester():
    return AppTester(Application)


@pytest.fixture
async def callback_api_mock(sanic_client):
    Sanic.test_mode = True
    app = Sanic("mock_callback_api")
    app.requests = []
    app.errors = 0
    app.errormax = 0

    @app.route(
        "/NDoHIncomingWhatsApp/api/CCISecure/SubmitWhatsAppChat", methods=["POST"]
    )
    def callback(request):
        app.requests.append(request)
        if app.errormax:
            if app.errors < app.errormax:
                app.errors += 1
                return response.text("", status=500)
        return response.text("Received Sucessfully")

    client = await sanic_client(app)
    url = config.CALLBACK_API_URL
    config.CALLBACK_API_URL = f"http://{client.host}:{client.port}"
    yield client
    config.CALLBACK_API_URL = url


@pytest.fixture
async def turn_api_mock(sanic_client):
    Sanic.test_mode = True
    app = Sanic("mock_turn_api")
    app.requests = []
    app.errors = 0
    app.errormax = 0

    @app.route("/v1/contacts/<msisdn:int>/messages", methods=["GET"])
    def callback(request, msisdn):
        app.requests.append(request)
        if app.errormax:
            if app.errors < app.errormax:
                app.errors += 1
                return response.json({}, status=500)
        return response.json(
            {
                "messages": [
                    {
                        "type": "text",
                        "text": {"body": "test message1"},
                        "timestamp": "1631711883",
                        "_vnd": {"v1": {"direction": "outbound"}},
                    },
                    {
                        "type": "text",
                        "text": {"body": "test message2"},
                        "timestamp": "1631712883",
                        "_vnd": {"v1": {"direction": "inbound"}},
                    },
                    {
                        "type": "image",
                        "timestamp": "1631713883",
                        "_vnd": {"v1": {"direction": "inbound"}},
                    },
                ]
            }
        )

    client = await sanic_client(app)
    url = config.TURN_URL
    config.TURN_URL = f"http://{client.host}:{client.port}"
    yield client
    config.TURN_URL = url


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
                "",
                "---------------------",
                "📌 Reply  *0* to return to the main *MENU*",
            ]
        ),
        buttons=["Call me back"],
        header="💉 VACCINE SUPPORT",
    )
    tester.assert_state("state_menu")

    await tester.user_input("call me back")
    tester.assert_state("state_full_name")


@pytest.mark.asyncio
async def test_menu_invalid(tester: AppTester):
    await tester.user_input("support", session=Message.SESSION_EVENT.NEW)
    tester.assert_state("state_menu")

    await tester.user_input("invalid")
    tester.assert_state(None)
    assert tester.application.messages[-1].helper_metadata == {
        "automation_handle": True
    }
    tester.assert_message(content="", session=Message.SESSION_EVENT.CLOSE)


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
@mock.patch("vaccine.hotline_callback.in_office_hours")
async def test_select_number(
    in_office_hours, tester: AppTester, callback_api_mock, turn_api_mock
):
    in_office_hours.return_value = False
    tester.setup_state("state_full_name")
    await tester.user_input("test name")
    tester.assert_message(
        "Can the hotline team call you back on 082 000 1001?",
        buttons=["Use this number", "Use another number"],
    )
    tester.assert_state("state_select_number")

    await tester.user_input("use this number")
    tester.assert_state(None)


@pytest.mark.asyncio
@mock.patch("vaccine.hotline_callback.in_office_hours")
async def test_enter_number(
    in_office_hours, tester: AppTester, callback_api_mock, turn_api_mock
):
    in_office_hours.return_value = True
    tester.setup_state("state_select_number")
    tester.setup_answer("state_full_name", "test name")
    await tester.user_input("use another number")
    tester.assert_message("Please TYPE the CELL PHONE NUMBER we can contact you on.")
    tester.assert_state("state_enter_number")

    await tester.user_input("invalid")
    tester.assert_message(
        "\n".join(["⚠️ Please type a valid cell phone number.", "Example _081234567_"])
    )
    tester.assert_state("state_enter_number")

    await tester.user_input("0820001003")
    tester.assert_state(None)


def test_get_current_datetime():
    dt = get_current_datetime()
    assert isinstance(dt, datetime)
    assert dt.tzinfo == timezone(timedelta(hours=2))


@mock.patch("vaccine.hotline_callback.get_current_datetime")
def test_in_office_hours(get_current_datetime):
    tz = timezone(timedelta(hours=2))

    # Weekday morning
    get_current_datetime.return_value = datetime(2021, 9, 15, 7, 0, 0, tzinfo=tz)
    assert in_office_hours() is True

    # Weekday afternoon
    get_current_datetime.return_value = datetime(2021, 9, 15, 19, 59, 59, tzinfo=tz)
    assert in_office_hours() is True

    # Weekday evening
    get_current_datetime.return_value = datetime(2021, 9, 15, 20, 0, 0, tzinfo=tz)
    assert in_office_hours() is False

    # Weekend morning
    get_current_datetime.return_value = datetime(2021, 9, 18, 8, 0, 0, tzinfo=tz)
    assert in_office_hours() is True

    # Weekend afternoon
    get_current_datetime.return_value = datetime(2021, 9, 18, 17, 59, 59, tzinfo=tz)
    assert in_office_hours() is True

    # Weekend evening
    get_current_datetime.return_value = datetime(2021, 9, 18, 18, 0, 0, tzinfo=tz)
    assert in_office_hours() is False

    # Public Holiday morning
    get_current_datetime.return_value = datetime(2021, 9, 24, 8, 0, 0, tzinfo=tz)
    assert in_office_hours() is True

    # Public Holiday afternoon
    get_current_datetime.return_value = datetime(2021, 9, 24, 17, 59, 59, tzinfo=tz)
    assert in_office_hours() is True

    # Public Holiday evening
    get_current_datetime.return_value = datetime(2021, 9, 24, 18, 0, 0, tzinfo=tz)
    assert in_office_hours() is False


@pytest.mark.asyncio
@mock.patch("vaccine.hotline_callback.in_office_hours")
async def test_success_inoffice(
    in_office_hours, tester: AppTester, callback_api_mock, turn_api_mock
):
    in_office_hours.return_value = True
    tester.setup_state("state_select_number")
    tester.setup_answer("state_full_name", "test name")
    tester.setup_user_address("1111")
    await tester.user_input("use this number")
    tester.assert_state(None)
    tester.assert_message(
        "\n".join(
            [
                "Thank you for confirming. The Hotline team have been informed and "
                "will call you back as soon as possible. Look out for an incoming call "
                "from +27315838817",
                "",
                "------",
                "📌 Reply  *0* to return to the main *MENU*",
            ]
        )
    )


@pytest.mark.asyncio
@mock.patch("vaccine.hotline_callback.get_today")
@mock.patch("vaccine.hotline_callback.in_office_hours")
async def test_success_ooo(
    in_office_hours, get_today, tester: AppTester, callback_api_mock, turn_api_mock
):
    in_office_hours.return_value = False
    get_today.return_value = date(2021, 9, 15)
    tester.setup_state("state_enter_number")
    tester.setup_answer("state_full_name", "test name")
    tester.setup_answer("state_select_number", "different_number")
    await tester.user_input("0820001003")
    tester.assert_state(None)
    tester.assert_message(
        "\n".join(
            [
                "Thank you for confirming. The Hotline team have been informed and "
                "will call you back during their operating hours. Look out for an "
                "incoming call from +27315838817",
                "",
                "------",
                "📌 Reply  *0* to return to the main *MENU*",
            ]
        )
    )
    [request] = callback_api_mock.app.requests
    assert request.json == {
        "Name": "test name",
        "CLI": "+27820001003",
        "DateTimeOfRequest": "2021-09-15",
        "Language": "English",
        "ChatHistory": "2021-09-15 15:18 < test message1\n"
        "2021-09-15 15:34 > test message2\n"
        "2021-09-15 15:51 > <image>",
    }


@pytest.mark.asyncio
@mock.patch("vaccine.hotline_callback.in_office_hours")
async def test_success_temporary_error(
    in_office_hours, tester: AppTester, callback_api_mock, turn_api_mock
):
    in_office_hours.return_value = False
    callback_api_mock.app.errormax = 1
    tester.setup_state("state_enter_number")
    tester.setup_answer("state_full_name", "test name")
    tester.setup_answer("state_select_number", "different_number")
    await tester.user_input("0820001003")
    tester.assert_state(None)
    tester.assert_message(
        "\n".join(
            [
                "Thank you for confirming. The Hotline team have been informed and "
                "will call you back during their operating hours. Look out for an "
                "incoming call from +27315838817",
                "",
                "------",
                "📌 Reply  *0* to return to the main *MENU*",
            ]
        )
    )
    assert len(callback_api_mock.app.requests) == 2


@pytest.mark.asyncio
@mock.patch("vaccine.hotline_callback.in_office_hours")
async def test_success_permanent_error(
    in_office_hours, tester: AppTester, callback_api_mock, turn_api_mock
):
    in_office_hours.return_value = False
    callback_api_mock.app.errormax = 3
    tester.setup_state("state_enter_number")
    tester.setup_answer("state_full_name", "test name")
    tester.setup_answer("state_select_number", "different_number")
    await tester.user_input("0820001003")
    tester.assert_state(None)
    tester.assert_message("Something went wrong. Please try again later.")
    assert len(callback_api_mock.app.requests) == 3
