import json

import pytest
from sanic import Sanic, response

# from vaccine.models import Message
from vaccine.testing import AppTester, TState, run_sanic
from yal import config
from yal.main import Application

# TODO: add number of messages assertions


@pytest.fixture
def tester():
    return AppTester(Application)


def get_rapidpro_contact(urn):
    contact = {
        "uuid": "b733e997-b0b4-4d4d-a3ad-0546e1644aa9",
        "name": "Test Human",
        "language": "eng",
        "groups": [],
        "fields": {},
        "blocked": False,
        "stopped": False,
        "created_on": "2015-11-11T08:30:24.922024+00:00",
        "modified_on": "2015-11-11T08:30:25.525936+00:00",
        "urns": [urn],
    }
    if urn == "whatsapp:27820001001":
        contact["fields"] = {}
    return contact


@pytest.fixture(autouse=True)
async def rapidpro_mock():
    Sanic.test_mode = True
    app = Sanic("mock_rapidpro")
    tstate = TState()

    @app.route("/api/v2/contacts.json", methods=["GET"])
    def get_contact(request):
        tstate.requests.append(request)
        if tstate.errormax and tstate.errors < tstate.errormax:
            tstate.errors += 1
            return response.json({}, status=500)

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

    @app.route("/api/v2/globals.json", methods=["GET"])
    def check_if_baseline_active(request):
        tstate.requests.append(request)
        assert request.args.get("key") == "baseline_survey_active"
        return response.json(
            {
                "next": None,
                "previous": None,
                "results": [
                    {
                        "key": "baseline_survey_active",
                        "name": "Baseline Survey Active",
                        "value": "True",
                        "modified_on": "2023-04-28T07:34:06.216776Z",
                    }
                ],
            },
            status=200,
        )

    async with run_sanic(app) as server:
        url = config.RAPIDPRO_URL
        config.RAPIDPRO_URL = f"http://{server.host}:{server.port}"
        config.RAPIDPRO_TOKEN = "testtoken"  # noqa: S105 - Fake password/token for test purposes
        server.tstate = tstate
        yield server
        config.RAPIDPRO_URL = url


@pytest.mark.asyncio
async def test_user_too_young_not_offered_study(tester: AppTester, rapidpro_mock):
    tester.user.metadata["age"] = "12"
    tester.user.metadata["country"] = "south africa"
    tester.user.metadata["used_bot_before"] = "no"

    tester.setup_state("state_start_pushmessage_optin")

    await tester.user_input("Yes, please!")
    tester.assert_state("state_pushmessage_optin_final")

    assert len(rapidpro_mock.tstate.requests) == 3
    request = rapidpro_mock.tstate.requests[1]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {"push_message_opt_in": "True"},
    }
    tester.assert_answer("state_is_eligible_for_study", "false")


@pytest.mark.asyncio
async def test_user_too_old_not_offered_study(tester: AppTester, rapidpro_mock):
    tester.user.metadata["age"] = "30"
    tester.user.metadata["country"] = "south africa"
    tester.user.metadata["used_bot_before"] = "no"

    tester.setup_state("state_start_pushmessage_optin")

    await tester.user_input("Yes, please!")
    tester.assert_state("state_pushmessage_optin_final")

    assert len(rapidpro_mock.tstate.requests) == 3
    request = rapidpro_mock.tstate.requests[1]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {"push_message_opt_in": "True"},
    }
    tester.assert_answer("state_is_eligible_for_study", "false")


@pytest.mark.asyncio
async def test_user_not_sa_not_offered_study(tester: AppTester, rapidpro_mock):
    tester.user.metadata["age"] = "20"
    tester.user.metadata["country"] = ""
    tester.user.metadata["used_bot_before"] = "no"

    tester.setup_state("state_start_pushmessage_optin")

    await tester.user_input("Yes, please!")
    tester.assert_state("state_pushmessage_optin_final")

    assert len(rapidpro_mock.tstate.requests) == 3
    request = rapidpro_mock.tstate.requests[1]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {"push_message_opt_in": "True"},
    }
    tester.assert_answer("state_is_eligible_for_study", "false")


