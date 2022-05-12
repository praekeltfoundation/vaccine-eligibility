import json

import pytest
from sanic import Sanic, response

from vaccine.models import Message, StateData, User
from vaccine.testing import AppTester
from yal import config
from yal.main import Application


@pytest.fixture
def tester():
    return AppTester(Application)


@pytest.fixture
async def turn_api_mock(sanic_client):
    Sanic.test_mode = True
    app = Sanic("mock_turn_api")
    app.requests = []
    app.errors = 0
    app.errormax = 0

    @app.route("/v1/contacts/<msisdn:int>/profile", methods=["GET"])
    def callback(request, msisdn):
        app.requests.append(request)
        if app.errormax:
            if app.errors < app.errormax:
                app.errors += 1
                return response.json({}, status=500)
        return response.json({"fields": {"prototype_user": msisdn == 27820001001}})

    client = await sanic_client(app)
    url = config.TURN_URL
    config.TURN_URL = f"http://{client.host}:{client.port}"
    yield client
    config.TURN_URL = url


@pytest.mark.asyncio
async def test_state_start_to_catch_all(tester: AppTester, turn_api_mock):
    await tester.user_input("AAA")
    tester.assert_state("state_start")
    tester.assert_num_messages(1)
    tester.assert_message("TODO: Catch all temp flow")

    assert len(turn_api_mock.app.requests) == 1


@pytest.mark.asyncio
async def test_state_start_to_welcome(tester: AppTester, turn_api_mock):
    await tester.user_input("hi")
    tester.assert_state("state_start")
    tester.assert_num_messages(1)
    tester.assert_message("TODO: welcome")

    assert len(turn_api_mock.app.requests) == 1


@pytest.mark.asyncio
async def test_state_start_to_coming_soon(tester: AppTester, turn_api_mock):
    tester.setup_user_address("27820001002")
    await tester.user_input("hi")
    tester.assert_state("state_start")
    tester.assert_num_messages(1)
    tester.assert_message("TODO: coming soon")

    assert len(turn_api_mock.app.requests) == 1
