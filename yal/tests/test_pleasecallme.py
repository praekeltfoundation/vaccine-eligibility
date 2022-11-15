import json
from datetime import datetime
from unittest import mock

import pytest
from sanic import Sanic, response

from vaccine.models import Message
from vaccine.testing import AppTester, TState, run_sanic
from yal import config
from yal.main import Application
from yal.utils import BACK_TO_MAIN


@pytest.fixture
def tester():
    return AppTester(Application)


@pytest.fixture
async def lovelife_mock():
    Sanic.test_mode = True
    app = Sanic("mock_lovelife")
    tstate = TState()

    @app.route("/lovelife/v1/queuemessage", methods=["POST"])
    def callback(request):
        tstate.requests.append(request)
        return response.json({"call_ref_id": "1655818013000", "status": "Success"})

    async with run_sanic(app) as server:
        url = config.LOVELIFE_URL
        config.LOVELIFE_URL = f"http://{server.host}:{server.port}"
        server.tstate = tstate
        yield server
        config.LOVELIFE_URL = url


def get_rapidpro_contact(urn):
    return {
        "fields": {
            "emergency_contact": "" if ("27820001001" in urn) else "+27831231234",
        },
    }


@pytest.fixture
async def rapidpro_mock():
    Sanic.test_mode = True
    app = Sanic("mock_rapidpro")
    tstate = TState()

    @app.route("/api/v2/contacts.json", methods=["GET"])
    def get_contact(request):
        tstate.requests.append(request)

        urn = request.args.get("urn")
        contacts = [get_rapidpro_contact(urn)]

        return response.json(
            {
                "results": contacts,
                "next": None,
            },
            status=200,
        )

    @app.route("/api/v2/contacts.json", methods=["POST"])
    def update_contact(request):
        tstate.requests.append(request)
        return response.json({}, status=200)

    async with run_sanic(app) as server:
        url = config.RAPIDPRO_URL
        config.RAPIDPRO_URL = f"http://{server.host}:{server.port}"
        config.RAPIDPRO_TOKEN = "testtoken"
        server.tstate = tstate
        yield server
        config.RAPIDPRO_URL = url


@pytest.fixture
async def contentrepo_api_mock():
    Sanic.test_mode = True
    app = Sanic("contentrepo_api_mock")
    tstate = TState()

    @app.route("/api/v2/pages", methods=["GET"])
    def get_main_menu(request):
        tstate.requests.append(request)
        return response.json(
            {
                "count": 1,
                "results": [{"id": 111, "title": "Main Menu 1 💊"}],
            }
        )

    @app.route("/suggestedcontent", methods=["GET"])
    def get_suggested_content(request):
        tstate.requests.append(request)
        return response.json(
            {
                "count": 1,
                "results": [{"id": 311, "title": "Suggested Content 1"}],
            }
        )

    async with run_sanic(app) as server:
        url = config.CONTENTREPO_API_URL
        config.CONTENTREPO_API_URL = f"http://{server.host}:{server.port}"
        server.tstate = tstate
        yield server
        config.CONTENTREPO_API_URL = url


@pytest.mark.asyncio
@mock.patch("yal.pleasecallme.get_current_datetime")
async def test_start_out_of_hours_sunday_after(get_current_datetime, tester: AppTester):
    get_current_datetime.return_value = datetime(2022, 6, 19, 17, 30)
    tester.setup_state("state_please_call_start")
    await tester.user_input(session=Message.SESSION_EVENT.NEW)

    tester.assert_metadata("next_available", "2022-06-20T09:00:00")
    tester.assert_state("state_out_of_hours")
    tester.assert_message(
        "\n".join(
            [
                "NEED HELP? / *Talk to a counsellor*",
                "-----",
                "",
                "🤖 *Eish! Our loveLife counsellors are all offline right now...*",
                "",
                "A loveLife counsellor will be available from 09:00 tomorrow",
                "",
                "*1* - 🚨I need help now!",
                "*2* - See opening hours",
                "",
                "-----",
                "*Or reply:*",
                BACK_TO_MAIN,
            ]
        )
    )


