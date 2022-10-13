import json
from datetime import datetime
from unittest import mock

import pytest
from sanic import Sanic, response

from vaccine.models import Message
from vaccine.testing import AppTester, TState, run_sanic
from yal import config
from yal.main import Application


@pytest.fixture
def tester():
    return AppTester(Application)


def get_rapidpro_contact(urn):
    return {
        "fields": {
            "onboarding_reminder_sent": "True",
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
        config.AWS_MEDIA_URL = "http://aws.com"
        server.tstate = tstate
        yield server
        config.RAPIDPRO_URL = url


@pytest.mark.asyncio
@mock.patch("yal.onboarding.get_current_datetime")
async def test_state_persona_name(
    get_current_datetime, tester: AppTester, rapidpro_mock
):
    get_current_datetime.return_value = datetime(2022, 6, 19, 17, 30)
    tester.setup_state("state_persona_name")

    await tester.user_input("Nurse Joy")

    tester.assert_state("state_persona_emoji")
    tester.assert_num_messages(1)

    [msg] = tester.fake_worker.outbound_messages
    assert msg.content == "\n".join(
        [
            "Great - from now on you can call me Nurse Joy.",
            "",
            "_You can change this later by typing in *9* from the main *MENU.*_",
        ]
    )

    assert len(rapidpro_mock.tstate.requests) == 2
    request = rapidpro_mock.tstate.requests[0]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {
            "last_onboarding_time": "2022-06-19T17:30:00",
            "onboarding_reminder_type": "5 min",
        },
    }


@pytest.mark.asyncio
@mock.patch("yal.onboarding.get_current_datetime")
async def test_state_persona_name_skip(
    get_current_datetime, tester: AppTester, rapidpro_mock
):
    get_current_datetime.return_value = datetime(2022, 6, 19, 17, 30)
    tester.setup_state("state_persona_name")

    await tester.user_input("skip")

    tester.assert_state("state_age")
    tester.assert_num_messages(1)

    assert len(rapidpro_mock.tstate.requests) == 2
    request = rapidpro_mock.tstate.requests[0]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {
            "last_onboarding_time": "2022-06-19T17:30:00",
            "onboarding_reminder_type": "5 min",
        },
    }


@pytest.mark.asyncio
@mock.patch("yal.onboarding.get_current_datetime")
async def test_state_persona_emoji(
    get_current_datetime, tester: AppTester, rapidpro_mock
):
    get_current_datetime.return_value = datetime(2022, 6, 19, 17, 30)
    tester.setup_state("state_persona_emoji")

    await tester.user_input("😉")

    tester.assert_state("state_age")
    tester.assert_num_messages(1)

    tester.assert_metadata("persona_emoji", "😉")

    assert len(rapidpro_mock.tstate.requests) == 2
    request = rapidpro_mock.tstate.requests[0]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {
            "last_onboarding_time": "2022-06-19T17:30:00",
            "onboarding_reminder_type": "5 min",
        },
    }


@pytest.mark.asyncio
@mock.patch("yal.onboarding.get_current_datetime")
async def test_state_persona_emoji_skip(
    get_current_datetime, tester: AppTester, rapidpro_mock
):
    get_current_datetime.return_value = datetime(2022, 6, 19, 17, 30)
    tester.setup_state("state_persona_emoji")

    await tester.user_input("skip")

    tester.assert_state("state_dob_full")
    tester.assert_num_messages(1)

    assert "persona_emoji" not in tester.user.metadata

    assert len(rapidpro_mock.tstate.requests) == 2
    request = rapidpro_mock.tstate.requests[0]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {
            "last_onboarding_time": "2022-06-19T17:30:00",
            "onboarding_reminder_type": "5 min",
        },
    }


@pytest.mark.asyncio
@mock.patch("yal.onboarding.get_current_datetime")
async def test_state_age(get_current_datetime, tester: AppTester, rapidpro_mock):
    get_current_datetime.return_value = datetime(2022, 6, 19, 17, 30)
    tester.setup_state("state_age")

    await tester.user_input("22")

    tester.assert_state("state_relationship_status")
    tester.assert_num_messages(1)

    tester.assert_answer("state_age", "22")

    assert len(rapidpro_mock.tstate.requests) == 2
    request = rapidpro_mock.tstate.requests[0]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {
            "last_onboarding_time": "2022-06-19T17:30:00",
            "onboarding_reminder_type": "5 min",
        },
    }


@pytest.mark.asyncio
@mock.patch("yal.onboarding.get_current_datetime")
async def test_state_relationship_status_valid(
    get_current_datetime, tester: AppTester, rapidpro_mock
):
    get_current_datetime.return_value = datetime(2022, 6, 19, 17, 30)
    tester.setup_state("state_relationship_status")

    await tester.user_input("2")

    tester.assert_state("state_province")
    tester.assert_num_messages(1)

    tester.assert_answer("state_relationship_status", "complicated")

    assert len(rapidpro_mock.tstate.requests) == 2
    request = rapidpro_mock.tstate.requests[0]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {
            "last_onboarding_time": "2022-06-19T17:30:00",
            "onboarding_reminder_type": "5 min",
        },
    }


