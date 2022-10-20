from datetime import datetime
from unittest import mock

import pytest
from sanic import Sanic, response

from vaccine.models import Message
from vaccine.testing import AppTester, TState, run_sanic
from yal import config
from yal.askaquestion import Application as AaqApplication
from yal.change_preferences import Application as ChangePreferencesApplication
from yal.content_feedback_survey import ContentFeedbackSurveyApplication
from yal.main import Application
from yal.mainmenu import Application as MainMenuApplication
from yal.onboarding import Application as OnboardingApplication
from yal.optout import Application as OptoutApplication
from yal.pleasecallme import Application as PleaseCallMeApplication
from yal.quiz import Application as QuizApplication
from yal.servicefinder import Application as ServiceFinderApplication
from yal.terms_and_conditions import Application as TermsApplication
from yal.usertest_feedback import Application as FeedbackApplication


def test_no_state_name_clashes():
    m_states = set(s for s in dir(Application) if s.startswith("state_"))
    mm_states = set(s for s in dir(MainMenuApplication) if s.startswith("state_"))
    on_states = set(s for s in dir(OnboardingApplication) if s.startswith("state_"))
    oo_states = set(s for s in dir(OptoutApplication) if s.startswith("state_"))
    te_states = set(s for s in dir(TermsApplication) if s.startswith("state_"))
    cp_states = set(
        s for s in dir(ChangePreferencesApplication) if s.startswith("state_")
    )
    q_states = set(s for s in dir(QuizApplication) if s.startswith("state_"))
    pc_states = set(s for s in dir(PleaseCallMeApplication) if s.startswith("state_"))
    sf_states = set(s for s in dir(ServiceFinderApplication) if s.startswith("state_"))
    aaq_states = set(s for s in dir(AaqApplication) if s.startswith("state_"))
    fb_states = set(s for s in dir(FeedbackApplication) if s.startswith("state_"))
    c_fb_states = set(
        s for s in dir(ContentFeedbackSurveyApplication) if s.startswith("state_")
    )
    intersection = (
        m_states
        & mm_states
        & on_states
        & oo_states
        & te_states
        & cp_states
        & q_states
        & pc_states
        & sf_states
        & aaq_states
        & fb_states
        & c_fb_states
    ) - {
        "state_name",
        "state_error",
    }

    assert len(intersection) == 0, f"Common states to both apps: {intersection}"


@pytest.fixture
def tester():
    return AppTester(Application)


def get_rapidpro_contact(urn):
    return {
        "uuid": "b733e997-b0b4-4d4d-a3ad-0546e1644aa9",
        "name": "",
        "language": "eng",
        "groups": [],
        "fields": {
            "onboarding_completed": "27820001001" in urn,
            "onboarding_reminder_sent": "27820001001" in urn,
            "aaq_timeout_sent": "27820001001" in urn,
            "aaq_timeout_type": "2" if "27820001001" in urn else "",
            "terms_accepted": "27820001001" in urn,
            "province": "FS",
            "suburb": "cape town",
            "street_name": "high level",
            "street_number": "99",
            "feedback_survey_sent": "true",
            "feedback_type": "content",
            "latitude": -26.2031026,
            "longitude": 28.0251783,
            "location_description": "99 high level, cape town, FS",
        },
        "blocked": False,
        "stopped": False,
        "created_on": "2015-11-11T08:30:24.922024+00:00",
        "modified_on": "2015-11-11T08:30:25.525936+00:00",
        "urns": [urn],
    }


@pytest.fixture
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


@pytest.fixture
async def contentrepo_api_mock():
    Sanic.test_mode = True
    app = Sanic("contentrepo_api_mock")
    tstate = TState()

    @app.route("/api/v2/pages", methods=["GET"])
    def get_main_menu(request):
        tstate.requests.append(request)
        tag = request.args.get("tag")
        if tag == "mainmenu":
            return response.json(
                {
                    "count": 1,
                    "results": [{"id": 111, "title": "Main Menu 1 💊"}],
                }
            )
        return response.json({"count": 0, "results": []})

    @app.route("/suggestedcontent", methods=["GET"])
    def get_suggested_content(request):
        tstate.requests.append(request)
        return response.json(
            {
                "count": 1,
                "results": [{"id": 311, "title": "Suggested Content 1"}],
            }
        )

    async with run_sanic(app) as server:
        url = config.CONTENTREPO_API_URL
        config.CONTENTREPO_API_URL = f"http://{server.host}:{server.port}"
        server.tstate = tstate
        yield server
        config.CONTENTREPO_API_URL = url