@pytest.mark.asyncio
@mock.patch("yal.pleasecallme.get_current_datetime")
async def test_start_out_of_hours_sunday_before(
    get_current_datetime, tester: AppTester
):
    get_current_datetime.return_value = datetime(2022, 6, 19, 9, 30)
    tester.setup_state("state_please_call_start")
    await tester.user_input(session=Message.SESSION_EVENT.NEW)

    tester.assert_metadata("next_available", "2022-06-19T12:00:00")
    tester.assert_state("state_out_of_hours")
    tester.assert_message(
        "\n".join(
            [
                "NEED HELP? / *Talk to a counsellor*",
                "-----",
                "",
                "🤖 *Eish! Our loveLife counsellors are all offline right now...*",
                "",
                "A loveLife counsellor will be available from 12:00",
                "",
                "*1* - 🚨I need help now!",
                "*2* - See opening hours",
                "",
                "-----",
                "*Or reply:*",
                BACK_TO_MAIN,
            ]
        )
    )


@pytest.mark.asyncio
@mock.patch("yal.pleasecallme.get_current_datetime")
async def test_start_out_of_hours_weekday_before(
    get_current_datetime, tester: AppTester
):
    get_current_datetime.return_value = datetime(2022, 6, 20, 8, 30)
    tester.setup_state("state_please_call_start")
    await tester.user_input(session=Message.SESSION_EVENT.NEW)

    tester.assert_metadata("next_available", "2022-06-20T09:00:00")
    tester.assert_state("state_out_of_hours")
    tester.assert_message(
        "\n".join(
            [
                "NEED HELP? / *Talk to a counsellor*",
                "-----",
                "",
                "🤖 *Eish! Our loveLife counsellors are all offline right now...*",
                "",
                "A loveLife counsellor will be available from 09:00",
                "",
                "*1* - 🚨I need help now!",
                "*2* - See opening hours",
                "",
                "-----",
                "*Or reply:*",
                BACK_TO_MAIN,
            ]
        )
    )


@pytest.mark.asyncio
@mock.patch("yal.pleasecallme.get_current_datetime")
async def test_start_out_of_hours_weekday_after(
    get_current_datetime, tester: AppTester
):
    get_current_datetime.return_value = datetime(2022, 6, 20, 20, 30)
    tester.setup_state("state_please_call_start")
    await tester.user_input(session=Message.SESSION_EVENT.NEW)

    tester.assert_metadata("next_available", "2022-06-21T09:00:00")
    tester.assert_state("state_out_of_hours")
    tester.assert_message(
        "\n".join(
            [
                "NEED HELP? / *Talk to a counsellor*",
                "-----",
                "",
                "🤖 *Eish! Our loveLife counsellors are all offline right now...*",
                "",
                "A loveLife counsellor will be available from 09:00 tomorrow",
                "",
                "*1* - 🚨I need help now!",
                "*2* - See opening hours",
                "",
                "-----",
                "*Or reply:*",
                BACK_TO_MAIN,
            ]
        )
    )


@pytest.mark.asyncio
@mock.patch("yal.pleasecallme.get_current_datetime")
async def test_start_in_hours(get_current_datetime, tester: AppTester):
    get_current_datetime.return_value = datetime(2022, 6, 20, 17, 30)
    tester.setup_state("state_please_call_start")
    await tester.user_input(session=Message.SESSION_EVENT.NEW)

    [greeting_msg, explanation_msg] = tester.fake_worker.outbound_messages
    assert greeting_msg.content == "\n".join(
        [
            "🤖 *Say no more—I'm on it!*",
            "☝🏾 Hold tight just a sec...",
        ]
    )
    assert explanation_msg.content == "\n".join(
        [
            "📞 A trained loveLife counsellor will call you back.",
            "",
            "They'll be able to talk to you about any sex, relationship and "
            "mental health questions you may have or issues you may be facing.",
        ]
    )

    tester.assert_state("state_in_hours")


