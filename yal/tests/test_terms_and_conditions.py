import json

import pytest
from sanic import Sanic, response

from vaccine.testing import AppTester, TState, run_sanic
from yal import config
from yal.main import Application


@pytest.fixture
def tester():
    return AppTester(Application)


@pytest.fixture
async def rapidpro_mock():
    Sanic.test_mode = True
    app = Sanic("mock_rapidpro")
    tstate = TState()

    @app.route("/api/v2/contacts.json", methods=["GET"])
    def get_contact(request):
        return response.json({"results": []})

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
async def test_state_welcome_valid(tester: AppTester):
    tester.setup_state("state_welcome")
    await tester.user_input("Create a profile")

    tester.assert_state("state_terms")
    tester.assert_num_messages(1)


@pytest.mark.asyncio
async def test_state_terms_read(tester: AppTester, rapidpro_mock):
    tester.setup_state("state_terms")
    await tester.user_input("3")

    tester.assert_state("state_terms")
    tester.assert_num_messages(1)


@pytest.mark.asyncio
async def test_submit_terms_and_conditions(tester: AppTester, rapidpro_mock):
    tester.setup_state("state_terms")
    await tester.user_input("1")

    tester.assert_state("state_persona_name")
    tester.assert_num_messages(1)

    [msg] = tester.fake_worker.outbound_messages
    assert msg.content == ("Excellent - now we can get you set up.")

    assert len(rapidpro_mock.tstate.requests) == 2
    request = rapidpro_mock.tstate.requests[0]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {"terms_accepted": "True"},
    }


@pytest.mark.asyncio
async def test_state_terms_decline(tester: AppTester, rapidpro_mock):
    tester.setup_state("state_terms")
    await tester.user_input("2")

    tester.assert_state("state_decline_confirm")
    tester.assert_num_messages(1)


@pytest.mark.asyncio
async def test_state_decline_confirm_valid(tester: AppTester, rapidpro_mock):
    tester.setup_state("state_decline_confirm")
    await tester.user_input("2")

    tester.assert_state("state_decline_2")

    [msg] = tester.fake_worker.outbound_messages
    assert msg.content == (
        "*No stress—I get it.* 😌\n"
        "\n"
        "It's wise to think these things over. Your online safety is "
        "important to us too.\n"
        "\n"
        "If you change your mind though, we'll be here! Just send me a "
        "*HI* whenever you're ready to chat again. In the meantime, be "
        "wise and look after yourself 😉👋🏾"
    )


@pytest.mark.asyncio
async def test_state_decline_confirm_accept(tester: AppTester, rapidpro_mock):
    tester.setup_state("state_decline_confirm")
    await tester.user_input("1")

    tester.assert_state("state_persona_name")
    tester.assert_num_messages(1)

    assert len(rapidpro_mock.tstate.requests) == 2
    request = rapidpro_mock.tstate.requests[0]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {"terms_accepted": "True"},
    }
