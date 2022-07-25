import json
from datetime import datetime
from unittest import mock

import pytest
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


def get_rapidpro_contact(urn):
    return {
        "fields": {
            "emergency_contact": "" if ("27820001001" in urn) else "+27831231234",
        },
    }


@pytest.fixture
async def rapidpro_mock(sanic_client):
    Sanic.test_mode = True
    app = Sanic("mock_rapidpro")
    app.requests = []

    @app.route("/api/v2/contacts.json", methods=["GET"])
    def get_contact(request):
        app.requests.append(request)

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
        app.requests.append(request)
        return response.json({}, status=200)

    client = await sanic_client(app)
    url = config.RAPIDPRO_URL
    config.RAPIDPRO_URL = f"http://{client.host}:{client.port}"
    config.RAPIDPRO_TOKEN = "testtoken"
    yield client
    config.RAPIDPRO_URL = url


@pytest.fixture
async def contentrepo_api_mock(sanic_client):
    Sanic.test_mode = True
    app = Sanic("contentrepo_api_mock")
    app.requests = []

    @app.route("/api/v2/pages", methods=["GET"])
    def get_main_menu(request):
        app.requests.append(request)
        return response.json(
            {
                "count": 1,
                "results": [{"id": 111, "title": "Main Menu 1 💊"}],
            }
        )

    @app.route("/suggestedcontent", methods=["GET"])
    def get_suggested_content(request):
        app.requests.append(request)
        return response.json(
            {
                "count": 1,
                "results": [{"id": 311, "title": "Suggested Content 1"}],
            }
        )

    client = await sanic_client(app)
    url = config.CONTENTREPO_API_URL
    config.CONTENTREPO_API_URL = f"http://{client.host}:{client.port}"
    yield client
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
                "🆘HELP!",
                "*Please call me*",
                "-----",
                "",
                "*👩🏾 Eish! Our loveLife counsellors are all offline right now...*",
                "",
                "A loveLife counsellor will be available from 09:00 tomorrow",
                "",
                "*1* - 🚨I need help now!",
                "*2* - See opening hours",
                "",
                "-----",
                "*Or reply:*",
                "*0* - 🏠Back to Main *MENU*",
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
                "🆘HELP!",
                "*Please call me*",
                "-----",
                "",
                "*👩🏾 Eish! Our loveLife counsellors are all offline right now...*",
                "",
                "A loveLife counsellor will be available from 12:00",
                "",
                "*1* - 🚨I need help now!",
                "*2* - See opening hours",
                "",
                "-----",
                "*Or reply:*",
                "*0* - 🏠Back to Main *MENU*",
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
                "🆘HELP!",
                "*Please call me*",
                "-----",
                "",
                "*👩🏾 Eish! Our loveLife counsellors are all offline right now...*",
                "",
                "A loveLife counsellor will be available from 09:00",
                "",
                "*1* - 🚨I need help now!",
                "*2* - See opening hours",
                "",
                "-----",
                "*Or reply:*",
                "*0* - 🏠Back to Main *MENU*",
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
                "🆘HELP!",
                "*Please call me*",
                "-----",
                "",
                "*👩🏾 Eish! Our loveLife counsellors are all offline right now...*",
                "",
                "A loveLife counsellor will be available from 09:00 tomorrow",
                "",
                "*1* - 🚨I need help now!",
                "*2* - See opening hours",
                "",
                "-----",
                "*Or reply:*",
                "*0* - 🏠Back to Main *MENU*",
            ]
        )
    )


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
async def test_state_out_of_hours_to_emergency(tester: AppTester):
    tester.user.metadata["next_available"] = "2022-06-20T17:30:00"
    tester.setup_state("state_out_of_hours")
    await tester.user_input("1")
    tester.assert_state("state_emergency")


@pytest.mark.asyncio
async def test_state_out_of_hours_to_open_hours(tester: AppTester):
    tester.user.metadata["next_available"] = "2022-06-20T17:30:00"
    tester.setup_state("state_out_of_hours")
    await tester.user_input("2")
    tester.assert_state("state_open_hours")