@pytest.mark.asyncio
@mock.patch("yal.onboarding.get_current_datetime")
async def test_state_full_address_invalid(
    get_current_datetime, tester: AppTester, rapidpro_mock
):
    get_current_datetime.return_value = datetime(2022, 6, 19, 17, 30)
    tester.setup_answer("age", "22")
    tester.setup_state("state_full_address")

    await tester.user_input("2 test street \n test suburb")

    tester.assert_state("state_suburb")

    assert len(rapidpro_mock.tstate.requests) == 2
    request = rapidpro_mock.tstate.requests[0]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {
            "last_onboarding_time": "2022-06-19T17:30:00",
            "onboarding_reminder_type": "5 min",
        },
    }


@pytest.mark.asyncio
@mock.patch("yal.onboarding.get_current_datetime")
async def test_state_full_address_valid(
    get_current_datetime, tester: AppTester, rapidpro_mock
):
    get_current_datetime.return_value = datetime(2022, 6, 19, 17, 30)
    tester.setup_answer("age", "22")
    tester.setup_state("state_full_address")

    await tester.user_input("2\ntest street\n test suburb")

    tester.assert_state("state_gender")

    assert len(rapidpro_mock.tstate.requests) == 2
    request = rapidpro_mock.tstate.requests[0]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {
            "last_onboarding_time": "2022-06-19T17:30:00",
            "onboarding_reminder_type": "5 min",
        },
    }


@pytest.mark.asyncio
@mock.patch("yal.onboarding.get_current_datetime")
async def test_state_full_address_minor(
    get_current_datetime, tester: AppTester, rapidpro_mock
):
    get_current_datetime.return_value = datetime(2022, 6, 19, 17, 30)
    tester.setup_answer("age", "17")
    tester.setup_state("state_province")

    await tester.user_input("2")

    tester.assert_state("state_gender")

    assert len(rapidpro_mock.tstate.requests) == 3
    request = rapidpro_mock.tstate.requests[0]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {
            "last_onboarding_time": "2022-06-19T17:30:00",
            "onboarding_reminder_type": "5 min",
        },
    }


@pytest.mark.asyncio
@mock.patch("yal.onboarding.get_current_datetime")
async def test_state_full_address_skip(
    get_current_datetime, tester: AppTester, rapidpro_mock
):
    get_current_datetime.return_value = datetime(2022, 6, 19, 17, 30)
    tester.setup_answer("age", "22")
    tester.setup_state("state_full_address")

    await tester.user_input("SKIP")

    tester.assert_state("state_gender")


@pytest.mark.asyncio
@mock.patch("yal.onboarding.get_current_datetime")
async def test_state_suburb_skip(
    get_current_datetime, tester: AppTester, rapidpro_mock
):
    get_current_datetime.return_value = datetime(2022, 6, 19, 17, 30)
    tester.setup_state("state_suburb")

    await tester.user_input("SKIP")

    tester.assert_state("state_gender")


@pytest.mark.asyncio
@mock.patch("yal.onboarding.get_current_datetime")
async def test_state_street_name_skip(
    get_current_datetime, tester: AppTester, rapidpro_mock
):
    get_current_datetime.return_value = datetime(2022, 6, 19, 17, 30)
    tester.setup_state("state_street_name")
    tester.setup_answer("state_suburb", "test suburb")

    await tester.user_input("SKIP")

    tester.assert_state("state_gender")


@pytest.mark.asyncio
@mock.patch("yal.onboarding.get_current_datetime")
async def test_state_number_name_skip(
    get_current_datetime, tester: AppTester, rapidpro_mock
):
    get_current_datetime.return_value = datetime(2022, 6, 19, 17, 30)
    tester.setup_state("state_street_number")
    tester.setup_answer("state_street_name", "test street name")

    await tester.user_input("SKIP")

    tester.assert_state("state_gender")


@pytest.mark.asyncio
@mock.patch("yal.onboarding.get_current_datetime")
async def test_state_gender(get_current_datetime, tester: AppTester, rapidpro_mock):
    get_current_datetime.return_value = datetime(2022, 6, 19, 17, 30)
    tester.setup_state("state_gender")

    await tester.user_input(session=Message.SESSION_EVENT.NEW)

    tester.assert_message(
        "\n".join(
            [
                "*ABOUT YOU*",
                "🌈 How you identify",
                "-----",
                "",
                "*You're almost done!*🙌🏾",
                "",
                "✅ Age",
                "✅ Relationship Status",
                "✅ Location",
                "◻️ Gender",
                "-----",
                "",
                "*What's your gender?*",
                "",
                "Please select the option you think best describes you:",
                "",
                "*1* - Girl/Woman",
                "*2* - Boy/Man",
                "*3* - Non-binary",
                "*4* - Something else",
                "*5* - Skip",
            ]
        )
    )

    assert len(rapidpro_mock.tstate.requests) == 1
    request = rapidpro_mock.tstate.requests[0]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {
            "last_onboarding_time": "2022-06-19T17:30:00",
            "onboarding_reminder_type": "5 min",
        },
    }