@pytest.mark.asyncio
async def test_state_out_of_hours_to_emergency(tester: AppTester, rapidpro_mock):
    tester.user.metadata["next_available"] = "2022-06-20T17:30:00"
    tester.setup_state("state_out_of_hours")
    await tester.user_input("1")
    tester.assert_state("state_emergency")


@pytest.mark.asyncio
async def test_state_out_of_hours_to_open_hours(tester: AppTester, rapidpro_mock):
    tester.user.metadata["next_available"] = "2022-06-20T17:30:00"
    tester.setup_state("state_out_of_hours")
    await tester.user_input("2")
    tester.assert_state("state_open_hours")


@pytest.mark.asyncio
async def test_state_open_hours_chose_to_call_when_open(
    tester: AppTester, rapidpro_mock
):
    tester.setup_state("state_open_hours")
    await tester.user_input("2")
    tester.assert_state("state_in_hours")

    [greeting_msg, explanation_msg] = tester.fake_worker.outbound_messages
    assert greeting_msg.content == "\n".join(
        [
            "🤖 *Say no more—I'm on it!*",
            "☝🏾 Hold tight just a sec...",
        ]
    )
    assert explanation_msg.content == "\n".join(
        [
            "📞 A trained loveLife counsellor will call you back.",
            "",
            "They'll be able to talk to you about any sex, relationship and "
            "mental health questions you may have or issues you may be facing.",
        ]
    )


@pytest.mark.asyncio
async def test_callback_check_scheduled_if_out_of_hours(
    tester: AppTester, lovelife_mock, rapidpro_mock
):
    tester.user.metadata["next_available"] = "2022-06-20T09:00:00"
    tester.setup_state("state_in_hours")
    await tester.user_input("1")
    tester.assert_state("state_callback_confirmation")

    [req] = lovelife_mock.tstate.requests
    assert req.json == {
        "PhoneNumber": "+27820001001",
        "SourceSystem": "Bwise by Young Africa live WhatsApp bot",
    }

    assert len(rapidpro_mock.tstate.requests) == 1
    request = rapidpro_mock.tstate.requests[0]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {"callback_check_time": "2022-06-20T11:00:00"},
    }


@pytest.mark.asyncio
@mock.patch("yal.pleasecallme.get_current_datetime")
async def test_state_in_hours(
    get_current_datetime, tester: AppTester, lovelife_mock, rapidpro_mock
):
    get_current_datetime.return_value = datetime(2022, 6, 19, 17, 30)
    tester.setup_state("state_in_hours")
    await tester.user_input("1")
    tester.assert_state("state_callback_confirmation")

    [req] = lovelife_mock.tstate.requests
    assert req.json == {
        "PhoneNumber": "+27820001001",
        "SourceSystem": "Bwise by Young Africa live WhatsApp bot",
    }

    assert len(rapidpro_mock.tstate.requests) == 1
    request = rapidpro_mock.tstate.requests[0]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {"callback_check_time": "2022-06-19T19:30:00"},
    }


@pytest.mark.asyncio
async def test_state_callback_confirmation(tester: AppTester, rapidpro_mock):
    tester.setup_state("state_callback_confirmation")
    await tester.user_input("1")

    tester.assert_state("state_start")


@pytest.mark.asyncio
async def test_state_callback_confirmation_need_help(tester: AppTester, rapidpro_mock):
    tester.setup_state("state_callback_confirmation")
    await tester.user_input("2")

    tester.assert_state("state_emergency")


@pytest.mark.asyncio
async def test_state_callback_confirmation_opening_hours(
    tester: AppTester, rapidpro_mock
):
    tester.setup_state("state_callback_confirmation")
    await tester.user_input("3")

    tester.assert_state("state_open_hours")


@pytest.mark.asyncio
async def test_state_in_hours_specify(tester: AppTester, rapidpro_mock):
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

    tester.assert_answer("state_specify_msisdn", "0831231234")


@pytest.mark.asyncio
async def test_state_specify_msisdn_country_code(tester: AppTester):
    tester.setup_state("state_specify_msisdn")
    await tester.user_input("27831231234")
    tester.assert_state("state_confirm_specified_msisdn")

    tester.assert_answer("state_specify_msisdn", "27831231234")