@pytest.mark.asyncio
async def test_state_open_hours_chose_to_call_when_open(tester: AppTester):
    tester.setup_state("state_open_hours")
    await tester.user_input("2")
    tester.assert_state("state_in_hours")

    [greeting_msg] = tester.fake_worker.outbound_messages
    assert greeting_msg.content == "\n".join(
        [
            "👩🏾 *Say no more—I'm on it!*",
            "☝🏾 Hold tight just a sec...",
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

    [req] = lovelife_mock.app.requests
    assert req.json == {
        "PhoneNumber": "+27820001001",
        "SourceSystem": "Bwise by Young Africa live WhatsApp bot",
    }

    assert len(rapidpro_mock.app.requests) == 1
    request = rapidpro_mock.app.requests[0]
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
async def test_state_ask_to_save_emergency_number(
    get_current_datetime, tester: AppTester, lovelife_mock, rapidpro_mock
):
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


@pytest.mark.asyncio
@mock.patch("yal.mainmenu.get_current_datetime")
async def test_state_callback_response_handles_call_received(
    get_current_datetime, tester: AppTester, rapidpro_mock, contentrepo_api_mock
):
    get_current_datetime.return_value = datetime(2022, 6, 19, 17, 30)
    tester.setup_state("state_handle_callback_check_response")
    await tester.user_input(
        session=Message.SESSION_EVENT.NEW, content="yes, i got a callback"
    )

    assert len(rapidpro_mock.app.requests) == 2
    [request1, request2] = rapidpro_mock.app.requests
    assert json.loads(request1.body.decode("utf-8")) == {
        "fields": {"callback_check_sent": ""},
    }
    assert json.loads(request2.body.decode("utf-8")) == {
        "fields": {
            "last_mainmenu_time": "2022-06-19T17:30:00",
            "suggested_text": "*6* - Suggested Content 1",
        },
    }

    tester.assert_state("state_mainmenu")
    assert len(contentrepo_api_mock.app.requests) == 3


@pytest.mark.asyncio
async def test_state_callback_response_handles_no_call(
    tester: AppTester, rapidpro_mock
):
    tester.setup_state("state_handle_callback_check_response")
    await tester.user_input(
        session=Message.SESSION_EVENT.NEW, content="no i'm still waiting"
    )

    assert len(rapidpro_mock.app.requests) == 1
    request = rapidpro_mock.app.requests[0]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {"callback_check_sent": ""},
    }

    tester.assert_num_messages(1)
    [msg] = tester.fake_worker.outbound_messages
    assert msg.content == "\n".join(
        [
            "👩🏾 *Eish! Sorry about that!*",
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
    await tester.user_input(
        session=Message.SESSION_EVENT.NEW, content="yes, but i missed it"
    )

    assert len(rapidpro_mock.app.requests) == 1
    request = rapidpro_mock.app.requests[0]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {"callback_check_sent": ""},
    }

    tester.assert_state("state_ask_to_call_again")


@pytest.mark.asyncio
async def test_state_ask_to_call_again_yes(tester: AppTester, rapidpro_mock):
    tester.setup_state("state_ask_to_call_again")

    await tester.user_input("ok")

    tester.assert_state("state_retry_callback_choose_number")
    tester.assert_num_messages(1)

    assert len(rapidpro_mock.app.requests) == 0


@pytest.mark.asyncio
async def test_state_ask_to_call_again_another_way(tester: AppTester, rapidpro_mock):
    tester.setup_state("state_ask_to_call_again")

    await tester.user_input("Get help another way")

    tester.assert_state("state_contact_bwise")
    tester.assert_num_messages(1)

    assert len(rapidpro_mock.app.requests) == 0


@pytest.mark.asyncio
async def test_state_ask_to_call_again_no(tester: AppTester, rapidpro_mock):
    tester.setup_state("state_ask_to_call_again")

    await tester.user_input("No, thanks")

    tester.assert_state("state_help_no_longer_needed")
    tester.assert_num_messages(1)

    assert len(rapidpro_mock.app.requests) == 0


@pytest.mark.asyncio
@mock.patch("yal.pleasecallme.get_current_datetime")
async def test_state_retry_callback_choose_number_whatsapp(
    get_current_datetime, tester: AppTester, lovelife_mock, rapidpro_mock
):
    get_current_datetime.return_value = datetime(2022, 6, 19, 17, 30)
    tester.setup_state("state_retry_callback_choose_number")

    await tester.user_input("Whatsapp number")

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
async def test_state_retry_callback_choose_number_saved_and_exists(
    tester: AppTester, rapidpro_mock
):
    tester.setup_user_address("27820001002")
    tester.setup_state("state_retry_callback_choose_number")

    await tester.user_input("Previously saved")

    tester.assert_state("state_offer_saved_emergency_contact")

    assert len(rapidpro_mock.app.requests) == 1
    tester.assert_message(
        "\n".join(
            [
                "🆘HELP!",
                "*Please call me*",
                "-----",
                "",
                "*👩🏾Is this the right number?*",
                "",
                "+27831231234",
                "",
                "*1* - Yes, that's it",
                "*2* - No, it's wrong",
                "",
                "-----",
                "*Or reply:*",
                "*0* - 🏠Back to Main *MENU*",
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

    assert len(rapidpro_mock.app.requests) == 1
    tester.assert_message(
        "\n".join(
            [
                "🆘HELP!",
                "*Please call me*",
                "-----",
                "",
                "*👩🏾 Whoops! I don't have another number saved for you.*",
                "*Which number should we use?*",
                "",
                "*1* - My Whatsapp number",
                "*2* - Another number",
                "",
                "----",
                "*Or reply:*",
                "*0* - 🏠 Back to Main MENU",
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

    [req] = lovelife_mock.app.requests
    assert req.json == {
        "PhoneNumber": "+27820001001",
        "SourceSystem": "Bwise by Young Africa live WhatsApp bot",
    }

    assert len(rapidpro_mock.app.requests) == 2
    request = rapidpro_mock.app.requests[1]
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

    assert len(rapidpro_mock.app.requests) == 1


@pytest.mark.asyncio
async def test_state_help_no_longer_needed_got_help(tester: AppTester, rapidpro_mock):
    tester.setup_state("state_help_no_longer_needed")

    await tester.user_input("Yes, I got help")

    tester.assert_state("state_got_help")
    tester.assert_num_messages(1)

    assert len(rapidpro_mock.app.requests) == 1
    request = rapidpro_mock.app.requests[0]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {"callback_abandon_reason": "got help"},
    }


@pytest.mark.asyncio
async def test_state_help_no_longer_needed_too_long(tester: AppTester, rapidpro_mock):
    tester.setup_state("state_help_no_longer_needed")

    await tester.user_input("This way is too long")

    tester.assert_state("state_too_long")
    tester.assert_num_messages(1)

    assert len(rapidpro_mock.app.requests) == 1
    request = rapidpro_mock.app.requests[0]
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

    assert len(rapidpro_mock.app.requests) == 1
    request = rapidpro_mock.app.requests[0]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {"callback_abandon_reason": "changed mind"},
    }


@pytest.mark.asyncio
async def test_state_too_long(tester: AppTester, rapidpro_mock):
    tester.setup_state("state_too_long")

    await tester.user_input("Get help another way")

    tester.assert_state("state_contact_bwise")
    tester.assert_num_messages(1)

    assert len(rapidpro_mock.app.requests) == 1
    request = rapidpro_mock.app.requests[0]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {"callback_abandon_reason": "too long"},
    }


@pytest.mark.asyncio
async def test_state_changed_mind(tester: AppTester, rapidpro_mock):
    tester.setup_state("state_changed_mind")

    await tester.user_input("Get help another way")

    tester.assert_state("state_contact_bwise")
    tester.assert_num_messages(1)

    assert len(rapidpro_mock.app.requests) == 1
    request = rapidpro_mock.app.requests[0]
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
