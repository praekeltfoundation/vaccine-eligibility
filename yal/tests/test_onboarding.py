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
async def test_state_persona_emoji_invalid(
    get_current_datetime, tester: AppTester, rapidpro_mock
):
    get_current_datetime.return_value = datetime(2022, 6, 19, 17, 30)
    tester.setup_state("state_persona_emoji")

    await tester.user_input("😎\n👔\n👞👞")

    tester.assert_state("state_age")
    tester.assert_num_messages(1)

    tester.assert_metadata("persona_emoji", "😎")

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
                "*Which gender do you most identify with?*",
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
    tester.setup_state("state_rel_status")
    tester.setup_answer("state_age", "22")
    tester.setup_answer("state_gender", "other")
    tester.setup_answer("state_persona_name", "Nurse Joy")
    tester.setup_answer("state_persona_emoji", "⛑️")

    await tester.user_input("No, I'm single")

    tester.assert_num_messages(1)
    tester.assert_message(
        "\n".join(
            [
                "*Can I start by asking how much you agree or disagree with some "
                "statements about you, your life, and your health?*",
            ]
        ),
        buttons=["OK, let's start!", "I can't right now"],
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


@pytest.mark.asyncio
async def test_assessment_start(tester: AppTester, rapidpro_mock):
    tester.setup_state("state_locus_of_control_assessment_start")
    await tester.user_input("OK, let's start!")
    tester.assert_state("state_survey_question")
    tester.assert_metadata(
        "assessment_end_state", "state_locus_of_control_assessment_end"
    )


@pytest.mark.asyncio
async def test_assessment_complete(tester: AppTester, rapidpro_mock):
    """
    Start pushmessage optin flow after assessment
    """
    tester.user.metadata[
        "assessment_end_state"
    ] = "state_locus_of_control_assessment_end"
    tester.user.metadata["assessment_section"] = 2
    tester.setup_state("state_survey_question")
    await tester.user_input(session=Message.SESSION_EVENT.NEW)
    tester.assert_message(
        "\n".join(
            [
                "If you'd like, I can also send you notifications once a day with "
                "relevant info that I've put together just for you.",
                "",
                "*Would you like to get notifications?*",
                "",
                "1. Yes, please!",
                "2. No thanks",
                "",
                "_💡You can turn the notifications off at any time, just reply "
                '"STOP" or go to your profile._',
            ]
        )
    )


@pytest.mark.asyncio
@mock.patch("yal.assessments.get_current_datetime")
async def test_assessment_skip(get_current_datetime, tester: AppTester, rapidpro_mock):
    get_current_datetime.return_value = datetime(2022, 6, 19, 17, 30)

    tester.user.metadata["persona_emoji"] = "🪱"
    tester.setup_state("state_locus_of_control_assessment_start")

    await tester.user_input(content="I can't right now")
    tester.assert_message(
        "\n".join(
            [
                "🪱 No worries, we get it!",
                "",
                "I'll send you a reminder message tomorrow, so you can come back "
                "and continue with these questions, then.",
                "",
                "Check you later 🤙🏾",
            ]
        )
    )
    assert len(rapidpro_mock.tstate.requests) == 2
    request = rapidpro_mock.tstate.requests[1]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {
            "assessment_reminder": "2022-06-20T16:30:00",
            "assessment_reminder_name": "locus_of_control",
        },
    }


@pytest.mark.asyncio
async def test_phase2_profile_update_to_submit_when_gender_set(
    tester: AppTester, rapidpro_mock
):
    tester.user.metadata["age"] = "22"
    tester.user.metadata["gender"] = "male"
    tester.user.metadata["relationship_status"] = "single"
    tester.user.metadata["persona_emoji"] = "🪱"

    await tester.user_input(
        "test",
        transport_metadata={
            "message": {
                "button": {"payload": "state_phase2_update_exising_user_profile"}
            }
        },
    )

    tester.assert_state("state_rel_status")
    await tester.user_input(content="It's complicated")

    tester.assert_state("state_locus_of_control_assessment_few_qs")

    assert len(rapidpro_mock.tstate.requests) == 5
    request = rapidpro_mock.tstate.requests[4]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {
            "age": "22",
            "opted_out": "FALSE",
            "onboarding_completed": "True",
            "gender": "male",
            "relationship_status": "complicated",
            "onboarding_reminder_sent": "",
            "onboarding_reminder_type": "",
            "persona_emoji": "🪱",
        },
    }


@pytest.mark.asyncio
async def test_phase2_profile_update_to_submit_when_no_gender(
    tester: AppTester, rapidpro_mock
):
    tester.user.metadata["age"] = "22"
    tester.user.metadata["relationship_status"] = "single"
    tester.user.metadata["persona_name"] = "Nurse Joy"

    await tester.user_input(
        "test",
        transport_metadata={
            "message": {
                "button": {"payload": "state_phase2_update_exising_user_profile"}
            }
        },
    )

    tester.assert_state("state_gender")
    await tester.user_input(content="Female")

    tester.assert_state("state_rel_status")
    await tester.user_input(content="It's complicated")

    tester.assert_state("state_locus_of_control_assessment_few_qs")

    assert len(rapidpro_mock.tstate.requests) == 8
    request = rapidpro_mock.tstate.requests[7]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {
            "age": "22",
            "opted_out": "FALSE",
            "onboarding_completed": "True",
            "gender": "female",
            "relationship_status": "complicated",
            "onboarding_reminder_sent": "",
            "onboarding_reminder_type": "",
            "persona_name": "Nurse Joy",
        },
    }
