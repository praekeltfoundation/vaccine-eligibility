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
            "onboarding_reminder_sent": "True" if "27820001002" in urn else "False",
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
            "_You can change this later from the main *MENU.*_",
        ]
    )

    assert len(rapidpro_mock.tstate.requests) == 3
    request = rapidpro_mock.tstate.requests[1]
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

    assert len(rapidpro_mock.tstate.requests) == 3
    request = rapidpro_mock.tstate.requests[1]
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

    assert len(rapidpro_mock.tstate.requests) == 3
    request = rapidpro_mock.tstate.requests[1]
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

    tester.assert_state("state_age")
    tester.assert_num_messages(1)

    assert "persona_emoji" not in tester.user.metadata

    assert len(rapidpro_mock.tstate.requests) == 3
    request = rapidpro_mock.tstate.requests[1]
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

    tester.assert_state("state_gender")
    tester.assert_num_messages(1)

    tester.assert_answer("state_age", "22")

    assert len(rapidpro_mock.tstate.requests) == 3
    request = rapidpro_mock.tstate.requests[1]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {
            "last_onboarding_time": "2022-06-19T17:30:00",
            "onboarding_reminder_type": "5 min",
        },
    }


@pytest.mark.asyncio
@mock.patch("yal.onboarding.get_current_datetime")
async def test_state_age_skip(get_current_datetime, tester: AppTester, rapidpro_mock):
    get_current_datetime.return_value = datetime(2022, 6, 19, 17, 30)
    tester.setup_state("state_age")

    await tester.user_input("Skip")

    tester.assert_state("state_gender")
    tester.assert_num_messages(1)

    tester.assert_answer("state_age", "Skip")

    assert len(rapidpro_mock.tstate.requests) == 3
    request = rapidpro_mock.tstate.requests[1]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {
            "last_onboarding_time": "2022-06-19T17:30:00",
            "onboarding_reminder_type": "5 min",
        },
    }


@pytest.mark.asyncio
@mock.patch("yal.onboarding.get_current_datetime")
async def test_state_gender(get_current_datetime, tester: AppTester, rapidpro_mock):
    get_current_datetime.return_value = datetime(2022, 6, 19, 17, 30)
    tester.setup_state("state_gender")

    await tester.user_input(session=Message.SESSION_EVENT.NEW)

    tester.assert_message(
        "\n".join(
            [
                "ABOUT YOU / 🌈 *Your identity*",
                "-----",
                "",
                "*What's your gender?*",
                "",
                "_Tap the button and select the option you think best fits._",
            ]
        )
    )

    assert len(rapidpro_mock.tstate.requests) == 2
    request = rapidpro_mock.tstate.requests[1]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {
            "last_onboarding_time": "2022-06-19T17:30:00",
            "onboarding_reminder_type": "5 min",
        },
    }


@pytest.mark.asyncio
@mock.patch("yal.askaquestion.config")
@mock.patch("yal.onboarding.get_current_datetime")
async def test_state_gender_from_list(
    get_current_datetime, mock_config, tester: AppTester, rapidpro_mock
):
    mock_config.AAQ_URL = "http://aaq-test.com"
    get_current_datetime.return_value = datetime(2022, 6, 19, 17, 30)
    tester.setup_state("state_gender")

    await tester.user_input("2")

    tester.assert_state("state_rel_status")
    tester.assert_num_messages(1)

    tester.assert_answer("state_gender", "male")

    assert len(rapidpro_mock.tstate.requests) == 3
    request = rapidpro_mock.tstate.requests[1]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {
            "last_onboarding_time": "2022-06-19T17:30:00",
            "onboarding_reminder_type": "5 min",
        },
    }


@pytest.mark.asyncio
async def test_submit_onboarding(tester: AppTester, rapidpro_mock):
    tester.setup_state("state_start_survey")
    tester.setup_answer("state_age", "22")
    tester.setup_answer("state_gender", "other")
    tester.setup_answer("state_persona_name", "Nurse Joy")
    tester.setup_answer("state_persona_emoji", "⛑️")
    tester.setup_answer("state_rel_status", "single")

    await tester.user_input("OK, let's start!")
    await tester.user_input("1")
    await tester.user_input("2")
    await tester.user_input("Strongly agree")
    await tester.user_input("Strongly agree")
    await tester.user_input("3")
    await tester.user_input("Not at all true")
    await tester.user_input("Not at all true")
    await tester.user_input("Yes")
    await tester.user_input("4")
    tester.assert_num_messages(1)
    tester.assert_message(
        "\n".join(
            [
                "🙏🏾 Lekker! Your profile is all set up!",
                "",
                "Let's get you started!",
            ]
        ),
        buttons=["Main menu"],
    )

    assert len(rapidpro_mock.tstate.requests) == 3
    request = rapidpro_mock.tstate.requests[2]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {
            "age": "22",
            "opted_out": "FALSE",
            "onboarding_completed": "True",
            "gender": "other",
            "relationship_status": "single",
            "onboarding_reminder_sent": "",
            "onboarding_reminder_type": "",
            "persona_name": "Nurse Joy",
            "persona_emoji": "⛑️",
        },
    }

    # Ensure that the main menu button works
    await tester.user_input("Main menu")
    tester.assert_state("state_welcome")


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


@pytest.mark.asyncio
async def test_onboarding_set_first_time_menu(
    tester: AppTester,
    rapidpro_mock,
):
    tester.setup_state("state_submit_terms_and_conditions")
    await tester.user_input(session=Message.SESSION_EVENT.NEW)
    assert len(rapidpro_mock.tstate.requests) == 3
    tester.assert_state("state_persona_name")
    request = rapidpro_mock.tstate.requests[1]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {
            "terms_accepted": "True",
        },
    }
