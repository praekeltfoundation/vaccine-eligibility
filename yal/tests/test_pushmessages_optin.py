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
        if tstate.errormax:
            if tstate.errors < tstate.errormax:
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

    async with run_sanic(app) as server:
        url = config.RAPIDPRO_URL
        config.RAPIDPRO_URL = f"http://{server.host}:{server.port}"
        config.RAPIDPRO_TOKEN = "testtoken"
        server.tstate = tstate
        yield server
        config.RAPIDPRO_URL = url


@pytest.mark.asyncio
async def test_state_pushmessages_optin(tester: AppTester, rapidpro_mock):
    tester.setup_state("state_start_pushmessage_optin")
    await tester.user_input("Yes, please!")
    tester.assert_state("state_pushmessage_optin_final")

    assert len(rapidpro_mock.tstate.requests) == 2
    request = rapidpro_mock.tstate.requests[1]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {"push_message_opt_in": "True"},
    }


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