@pytest.mark.asyncio
@mock.patch("yal.onboarding.get_current_datetime")
async def test_state_gender_valid(
    get_current_datetime, tester: AppTester, rapidpro_mock
):
    get_current_datetime.return_value = datetime(2022, 6, 19, 17, 30)
    tester.setup_state("state_gender")

    await tester.user_input("2")

    tester.assert_state("state_onboarding_complete")
    tester.assert_num_messages(1)

    tester.assert_answer("state_gender", "boy_man")

    assert len(rapidpro_mock.tstate.requests) == 2
    request = rapidpro_mock.tstate.requests[0]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {
            "last_onboarding_time": "2022-06-19T17:30:00",
            "onboarding_reminder_type": "5 min",
        },
    }


@pytest.mark.asyncio
async def test_submit_onboarding(tester: AppTester, rapidpro_mock):
    tester.setup_state("state_gender")

    tester.setup_answer("state_age", "22")
    tester.setup_answer("state_relationship_status", "yes")
    tester.setup_answer("state_gender", "other")
    tester.setup_answer("state_province", "FS")
    tester.setup_answer("state_suburb", "SomeSuburb")
    tester.setup_answer("state_street_name", "Good street")
    tester.setup_answer("state_street_number", "12")
    tester.setup_answer("state_persona_name", "Nurse Joy")
    tester.setup_answer("state_persona_emoji", "⛑️")

    await tester.user_input("4")

    tester.assert_state("state_onboarding_complete")
    tester.assert_num_messages(1)

    assert len(rapidpro_mock.tstate.requests) == 2
    request = rapidpro_mock.tstate.requests[1]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {
            "age": "22",
            "opted_out": "FALSE",
            "onboarding_completed": "True",
            "relationship_status": "yes",
            "gender": "other",
            "province": "FS",
            "suburb": "SomeSuburb",
            "street_name": "Good street",
            "street_number": "12",
            "onboarding_reminder_sent": "",
            "onboarding_reminder_type": "",
            "persona_name": "Nurse Joy",
            "persona_emoji": "⛑️",
        },
    }

    tester.assert_metadata("province", "FS")
    tester.assert_metadata("suburb", "SomeSuburb")
    tester.assert_metadata("street_name", "Good street")
    tester.assert_metadata("street_number", "12")


@pytest.mark.asyncio
async def test_onboarding_reminder_yes_response(tester: AppTester, rapidpro_mock):
    tester.setup_state("state_handle_onboarding_reminder_response")
    await tester.user_input("Continue")

    tester.assert_state("state_persona_name")
    tester.assert_num_messages(1)
    assert len(rapidpro_mock.tstate.requests) == 3
    request = rapidpro_mock.tstate.requests[1]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {
            "onboarding_reminder_sent": "",
        },
    }


@pytest.mark.asyncio
async def test_onboarding_reminder_no_thanks_response(tester: AppTester, rapidpro_mock):
    tester.setup_state("state_handle_onboarding_reminder_response")
    await tester.user_input(session=Message.SESSION_EVENT.NEW, content="Not Interested")

    tester.assert_state("state_stop_onboarding_reminders")


@pytest.mark.asyncio
async def test_onboarding_reminder_no_thanks_response_actioned(
    tester: AppTester, rapidpro_mock
):
    tester.setup_state("state_stop_onboarding_reminders")
    await tester.user_input(session=Message.SESSION_EVENT.NEW, content="Not Interested")

    tester.assert_num_messages(1)

    assert len(rapidpro_mock.tstate.requests) == 2
    request = rapidpro_mock.tstate.requests[1]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {"onboarding_reminder_sent": "", "onboarding_reminder_type": ""},
    }


@pytest.mark.asyncio
async def test_onboarding_reminder_later_response(tester: AppTester, rapidpro_mock):
    tester.setup_state("state_handle_onboarding_reminder_response")
    await tester.user_input(
        session=Message.SESSION_EVENT.NEW, content="remind me later"
    )

    tester.assert_state("state_reschedule_onboarding_reminders")


@pytest.mark.asyncio
@mock.patch("yal.onboarding.get_current_datetime")
async def test_onboarding_reminder_later_response_actioned(
    get_current_datetime, tester: AppTester, rapidpro_mock
):
    get_current_datetime.return_value = datetime(2022, 6, 19, 17, 30)
    tester.setup_state("state_reschedule_onboarding_reminders")
    await tester.user_input(
        session=Message.SESSION_EVENT.NEW, content="remind me later"
    )

    tester.assert_num_messages(1)

    assert len(rapidpro_mock.tstate.requests) == 2
    request = rapidpro_mock.tstate.requests[1]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {
            "onboarding_reminder_sent": "",
            "onboarding_reminder_type": "2 hrs",
            "last_onboarding_time": "2022-06-19T17:30:00",
        },
    }