@pytest.mark.asyncio
async def test_state_specify_msisdn_country_code_plus(tester: AppTester):
    tester.setup_state("state_specify_msisdn")
    await tester.user_input("+27831231234")
    tester.assert_state("state_confirm_specified_msisdn")

    tester.assert_answer("state_specify_msisdn", "+27831231234")


@pytest.mark.asyncio
async def test_state_confirm_specified_msisdn_incorrect(
    tester: AppTester, rapidpro_mock
):
    tester.setup_state("state_confirm_specified_msisdn")
    tester.setup_answer("state_specify_msisdn", "0831231234")
    await tester.user_input("2")
    tester.assert_state("state_specify_msisdn")


@pytest.mark.asyncio
async def test_state_confirm_specified_msisdn(tester: AppTester, rapidpro_mock):
    tester.setup_state("state_confirm_specified_msisdn")
    tester.setup_answer("state_specify_msisdn", "0831231234")
    await tester.user_input("1")
    tester.assert_state("state_ask_to_save_emergency_number")


@pytest.mark.asyncio
@mock.patch("yal.pleasecallme.get_current_datetime")
async def test_state_ask_to_save_emergency_number(
    get_current_datetime, tester: AppTester, lovelife_mock, rapidpro_mock
):
    get_current_datetime.return_value = datetime(2022, 6, 19, 17, 30)
    tester.setup_state("state_ask_to_save_emergency_number")
    tester.setup_answer("state_specify_msisdn", "+27831231234")
    await tester.user_input("2")
    tester.assert_state("state_callback_confirmation")

    [req] = lovelife_mock.tstate.requests
    assert req.json == {
        "PhoneNumber": "+27831231234",
        "SourceSystem": "Bwise by Young Africa live WhatsApp bot",
    }

    assert len(rapidpro_mock.tstate.requests) == 1
    request = rapidpro_mock.tstate.requests[0]
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

    [req] = lovelife_mock.tstate.requests
    assert req.json == {
        "PhoneNumber": "+27831231234",
        "SourceSystem": "Bwise by Young Africa live WhatsApp bot",
    }

    assert len(rapidpro_mock.tstate.requests) == 2
    request = rapidpro_mock.tstate.requests[0]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {"emergency_contact": "+27831231234"},
    }
    request = rapidpro_mock.tstate.requests[1]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {"callback_check_time": "2022-06-19T19:30:00"},
    }


@pytest.mark.asyncio
@mock.patch("yal.pleasecallme.get_current_datetime")
async def test_state_callback_response_handles_call_received(
    get_current_datetime, tester: AppTester, rapidpro_mock, contentrepo_api_mock
):
    get_current_datetime.return_value = datetime(2022, 6, 19, 17, 30)
    tester.setup_state("state_handle_callback_check_response")
    await tester.user_input("I got the call")

    assert len(rapidpro_mock.tstate.requests) == 1
    [request] = rapidpro_mock.tstate.requests
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {
            "last_mainmenu_time": "2022-06-19T17:30:00",
        },
    }

    tester.assert_state("state_collect_call_feedback")


@pytest.mark.asyncio
async def test_state_callback_response_handles_no_call(
    tester: AppTester, rapidpro_mock
):
    tester.setup_state("state_handle_callback_check_response")
    await tester.user_input("No call yet")

    assert len(rapidpro_mock.tstate.requests) == 0

    tester.assert_num_messages(1)
    [msg] = tester.fake_worker.outbound_messages
    assert msg.content == "\n".join(
        [
            "🤖 *Eish! Sorry about that!*",
            "",
            "Something must have gone wrong on our side. Apologies for that.",
        ]
    )

    tester.assert_state("state_ask_to_call_again")


@pytest.mark.asyncio
async def test_state_callback_response_handles_missed_call(
    tester: AppTester, rapidpro_mock
):
    tester.setup_state("state_handle_callback_check_response")
    await tester.user_input("I missed the call")

    assert len(rapidpro_mock.tstate.requests) == 0
    tester.assert_state("state_ask_to_call_again")