@pytest.mark.asyncio
async def test_user_used_bot_before_not_offered_study(tester: AppTester, rapidpro_mock):
    tester.user.metadata["age"] = "20"
    tester.user.metadata["country"] = "south africa"
    tester.user.metadata["used_bot_before"] = "yes"

    tester.setup_state("state_start_pushmessage_optin")

    await tester.user_input("Yes, please!")
    tester.assert_state("state_pushmessage_optin_final")

    assert len(rapidpro_mock.tstate.requests) == 3
    request = rapidpro_mock.tstate.requests[1]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {"push_message_opt_in": "True"},
    }
    tester.assert_answer("state_is_eligible_for_study", "false")


@pytest.mark.asyncio
async def test_state_pushmessages_optin_no(tester: AppTester, rapidpro_mock):
    tester.setup_state("state_start_pushmessage_optin")
    await tester.user_input("No thanks")
    tester.assert_state("state_pushmessage_optin_final")

    assert len(rapidpro_mock.tstate.requests) == 2
    request = rapidpro_mock.tstate.requests[1]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {"push_message_opt_in": "False"},
    }


# TODO: Add a test that checks that the user is not invited when
# the is_baseline_active flag is False


@pytest.mark.asyncio
async def test_eligible_user_is_offered_study(tester: AppTester, rapidpro_mock):
    tester.user.metadata["age"] = "20"
    tester.user.metadata["country"] = "south africa"
    tester.user.metadata["used_bot_before"] = "no"

    tester.setup_state("state_start_pushmessage_optin")

    await tester.user_input("Yes, please!")
    tester.assert_state("state_study_invitation")

    assert len(rapidpro_mock.tstate.requests) == 3
    request = rapidpro_mock.tstate.requests[1]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {"push_message_opt_in": "True"},
    }

    tester.assert_answer("state_is_eligible_for_study", "true")


@pytest.mark.asyncio
async def test_state_study_invitation_declined(tester: AppTester, rapidpro_mock):
    tester.setup_state("state_study_invitation")
    await tester.user_input("I'm not interested")
    tester.assert_state("state_pushmessage_optin_final")

    assert len(rapidpro_mock.tstate.requests) == 1


@pytest.mark.asyncio
async def test_state_study_invitation_accepted(tester: AppTester, rapidpro_mock):
    tester.setup_state("state_study_invitation")
    await tester.user_input("Yes I want to answer")
    tester.assert_state("state_study_consent")

    assert len(rapidpro_mock.tstate.requests) == 1


@pytest.mark.asyncio
async def test_state_study_consent_rejected(tester: AppTester, rapidpro_mock):
    tester.setup_state("state_study_consent")
    await tester.user_input("No, I don't agree")
    tester.assert_state("state_pushmessage_optin_final")

    assert len(rapidpro_mock.tstate.requests) == 1


@pytest.mark.asyncio
async def test_state_study_consent_accepted(tester: AppTester, rapidpro_mock):
    tester.setup_state("state_study_consent")
    await tester.user_input("Yes, I agree")
    tester.assert_state("state_survey_question")

    assert len(rapidpro_mock.tstate.requests) == 4
    request = rapidpro_mock.tstate.requests[1]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {"ejaf_study_optin": "True"},
    }


@pytest.mark.asyncio
async def test_user_with_no_age_not_offered_study(tester: AppTester, rapidpro_mock):
    tester.user.metadata["age"] = None
    tester.user.metadata["country"] = "south africa"
    tester.user.metadata["used_bot_before"] = "no"

    tester.setup_state("state_start_pushmessage_optin")

    await tester.user_input("Yes, please!")
    tester.assert_state("state_pushmessage_optin_final")

    assert len(rapidpro_mock.tstate.requests) == 3
    request = rapidpro_mock.tstate.requests[1]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {"push_message_opt_in": "True"},
    }
    tester.assert_answer("state_is_eligible_for_study", "false")
