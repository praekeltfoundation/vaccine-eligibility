import json

import pytest
from sanic import Sanic, response

from vaccine.testing import AppTester
from yal.main import Application


@pytest.fixture
def tester():
    return AppTester(Application)


@pytest.fixture
async def turn_api_mock(sanic_client, tester):
    Sanic.test_mode = True
    app = Sanic("mock_turn_api")
    app.requests = []
    app.errors = 0
    app.errormax = 0

    @app.route("/v1/contacts/<msisdn:int>/profile", methods=["PATCH"])
    def callback(request, msisdn):
        app.requests.append(request)
        if app.errormax:
            if app.errors < app.errormax:
                app.errors += 1
                return response.json({}, status=500)
        return response.json({})

    client = await sanic_client(app)
    turn_profile_url = tester.application.turn_profile_url

    host = f"http://{client.host}:{client.port}"
    tester.application.turn_profile_url = (
        lambda whatsapp_id: f"{host}/v1/contacts/{whatsapp_id}/profile"
    )

    yield client
    tester.application.turn_profile_url = turn_profile_url


@pytest.mark.asyncio
async def test_state_dob_month_valid(tester: AppTester):
    tester.setup_state("state_dob_month")
    await tester.user_input("2")

    tester.assert_state("state_dob_day")
    tester.assert_num_messages(1)

    tester.assert_answer("state_dob_month", "2")


@pytest.mark.asyncio
async def test_state_dob_month_invalid(tester: AppTester):
    tester.setup_state("state_dob_month")
    await tester.user_input("22")

    tester.assert_state("state_dob_month")
    tester.assert_num_messages(1)

    tester.assert_no_answer("state_dob_month")


@pytest.mark.asyncio
async def test_state_dob_month_skip(tester: AppTester):
    tester.setup_state("state_dob_month")
    await tester.user_input("skip")

    tester.assert_state("state_dob_day")
    tester.assert_num_messages(1)

    tester.assert_answer("state_dob_month", "skip")


@pytest.mark.asyncio
async def test_state_dob_day_valid(tester: AppTester):
    tester.setup_state("state_dob_day")
    await tester.user_input("2")

    tester.assert_state("state_dob_year")
    tester.assert_num_messages(1)

    tester.assert_answer("state_dob_day", "2")


@pytest.mark.asyncio
async def test_state_dob_day_invalid(tester: AppTester):
    tester.setup_state("state_dob_day")
    await tester.user_input("200")

    tester.assert_state("state_dob_day")
    tester.assert_num_messages(1)

    tester.assert_no_answer("state_dob_day")


@pytest.mark.asyncio
async def test_state_dob_day_skip(tester: AppTester):
    tester.setup_state("state_dob_day")
    await tester.user_input("skip")

    tester.assert_state("state_dob_year")
    tester.assert_num_messages(1)

    tester.assert_answer("state_dob_day", "skip")


@pytest.mark.asyncio
async def test_submit_onboarding(tester: AppTester, turn_api_mock):
    tester.setup_state("state_name_gender")

    tester.setup_answer("state_dob_month", "2")
    tester.setup_answer("state_dob_day", "22")
    tester.setup_answer("state_dob_year", "2007")
    tester.setup_answer("state_relationship_status", "yes")
    tester.setup_answer("state_gender", "other")
    tester.setup_answer("state_name_gender", "new gender")

    await tester.user_input("new gender")

    tester.assert_state("state_onboarding_complete")
    tester.assert_num_messages(1)

    assert len(turn_api_mock.app.requests) == 1
    request = turn_api_mock.app.requests[0]
    assert json.loads(request.body.decode("utf-8")) == {
        "onboarding_completed": True,
        "dob_month": "2",
        "dob_day": "22",
        "dob_year": "2007",
        "relationship_status": "yes",
        "gender": "other",
        "gender_other": "new gender",
    }
