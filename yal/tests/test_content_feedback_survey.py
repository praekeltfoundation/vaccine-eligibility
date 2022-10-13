import pytest
from sanic import Sanic, response

from vaccine.models import Message
from vaccine.testing import AppTester, MockServer, TState, run_sanic
from yal import config
from yal.content_feedback_survey import ContentFeedbackSurveyApplication
from yal.utils import BACK_TO_MAIN, GET_HELP


@pytest.fixture
async def rapidpro_mock():
    app = Sanic("mock_rapidpro")
    tstate = TState()

    @app.route("/api/v2/contacts.json", methods=["POST"])
    def update_contact(request):
        tstate.requests.append(request)
        return response.json({}, status=200)

    async with run_sanic(app) as server:
        url = config.RAPIDPRO_URL
        config.RAPIDPRO_URL = f"http://{server.host}:{server.port}"
        server.tstate = tstate
        yield server
        config.RAPIDPRO_URL = url


@pytest.fixture
def tester():
    return AppTester(ContentFeedbackSurveyApplication)


@pytest.mark.asyncio
async def test_start(tester: AppTester, rapidpro_mock: MockServer):
    await tester.user_input("yes", session=Message.SESSION_EVENT.NEW)
    tester.assert_state("state_positive_feedback")
    tester.assert_message(
        "\n".join(
            [
                "*That's great - I'm so happy I could help.* 😊",
                "",
                "If there is anything or any info that you think needs to be changed "
                "or added, please let me know.",
                "",
                "Reply:",
                "1. No changes",
                "2. Yes, I have a change!",
                "",
                "--",
                BACK_TO_MAIN,
                GET_HELP,
            ]
        )
    )

    assert rapidpro_mock.tstate
    [update_contact] = rapidpro_mock.tstate.requests
    assert update_contact.json["fields"] == {"feedback_survey_sent": ""}
