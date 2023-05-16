import json
from datetime import datetime
from unittest import mock

import pytest
from sanic import Sanic, response

from vaccine.models import Message
from vaccine.testing import AppTester, TState, run_sanic
from yal import config
from yal.main import Application
from yal.utils import GENERIC_ERRORS, replace_persona_fields


@pytest.fixture
def tester():
    return AppTester(Application)


def get_generic_errors():
    errors = []
    for error in GENERIC_ERRORS:
        errors.append(replace_persona_fields(error))
    return errors


def get_rapidpro_contact(urn):
    return {
        "fields": {
            "emergency_contact": "" if ("27820001001" in urn) else "+27831231234",
        },
    }


@pytest.fixture(autouse=True)
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


@pytest.mark.asyncio
@mock.patch("yal.surveys.baseline.get_current_datetime")
async def test_state_submit_baseline_completed(
    get_current_datetime, tester: AppTester, rapidpro_mock
):
    get_current_datetime.return_value = datetime(2022, 6, 19, 17, 30)
    tester.setup_state("state_alcohol_assessment_v2_end")
    await tester.user_input(session=Message.SESSION_EVENT.NEW)

    tester.assert_state("state_baseline_end")

    assert len(rapidpro_mock.tstate.requests) == 3
    request = rapidpro_mock.tstate.requests[2]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {
            "baseline_survey_completed": "True",
            "ejaf_airtime_incentive_sent": "False",
            "ejaf_baseline_completed_on": "2022-06-19T17:30:00",
        },
    }
    tester.assert_metadata("baseline_survey_completed", "True")
    tester.assert_metadata("ejaf_airtime_incentive_sent", "False")
    tester.assert_metadata("ejaf_baseline_completed_on", "2022-06-19T17:30:00")

    tester.assert_answer("baseline_survey_completed", "True")


@pytest.mark.asyncio
async def test_state_baseline_end_invalid_input(tester: AppTester):

    tester.setup_state("state_baseline_end")

    await tester.user_input("invalid")

    tester.assert_state("state_baseline_end")

    [message] = tester.application.messages
    assert (
        message.content in get_generic_errors()
    ), f"Message content not in provided list, it is {message.content}"


# @pytest.mark.asyncio
# async def test_state_halfway_message(tester: AppTester):

# tester.setup_state("state_baseline_halfway_msg")

# await tester.user_input("OK Let's do it")

# tester.assert_state("state_baseline_halfway_msg")
# [message] = tester.application.messages
# print(message.content)
# tester.assert_message(
#    "*How good a job do you feel you are doing in taking care of your health?*"
# )

@pytest.mark.asyncio
async def test_state_self_esteem_assessment_v2_end(tester: AppTester):

    await tester.user_input(
        "test",
        transport_metadata={
            "message": {"button": {"payload": "state_self_esteem_assessment_v2_end"}}
        },
    )
    tester.assert_state("state_survey_question")
    tester.assert_metadata("assessment_name", "connectedness_v2")
    tester.assert_metadata("assessment_end_state", "state_connectedness_assessment_v2_end")


@pytest.mark.asyncio
async def test_state_connectedness_assessment_v2_end(tester: AppTester):

    await tester.user_input(
        "test",
        transport_metadata={
            "message": {"button": {"payload": "state_connectedness_assessment_v2_end"}}
        },
    )
    tester.assert_state("state_survey_question")
    tester.assert_metadata("assessment_name", "body_image_v2")
    tester.assert_metadata("assessment_end_state", "state_body_image_assessment_v2_end")


@pytest.mark.asyncio
async def test_state_body_image_assessment_v2_end(tester: AppTester):

    await tester.user_input(
        "test",
        transport_metadata={
            "message": {"button": {"payload": "state_body_image_assessment_v2_end"}}
        },
    )
    tester.assert_state("state_survey_question")
    tester.assert_metadata("assessment_name", "depression_v2")
    tester.assert_metadata("assessment_end_state", "state_depression_assessment_v2_end")


@pytest.mark.asyncio
async def test_depression_assessment_v2_end(tester: AppTester):

    await tester.user_input(
        "test",
        transport_metadata={
            "message": {"button": {"payload": "state_depression_assessment_v2_end"}}
        },
    )
    tester.assert_state("state_survey_question")
    tester.assert_metadata("assessment_name", "anxiety_v2")
    tester.assert_metadata("assessment_end_state", "state_anxiety_assessment_v2_end")


@pytest.mark.asyncio
async def test_state_anxiety_assessment_v2_end(tester: AppTester):

    await tester.user_input(
        "test",
        transport_metadata={
            "message": {"button": {"payload": "state_anxiety_assessment_v2_end"}}
        },
    )
    tester.assert_state("state_baseline_halfway_msg")


# @pytest.mark.asyncio
# async def test_state_baseline_halfway_msg(tester: AppTester):
#     tester.setup_state("state_baseline_halfway_msg")
#     await tester.user_input("OK Let's do it")
#     tester.assert_state("state_self_perceived_healthcare_assessment_v2")


@pytest.mark.asyncio
async def test_state_self_perceived_healthcare_assessment_v2_end(tester: AppTester):

    await tester.user_input(
        "test",
        transport_metadata={
            "message": {"button": {"payload": "state_self_perceived_healthcare_assessment_v2_end"}}
        },
    )

    tester.assert_state("state_survey_question")
    tester.assert_metadata("assessment_name", "sexual_health_literacy_v2")
    tester.assert_metadata("assessment_end_state", "state_sexual_health_lit_assessment_v2_end")


@pytest.mark.asyncio
async def test_state_sexual_health_lit_assessment_v2_end(tester: AppTester):

    await tester.user_input(
        "test",
        transport_metadata={
            "message": {"button": {"payload": "state_sexual_health_lit_assessment_v2_end"}}
        },
    )

    tester.assert_state("state_survey_question")
    tester.assert_metadata("assessment_name", "gender_attitude_v2")
    tester.assert_metadata("assessment_end_state", "state_gender_attitude_assessment_v2_end")


@pytest.mark.asyncio
async def test_state_gender_attitude_assessment_v2_end(tester: AppTester):

    await tester.user_input(
        "test",
        transport_metadata={
            "message": {"button": {"payload": "state_gender_attitude_assessment_v2_end"}}
        },
    )

    tester.assert_state("state_survey_question")
    tester.assert_metadata("assessment_name", "sexual_consent_v2")
    tester.assert_metadata("assessment_end_state", "state_sexual_consent_assessment_v2_end")


@pytest.mark.asyncio
async def test_state_sexual_consent_assessment_v2_end(tester: AppTester):

    await tester.user_input(
        "test",
        transport_metadata={
            "message": {"button": {"payload": "state_sexual_consent_assessment_v2_end"}}
        },
    )

    tester.assert_state("state_survey_question")
    tester.assert_metadata("assessment_name", "alcohol_v2")
    tester.assert_metadata("assessment_end_state", "state_alcohol_assessment_v2_end")


@pytest.mark.asyncio
async def test_state_alcohol_assessment_v2_end(tester: AppTester):

    await tester.user_input(
        "test",
        transport_metadata={
            "message": {"button": {"payload": "state_alcohol_assessment_v2_end"}}
        },
    )

    tester.assert_state("state_baseline_end")