@pytest.mark.asyncio
async def test_state_ask_to_call_again_yes(tester: AppTester, rapidpro_mock):
    tester.setup_state("state_ask_to_call_again")

    await tester.user_input("ok")

    tester.assert_state("state_retry_callback_choose_number")
    tester.assert_num_messages(1)

    assert len(rapidpro_mock.tstate.requests) == 0


@pytest.mark.asyncio
async def test_state_ask_to_call_again_another_way(tester: AppTester, rapidpro_mock):
    tester.setup_state("state_ask_to_call_again")

    await tester.user_input("Get help another way")

    tester.assert_state("state_contact_bwise")
    tester.assert_num_messages(1)

    assert len(rapidpro_mock.tstate.requests) == 0


@pytest.mark.asyncio
async def test_state_ask_to_call_again_no(tester: AppTester, rapidpro_mock):
    tester.setup_state("state_ask_to_call_again")

    await tester.user_input("No, thanks")

    tester.assert_state("state_help_no_longer_needed")
    tester.assert_num_messages(1)

    assert len(rapidpro_mock.tstate.requests) == 0


@pytest.mark.asyncio
@mock.patch("yal.pleasecallme.get_current_datetime")
async def test_state_retry_callback_choose_number_whatsapp(
    get_current_datetime, tester: AppTester, lovelife_mock, rapidpro_mock
):
    get_current_datetime.return_value = datetime(2022, 6, 19, 17, 30)
    tester.setup_state("state_retry_callback_choose_number")

    await tester.user_input("Whatsapp number")

    tester.assert_state("state_callback_confirmation")

    [req] = lovelife_mock.tstate.requests
    assert req.json == {
        "PhoneNumber": "+27820001001",
        "SourceSystem": "Bwise by Young Africa live WhatsApp bot",
    }

    assert len(rapidpro_mock.tstate.requests) == 1
    request = rapidpro_mock.tstate.requests[0]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {"callback_check_time": "2022-06-19T19:30:00"},
    }


@pytest.mark.asyncio
async def test_state_retry_callback_choose_number_saved_and_exists(
    tester: AppTester, rapidpro_mock
):
    tester.setup_user_address("27820001002")
    tester.setup_state("state_retry_callback_choose_number")

    await tester.user_input("Previously saved")

    tester.assert_state("state_offer_saved_emergency_contact")

    assert len(rapidpro_mock.tstate.requests) == 1
    tester.assert_message(
        "\n".join(
            [
                "NEED HELP? / *Talk to a counsellor*",
                "-----",
                "",
                "🤖 *Is this the right number?*",
                "",
                "+27831231234",
                "",
                "*1* - Yes, that's it",
                "*2* - No, it's wrong",
                "",
                "-----",
                "*Or reply:*",
                BACK_TO_MAIN,
            ]
        )
    )


@pytest.mark.asyncio
async def test_state_retry_callback_choose_number_saved_no_number_found(
    tester: AppTester, rapidpro_mock
):
    tester.setup_state("state_retry_callback_choose_number")

    await tester.user_input("Previously saved")

    tester.assert_state("state_offer_saved_emergency_contact")

    assert len(rapidpro_mock.tstate.requests) == 1
    tester.assert_message(
        "\n".join(
            [
                "NEED HELP? / *Talk to a counsellor*",
                "-----",
                "",
                "🤖 *Whoops! I don't have another number saved for you.*",
                "*Which number should we use?*",
                "",
                "*1* - My Whatsapp number",
                "*2* - Another number",
                "",
                "----",
                "*Or reply:*",
                BACK_TO_MAIN,
            ]
        )
    )


