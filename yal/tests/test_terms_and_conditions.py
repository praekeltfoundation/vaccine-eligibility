import json

import pytest
from sanic import Sanic, response

from vaccine.testing import AppTester
from yal import config
from yal.main import Application


@pytest.fixture
def tester():
    return AppTester(Application)


@pytest.fixture
async def rapidpro_mock(sanic_client):
    Sanic.test_mode = True
    app = Sanic("mock_rapidpro")
    app.requests = []

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
    await tester.user_input("OK")

    tester.assert_state("state_terms")
    tester.assert_num_messages(1)


@pytest.mark.asyncio
async def test_state_terms_valid(tester: AppTester):
    tester.setup_state("state_terms")
    await tester.user_input("1")

    tester.assert_state("state_terms")
    tester.assert_num_messages(1)


@pytest.mark.asyncio
async def test_submit_terms_and_conditions(tester: AppTester, rapidpro_mock):
    tester.setup_state("state_terms")
    await tester.user_input("2")

    tester.assert_state("state_dob_full")
    tester.assert_num_messages(1)

    assert len(rapidpro_mock.app.requests) == 1
    request = rapidpro_mock.app.requests[0]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {"terms_accepted": "True"},
    }
