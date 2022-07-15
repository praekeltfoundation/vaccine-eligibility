from datetime import datetime
from unittest import mock

import pytest
import json
from sanic import Sanic, response

from vaccine.models import Message
from vaccine.testing import AppTester
from yal import config
from yal.main import Application


@pytest.fixture
def tester():
    return AppTester(Application)


@pytest.fixture
async def lovelife_mock(sanic_client):
    Sanic.test_mode = True
    app = Sanic("mock_lovelife")
    app.requests = []

    @app.route("/lovelife/v1/queuemessage", methods=["POST"])
    def callback(request):
        app.requests.append(request)
        return response.json({"call_ref_id": "1655818013000", "status": "Success"})

    client = await sanic_client(app)
    url = config.LOVELIFE_URL
    config.LOVELIFE_URL = f"http://{client.host}:{client.port}"
    yield client
    config.LOVELIFE_URL = url


@pytest.fixture
async def rapidpro_mock(sanic_client):
    Sanic.test_mode = True
    app = Sanic("mock_rapidpro")
    app.requests = []

    @app.route("/api/v2/contacts.json", methods=["POST"])
    def update_contact(request):
        app.requests.append(request)
        return response.json({}, status=200)

    client = await sanic_client(app)
    url = config.RAPIDPRO_URL
    config.RAPIDPRO_URL = f"http://{client.host}:{client.port}"
    config.RAPIDPRO_TOKEN = "testtoken"
    yield client
    config.RAPIDPRO_URL = url


@pytest.mark.asyncio
@mock.patch("yal.pleasecallme.get_current_datetime")
async def test_start_out_of_hours(get_current_datetime, tester: AppTester):
    get_current_datetime.return_value = datetime(2022, 6, 19, 17, 30)
    tester.setup_state("state_please_call_start")
    await tester.user_input(session=Message.SESSION_EVENT.NEW)

    tester.assert_state("state_out_of_hours")


@pytest.mark.asyncio
@mock.patch("yal.pleasecallme.get_current_datetime")
async def test_start_in_hours(get_current_datetime, tester: AppTester):
    get_current_datetime.return_value = datetime(2022, 6, 20, 17, 30)
    tester.setup_state("state_please_call_start")
    await tester.user_input(session=Message.SESSION_EVENT.NEW)

    [greeting_msg] = tester.fake_worker.outbound_messages
    assert greeting_msg.content == "\n".join(
        [
            "👩🏾 *Say no more—I'm on it!*",
            "☝🏾 Hold tight just a sec...",
        ]
    )

    tester.assert_state("state_in_hours")


@pytest.mark.asyncio
async def test_state_out_of_hours(tester: AppTester):
    tester.setup_state("state_out_of_hours")
    await tester.user_input("1")
    tester.assert_state("state_open_hours")


@pytest.mark.asyncio
@mock.patch("yal.pleasecallme.get_current_datetime")
async def test_state_in_hours(get_current_datetime, tester: AppTester, lovelife_mock, rapidpro_mock):
    get_current_datetime.return_value = datetime(2022, 6, 19, 17, 30)
    tester.setup_state("state_in_hours")
    await tester.user_input("1")
    tester.assert_state("state_callback_confirmation")

    [req] = lovelife_mock.app.requests
    assert req.json == {
        "PhoneNumber": "+27820001001",
        "SourceSystem": "Bwise by Young Africa live WhatsApp bot",
    }

    assert len(rapidpro_mock.app.requests) == 1
    request = rapidpro_mock.app.requests[0]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {"callback_check_time": "2022-06-19T19:30:00"},
    }


@pytest.mark.asyncio
async def test_state_callback_confirmation(tester: AppTester):
    tester.setup_state("state_callback_confirmation")
    await tester.user_input("1")

    tester.assert_state("state_start")


@pytest.mark.asyncio
async def test_state_in_hours_specify(tester: AppTester):
    tester.setup_state("state_in_hours")
    await tester.user_input("2")
    tester.assert_state("state_specify_msisdn")


@pytest.mark.asyncio
async def test_state_specify_msisdn_invalid(tester: AppTester):
    tester.setup_state("state_specify_msisdn")
    await tester.user_input("invalid")
    tester.assert_state("state_specify_msisdn")


@pytest.mark.asyncio
async def test_state_specify_msisdn(tester: AppTester):
    tester.setup_state("state_specify_msisdn")
    await tester.user_input("0831231234")
    tester.assert_state("state_confirm_specified_msisdn")


@pytest.mark.asyncio
async def test_state_confirm_specified_msisdn_incorrect(tester: AppTester):
    tester.setup_state("state_confirm_specified_msisdn")
    tester.setup_answer("state_specify_msisdn", "0831231234")
    await tester.user_input("2")
    tester.assert_state("state_specify_msisdn")


@pytest.mark.asyncio
async def test_state_confirm_specified_msisdn(tester: AppTester):
    tester.setup_state("state_confirm_specified_msisdn")
    tester.setup_answer("state_specify_msisdn", "0831231234")
    await tester.user_input("1")
    tester.assert_state("state_ask_to_save_emergency_number")


@pytest.mark.asyncio
@mock.patch("yal.pleasecallme.get_current_datetime")
async def test_state_ask_to_save_emergency_number(get_current_datetime, tester: AppTester, lovelife_mock, rapidpro_mock):
    get_current_datetime.return_value = datetime(2022, 6, 19, 17, 30)
    tester.setup_state("state_ask_to_save_emergency_number")
    tester.setup_answer("state_specify_msisdn", "+27831231234")
    await tester.user_input("2")
    tester.assert_state("state_callback_confirmation")

    [req] = lovelife_mock.app.requests
    assert req.json == {
        "PhoneNumber": "+27831231234",
        "SourceSystem": "Bwise by Young Africa live WhatsApp bot",
    }

    assert len(rapidpro_mock.app.requests) == 1
    request = rapidpro_mock.app.requests[0]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {"callback_check_time": "2022-06-19T19:30:00"},
    }


@pytest.mark.asyncio
@mock.patch("yal.pleasecallme.get_current_datetime")
async def test_state_save_emergency_contact(
    get_current_datetime, tester: AppTester, lovelife_mock, rapidpro_mock
):
    get_current_datetime.return_value = datetime(2022, 6, 19, 17, 30)
    tester.setup_state("state_ask_to_save_emergency_number")
    tester.setup_answer("state_specify_msisdn", "+27831231234")
    await tester.user_input("1")
    tester.assert_state("state_callback_confirmation")

    [req] = lovelife_mock.app.requests
    assert req.json == {
        "PhoneNumber": "+27831231234",
        "SourceSystem": "Bwise by Young Africa live WhatsApp bot",
    }

    assert len(rapidpro_mock.app.requests) == 2
    request = rapidpro_mock.app.requests[0]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {"emergency_contact": "+27831231234"},
    }
    request = rapidpro_mock.app.requests[1]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {"callback_check_time": "2022-06-19T19:30:00"},
    }
