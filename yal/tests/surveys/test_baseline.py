import pytest
from sanic import Sanic, response

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
async def test_state_baseline_end_invalid_input(tester: AppTester):

    tester.setup_state("state_baseline_end")

    await tester.user_input("invalid")

    tester.assert_state("state_baseline_end")

    [message] = tester.application.messages
    assert (
        message.content in get_generic_errors()
    ), f"Message content not in provided list, it is {message.content}"


@pytest.mark.asyncio
async def test_state_halfway_message(tester: AppTester):

    tester.setup_state("state_baseline_halfway_msg")

    await tester.user_input("OK Let's do it")

    # tester.assert_state("state_baseline_halfway_msg")
    [message] = tester.application.messages
    # print(message.content)
    # tester.assert_message(
    #    "*How good a job do you feel you are doing in taking care of your health?*"
    # )