@pytest.mark.asyncio
@mock.patch("yal.pleasecallme.get_current_datetime")
async def test_retry_callback_no_number_found_whatsapp(
    get_current_datetime, tester: AppTester, lovelife_mock, rapidpro_mock
):
    get_current_datetime.return_value = datetime(2022, 6, 19, 17, 30)
    tester.setup_state("state_offer_saved_emergency_contact")
    await tester.user_input("Whatsapp number")

    tester.assert_state("state_callback_confirmation")

    [req] = lovelife_mock.tstate.requests
    assert req.json == {
        "PhoneNumber": "+27820001001",
        "SourceSystem": "Bwise by Young Africa live WhatsApp bot",
    }

    assert len(rapidpro_mock.tstate.requests) == 2
    request = rapidpro_mock.tstate.requests[1]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {"callback_check_time": "2022-06-19T19:30:00"},
    }


@pytest.mark.asyncio
@mock.patch("yal.pleasecallme.get_current_datetime")
async def test_retry_callback_no_number_found_another_number(
    get_current_datetime, tester: AppTester, lovelife_mock, rapidpro_mock
):
    get_current_datetime.return_value = datetime(2022, 6, 19, 17, 30)
    tester.setup_state("state_offer_saved_emergency_contact")
    await tester.user_input("Another number")

    tester.assert_state("state_specify_msisdn")

    assert len(rapidpro_mock.tstate.requests) == 1


@pytest.mark.asyncio
async def test_state_help_no_longer_needed_got_help(tester: AppTester, rapidpro_mock):
    tester.setup_state("state_help_no_longer_needed")

    await tester.user_input("Yes, I got help")

    tester.assert_state("state_got_help")
    tester.assert_num_messages(1)

    assert len(rapidpro_mock.tstate.requests) == 1
    request = rapidpro_mock.tstate.requests[0]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {"callback_abandon_reason": "got help"},
    }


@pytest.mark.asyncio
async def test_state_help_no_longer_needed_too_long(tester: AppTester, rapidpro_mock):
    tester.setup_state("state_help_no_longer_needed")

    await tester.user_input("This way is too long")

    tester.assert_state("state_too_long")
    tester.assert_num_messages(1)

    assert len(rapidpro_mock.tstate.requests) == 1
    request = rapidpro_mock.tstate.requests[0]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {"callback_abandon_reason": "too long"},
    }


@pytest.mark.asyncio
async def test_state_help_no_longer_needed_changed_mind(
    tester: AppTester, rapidpro_mock
):
    tester.setup_state("state_help_no_longer_needed")

    await tester.user_input("I've changed my mind")

    tester.assert_state("state_changed_mind")
    tester.assert_num_messages(1)

    assert len(rapidpro_mock.tstate.requests) == 1
    request = rapidpro_mock.tstate.requests[0]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {"callback_abandon_reason": "changed mind"},
    }


@pytest.mark.asyncio
async def test_state_too_long(tester: AppTester, rapidpro_mock):
    tester.setup_state("state_too_long")

    await tester.user_input("Get help another way")

    tester.assert_state("state_contact_bwise")
    tester.assert_num_messages(1)

    assert len(rapidpro_mock.tstate.requests) == 1
    request = rapidpro_mock.tstate.requests[0]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {"callback_abandon_reason": "too long"},
    }


@pytest.mark.asyncio
async def test_state_changed_mind(tester: AppTester, rapidpro_mock):
    tester.setup_state("state_changed_mind")

    await tester.user_input("Get help another way")

    tester.assert_state("state_contact_bwise")
    tester.assert_num_messages(1)

    assert len(rapidpro_mock.tstate.requests) == 1
    request = rapidpro_mock.tstate.requests[0]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {"callback_abandon_reason": "changed mind"},
    }


@pytest.mark.asyncio
async def test_state_contact_bwise_facebook(tester: AppTester):
    config.CONTENTREPO_API_URL = "https://contenrepo/"
    tester.setup_state("state_contact_bwise")

    await tester.user_input("Facebook")

    tester.assert_state("state_facebook_page")
    tester.assert_num_messages(1)
    # TODO: Add image to content repo
    # [msg] = tester.fake_worker.outbound_messages
    # assert msg.helper_metadata == {
    #     "image": "https://contenrepo/media/original_images/"
    #               "Screenshot 2022-06-07 at 09.29.20.png"
    # }