@pytest.mark.asyncio
async def test_reset_keyword(tester: AppTester, rapidpro_mock, contentrepo_api_mock):
    tester.setup_state("state_catch_all")
    await tester.user_input("hi")
    tester.assert_state("state_mainmenu")
    tester.assert_num_messages(1)

    assert len(rapidpro_mock.tstate.requests) == 2
    assert len(contentrepo_api_mock.tstate.requests) == 4


@pytest.mark.asyncio
@mock.patch("yal.pleasecallme.get_current_datetime")
async def test_help_keyword(get_current_datetime, tester: AppTester):
    get_current_datetime.return_value = datetime(2022, 6, 21, 13, 30)

    tester.setup_state("state_catch_all")
    await tester.user_input("help")
    tester.assert_state("state_in_hours")
    tester.assert_num_messages(1)


@pytest.mark.asyncio
async def test_stop_keyword(tester: AppTester):
    tester.setup_state("state_catch_all")
    await tester.user_input("stop")
    tester.assert_state("state_optout")
    tester.assert_num_messages(1)


@pytest.mark.asyncio
async def test_state_start_to_catch_all(tester: AppTester, rapidpro_mock):
    await tester.user_input("AAA")
    tester.assert_state("state_start")
    tester.assert_num_messages(1)
    tester.assert_message(
        "\n".join(
            [
                "🤖 *Hey there — Welcome to B-Wise!*",
                "",
                "If you're looking for answers to questions about bodies, sex, "
                "relationships and health, please reply with the word *HI*.",
            ]
        )
    )

    assert len(rapidpro_mock.tstate.requests) == 1


@pytest.mark.asyncio
async def test_state_start_to_mainmenu(
    tester: AppTester, rapidpro_mock, contentrepo_api_mock
):
    await tester.user_input("hi")
    tester.assert_state("state_mainmenu")
    tester.assert_num_messages(1)

    assert len(rapidpro_mock.tstate.requests) == 2
    assert len(contentrepo_api_mock.tstate.requests) == 4

    tester.assert_metadata("longitude", 28.0251783)
    tester.assert_metadata("latitude", -26.2031026)
    tester.assert_metadata("location_description", "99 high level, cape town, FS")


@pytest.mark.asyncio
async def test_onboarding_reminder_response_to_reminder_handler(
    tester: AppTester, rapidpro_mock
):
    await tester.user_input(session=Message.SESSION_EVENT.NEW, content="not interested")
    tester.assert_state("state_stop_onboarding_reminders")
    tester.assert_num_messages(1)

    assert len(rapidpro_mock.tstate.requests) == 2


@pytest.mark.asyncio
async def test_callback_check_response_to_handler(tester: AppTester):
    await tester.user_input(session=Message.SESSION_EVENT.NEW, content="callback")
    tester.assert_state("state_handle_callback_check_response")
    tester.assert_num_messages(1)


@pytest.mark.asyncio
async def test_aaq_timeout_response_to_handler(tester: AppTester, rapidpro_mock):
    await tester.user_input(session=Message.SESSION_EVENT.NEW, content="no")
    tester.assert_num_messages(1)
    tester.assert_message("TODO: Handle question not answered")

    assert len(rapidpro_mock.tstate.requests) == 3


@pytest.mark.asyncio
async def test_content_feedback_response(tester: AppTester, rapidpro_mock):
    """
    If this is in response to a content feedback push message, then it should be handled
    by the content feedback state
    """
    await tester.user_input("1")
    tester.assert_state("state_positive_feedback")
    tester.assert_num_messages(1)

    assert len(rapidpro_mock.tstate.requests) == 2
