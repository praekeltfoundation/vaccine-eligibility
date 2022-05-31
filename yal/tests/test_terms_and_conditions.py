import json

import pytest
from sanic import Sanic, response

from vaccine.testing import AppTester
from yal import turn
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
    get_profile_url = turn.get_profile_url

    host = f"http://{client.host}:{client.port}"
    turn.get_profile_url = (
        lambda whatsapp_id: f"{host}/v1/contacts/{whatsapp_id}/profile"
    )

    yield client
    turn.get_profile_url = get_profile_url


@pytest.mark.asyncio
async def test_state_welcome_valid(tester: AppTester):
    tester.setup_state("state_welcome")
    await tester.user_input("2")

    tester.assert_state("state_get_to_know")
    tester.assert_num_messages(1)


@pytest.mark.asyncio
async def test_state_get_to_know_valid(tester: AppTester):
    tester.setup_state("state_get_to_know")
    await tester.user_input("2")

    tester.assert_state("state_get_to_know_why")
    tester.assert_num_messages(1)


@pytest.mark.asyncio
async def test_state_get_to_know_why_valid(tester: AppTester):
    tester.setup_state("state_get_to_know_why")
    await tester.user_input("OK 👍")

    tester.assert_state("state_terms")
    tester.assert_num_messages(1)


@pytest.mark.asyncio
async def test_state_terms_valid(tester: AppTester):
    tester.setup_state("state_terms")
    await tester.user_input("1")

    tester.assert_state("state_start")
    tester.assert_num_messages(1)


@pytest.mark.asyncio
async def test_submit_terms_and_conditions(tester: AppTester, turn_api_mock):
    tester.setup_state("state_terms")
    await tester.user_input("2")

    tester.assert_state("state_dob_year")
    tester.assert_num_messages(1)

    assert len(turn_api_mock.app.requests) == 1
    request = turn_api_mock.app.requests[0]
    assert json.loads(request.body.decode("utf-8")) == {"terms_accepted": True}
