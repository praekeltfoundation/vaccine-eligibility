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
async def test_positive_feedback(tester: AppTester, rapidpro_mock: MockServer):
    """If the user responds positively to the push message, ask for any feedback"""
    await tester.user_input("yes", session=Message.SESSION_EVENT.NEW)
    tester.assert_state("state_positive_feedback")
    tester.assert_message(
        "\n".join(
            [
                "*That's great - I'm so happy I could help.* 😊",
                "",
                "If there is anything that you think needs to be changed or added in "
                "the info I gave you? Please let me know!",
                "",
                "Reply:",
                "1. No changes",
                "2. Yes, I have a change",
                "",
                "--",
                "",
                BACK_TO_MAIN,
                GET_HELP,
            ]
        )
    )

    assert rapidpro_mock.tstate
    [update_contact] = rapidpro_mock.tstate.requests
    assert update_contact.json["fields"] == {"feedback_survey_sent": ""}


@pytest.mark.asyncio
async def test_no_feedback(tester: AppTester):
    """If the user doesn't have any feedback, end"""
    tester.setup_state("state_positive_feedback")
    await tester.user_input("No changes")

    tester.assert_message(
        "\n".join(
            [
                "Thanks for letting us know!",
                "",
                "Check you later 👋🏾",
                "",
                "-----",
                "*Or reply:*",
                BACK_TO_MAIN,
                GET_HELP,
            ]
        ),
        session=Message.SESSION_EVENT.CLOSE,
    )


@pytest.mark.asyncio
async def test_get_feedback(tester: AppTester):
    """If the user has feedback, ask them for it"""
    tester.setup_state("state_positive_feedback")
    await tester.user_input("Yes, I have a change")

    tester.assert_message(
        "\n".join(
            [
                "Please tell me what was missing or what you'd like to change.",
                "",
                "_Just type and send your feedback now._",
                "",
                "-----",
                "*Or reply:*",
                BACK_TO_MAIN,
                GET_HELP,
            ]
        )
    )
    tester.assert_state("state_get_feedback")


@pytest.mark.asyncio
async def test_confirm_feedback(tester: AppTester):
    """After the user has given their feedback, confirm"""
    tester.setup_state("state_get_feedback")
    await tester.user_input("test feedback")

    tester.assert_message(
        "\n".join(
            [
                "Ok got it 👍🏾",
                "",
                "Thank you for the feedback - I'm working on it already.",
                "",
                "Chat again soon 👋🏾",
                "",
                "-----",
                "*Or reply:*",
                BACK_TO_MAIN,
                GET_HELP,
            ]
        ),
        session=Message.SESSION_EVENT.CLOSE,
    )


@pytest.mark.asyncio
async def test_negative_feedback(tester: AppTester, rapidpro_mock: MockServer):
    """If the user responds negative to the push message, ask if they want AAQ"""
    await tester.user_input("no", session=Message.SESSION_EVENT.NEW)
    tester.assert_state("state_negative_feedback")
    tester.assert_message(
        "\n".join(
            [
                "I'm sorry I couldn't find what you were looking for this time... "
                "maybe I can help you find it if you *ask me a question?*",
                "",
                "*Would you like to ask me a question now?*",
                "",
                "*1*. Yes, please",
                "*2*. Maybe later",
                "",
                "-----",
                "*Or reply:*",
                BACK_TO_MAIN,
                GET_HELP,
            ]
        )
    )


@pytest.mark.asyncio
async def test_no_negative_feedback(tester: AppTester, rapidpro_mock: MockServer):
    """If the user doesn't want to AAQ, confirm"""
    tester.setup_state("state_negative_feedback")
    await tester.user_input("Maybe later")
    tester.assert_message(
        "\n".join(
            [
                "Cool. 👍🏾",
                "",
                'If you change your mind, just go back to "ask a question" on the '
                "main menu.",
                "",
                "-----",
                "*Reply:*",
                BACK_TO_MAIN,
                GET_HELP,
            ]
        )
    )
