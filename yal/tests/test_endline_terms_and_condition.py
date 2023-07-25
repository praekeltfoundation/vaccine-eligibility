import json

import pytest
from sanic import Sanic, response

from vaccine.testing import AppTester, TState, run_sanic
from yal import config
from yal.main import Application


@pytest.fixture
def tester():
    return AppTester(Application)


@pytest.fixture(autouse=True)
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
async def test_state_start_terms_accept(tester: AppTester, rapidpro_mock):
    tester.setup_state("state_start_terms")
    await tester.user_input("Yes, I agree")
    tester.assert_state("state_accept_consent")

    message = "\n".join(
        [
            "*Amazing Thank you!*",
            "Okay, first I've got a few questions to help me figure out how "
            "you're doing at taking care of your love and health needs.",
            "",
            "I'm going to ask a few questions about you and how much you "
            "agree or disagree with some statements about you, your life, "
            "and your health?",
        ]
    )
    tester.assert_message(message)


@pytest.mark.asyncio
async def test_state_terms_decline(tester: AppTester, rapidpro_mock):
    tester.setup_state("state_start_terms")
    await tester.user_input("No, I don't agree")

    tester.assert_state("state_no_consent")
    message = "\n".join(
        [
            "That's completely okay, there are no consequences to not taking ,"
            "part in this study. Please enjoy the BWise tool and stay safe. "
            "If you change your mind, please send *Answer* to this number",
        ]
    )
    tester.assert_message(message)


@pytest.mark.asyncio
async def test_state_monthly_household_income_endline(tester: AppTester, rapidpro_mock):
    tester.setup_state("state_monthly_household_income_endline")
    await tester.user_input("1")

    tester.assert_state("state_survey_question")

    message = "\n".join(["◼️◽️◽️◽️", "-----", "", "*I'm my own boss.* 😎"])
    tester.assert_message(message)


@pytest.mark.asyncio
async def test_state_accept_consent_reminder(tester: AppTester, rapidpro_mock):

    tester.setup_state("state_accept_consent")
    await tester.user_input("I can't right now")

    tester.assert_state("state_set_reminder_timer")
    tester.assert_metadata("assessment_reminder_name", "locus_of_control_endline")
    tester.assert_metadata("assessment_reminder_type", "endline reengagement 30min")

    message = "\n".join(
        [
            "🤖 No worries, we get it!",
            "",
            "I'll send you a reminder message in 30 mins, so you can come back"
            " and answer these questions.",
            "",
            "Check you later 🤙🏾",
        ]
    )
    tester.assert_message(message)


@pytest.mark.asyncio
async def test_state_submit_terms_and_conditions_accept(
    tester: AppTester, rapidpro_mock
):
    tester.setup_state("state_monthly_household_income_endline")
    await tester.user_input("1")

    assert len(rapidpro_mock.tstate.requests) == 3
    request = rapidpro_mock.tstate.requests[0]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {"endline_terms_accepted": "True"},
    }