@pytest.mark.asyncio
async def test_state_contact_bwise_twitter(tester: AppTester):
    config.CONTENTREPO_API_URL = "https://contenrepo/"
    tester.setup_state("state_contact_bwise")

    await tester.user_input("Twitter")

    tester.assert_state("state_twitter_page")
    tester.assert_num_messages(1)
    # TODO: Add image to content repo
    # [msg] = tester.fake_worker.outbound_messages
    # assert msg.helper_metadata == {
    #     "image": "https://contenrepo/media/original_images/"
    #               "Screenshot 2022-06-07 at 09.56.48.png"
    # }


@pytest.mark.asyncio
async def test_state_contact_bwise_website(tester: AppTester):
    config.CONTENTREPO_API_URL = "https://contenrepo/"
    tester.setup_state("state_contact_bwise")

    await tester.user_input("Website")

    tester.assert_state("state_website")
    tester.assert_num_messages(1)
    # TODO: Add image to content repo
    # [msg] = tester.fake_worker.outbound_messages
    # assert msg.helper_metadata == {
    #     "image": "https://contenrepo/media/original_images/"
    #               "Screenshot 2022-06-06 at 15.02.53.png"
    # }


@pytest.mark.asyncio
async def state_collect_call_feedback_helpful(tester: AppTester):
    tester.setup_state("state_collect_call_feedback")
    await tester.user_input("Yes, very helpful")
    tester.assert_state("state_call_helpful")


@pytest.mark.asyncio
async def state_collect_call_helpful_aaq(tester: AppTester):
    tester.setup_state("state_call_helpful")
    await tester.user_input("Ask a question")
    tester.assert_state("state_aaq_start")


@pytest.mark.asyncio
async def state_collect_call_helpful_update_info(tester: AppTester):
    tester.setup_state("state_call_helpful")
    await tester.user_input("Update your info")
    tester.assert_state("state_display_preferences")


@pytest.mark.asyncio
@mock.patch("yal.pleasecallme.get_current_datetime")
async def state_collect_call_helpful_goto_counsellor(
    get_current_datetime, tester: AppTester
):
    get_current_datetime.return_value = datetime(2022, 6, 19, 17, 30)
    tester.setup_state("state_call_helpful")
    await tester.user_input("Talk to a counsellor")
    tester.assert_state("state_out_of_hours")


@pytest.mark.asyncio
async def state_collect_call_feedback_not_helpful(tester: AppTester):
    tester.setup_state("state_collect_call_feedback")
    await tester.user_input("No, not really")
    tester.assert_state("state_call_not_helpful_feedback")


@pytest.mark.asyncio
async def state_call_not_helpful_feedback(tester: AppTester):
    tester.setup_state("state_call_not_helpful_feedback")
    await tester.user_input("Some detailed feedback")
    tester.assert_state("state_call_not_helpful_try_again")


@pytest.mark.asyncio
@mock.patch("yal.pleasecallme.get_current_datetime")
async def state_call_not_helpful_try_again(get_current_datetime, tester: AppTester):
    get_current_datetime.return_value = datetime(2022, 6, 19, 17, 30)
    tester.setup_state("state_call_not_helpful_try_again")
    await tester.user_input("Yes, It might help")
    tester.assert_state("state_out_of_hours")


@pytest.mark.asyncio
async def state_call_not_helpful_try_again_declined(tester: AppTester):
    tester.setup_state("state_call_not_helpful_try_again")
    await tester.user_input("No, thanks")
    tester.assert_state("state_call_not_helpful_try_again_declined")


@pytest.mark.asyncio
async def state_call_not_helpful_try_again_declined_to_aaq(tester: AppTester):
    tester.setup_state("state_call_not_helpful_try_again_declined")
    await tester.user_input("Ask a question")
    tester.assert_state("state_aaq_start")


@pytest.mark.asyncio
async def state_call_not_helpful_try_again_declined_to_update(tester: AppTester):
    tester.setup_state("state_call_not_helpful_try_again_declined")
    await tester.user_input("Update your info")
    tester.assert_state("state_display_preferences")
