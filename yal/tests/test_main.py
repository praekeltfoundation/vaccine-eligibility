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
from yal.servicefinder_feedback_survey import ServiceFinderFeedbackSurveyApplication
from yal.terms_and_conditions import Application as TermsApplication
from yal.usertest_feedback import Application as FeedbackApplication
from yal.utils import BACK_TO_MAIN, GET_HELP, get_current_datetime
from yal.wa_fb_crossover_feedback import Application as WaFbCrossoverFeedbackApplication


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
    sf_s_states = set(
        s for s in dir(ServiceFinderFeedbackSurveyApplication) if s.startswith("state_")
    )
    wa_fb_states = set(
        s for s in dir(WaFbCrossoverFeedbackApplication) if s.startswith("state_")
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
        & sf_s_states
        & wa_fb_states
    ) - {
        "state_name",
        "state_error",
    }

    assert len(intersection) == 0, f"Common states to both apps: {intersection}"


@pytest.fixture
def tester():
    return AppTester(Application)


def get_rapidpro_contact(urn):
    feedback_type = ""
    feedback_timestamp = None
    if "27820001002" in urn:
        feedback_type = "content"
    if "27820001003" in urn:
        feedback_type = "facebook_banner"
    if "27820001004" in urn:
        feedback_type = "servicefinder"
        feedback_timestamp = get_current_datetime().isoformat()
    feedback_type_2 = ""
    feedback_timestamp_2 = None
    feedback_survey_sent_2 = ""
    if "27820001005" in urn:
        feedback_type_2 = "servicefinder"
        feedback_timestamp_2 = "2022-03-04T05:06:07"
        feedback_survey_sent_2 = "true"
    if "27820001006" in urn:
        feedback_type = "ask_a_question"
    if "27820001007" in urn:
        feedback_type = "ask_a_question_2"
    return {
        "uuid": "b733e997-b0b4-4d4d-a3ad-0546e1644aa9",
        "name": "",
        "language": "eng",
        "groups": [],
        "fields": {
            "onboarding_completed": "27820001001" in urn,
            "onboarding_reminder_sent": "27820001001" in urn,
            "terms_accepted": "27820001001" in urn,
            "province": "FS",
            "suburb": "cape town",
            "street_name": "high level",
            "street_number": "99",
            "feedback_survey_sent": "true",
            "feedback_type": feedback_type,
            "feedback_timestamp": feedback_timestamp,
            "feedback_type_2": feedback_type_2,
            "feedback_timestamp_2": feedback_timestamp_2,
            "feedback_survey_sent_2": feedback_survey_sent_2,
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


MODEL_ANSWERS_PAGE_1 = {
    "FAQ #1 Title": {"id": "1", "body": "This is FAQ #1's content."},
    "FAQ #2 Title that is very long": {"id": "2", "body": "This is FAQ #2's content."},
    "FAQ #3 Title": {"id": "3", "body": "This is FAQ #3's content."},
    "FAQ #4 Title": {"id": "4", "body": "This is FAQ #4's content."},
    "FAQ #5 Title": {"id": "5", "body": "This is FAQ #5's content."},
}


MODEL_ANSWERS_PAGE_2 = {
    "FAQ #6 Title": {"id": "6", "body": "This is FAQ #6's content."},
    "FAQ #7 Title": {"id": "7", "body": "This is FAQ #7's content."},
    "FAQ #8 Title": {"id": "8", "body": "This is FAQ #8's content."},
}


def get_aaq_response(answers, next=None, prev=None):
    top_responses = [[v["id"], k, v["body"]] for k, v in answers.items()]
    response = {
        "top_responses": top_responses,
        "feedback_secret_key": "abcde12345",
        "inbound_secret_key": "secret_123",
        "inbound_id": 28,
    }
    if next:
        response["next_page_url"] = f"{next}?inbound_secret_key=secret_123"
    if prev:
        response["prev_page_url"] = f"{prev}?inbound_secret_key=secret_123"
    return response


@pytest.fixture
async def aaq_mock():
    Sanic.test_mode = True
    app = Sanic("mock_aaq")
    tstate = TState()

    @app.route("/inbound/check", methods=["POST"])
    def inbound_check(request):
        tstate.requests.append(request)
        body = get_aaq_response(MODEL_ANSWERS_PAGE_1, next="/inbound/92567/1")
        return response.json(body, status=200)

    @app.route("/inbound/92567/1", methods=["GET"])
    def inbound_check_page_2(request):
        tstate.requests.append(request)
        body = get_aaq_response(MODEL_ANSWERS_PAGE_2, prev="/inbound/92567/0")
        return response.json(body, status=200)

    @app.route("/inbound/feedback", methods=["PUT"])
    def add_feedback(request):
        tstate.requests.append(request)
        return response.json({}, status=200)

    async with run_sanic(app) as server:
        url = config.AAQ_URL
        config.AAQ_URL = f"http://{server.host}:{server.port}"
        config.AAQ_TOKEN = "testtoken"
        server.tstate = tstate
        yield server
        config.AAQ_URL = url


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
    assert len(contentrepo_api_mock.tstate.requests) == 5


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
    assert len(contentrepo_api_mock.tstate.requests) == 5

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
async def test_aaq_timeout_response_to_handler(
    tester: AppTester, rapidpro_mock, aaq_mock
):
    tester.setup_user_address("27820001007")
    tester.user.metadata["inbound_id"] = "inbound-id"
    tester.user.metadata["feedback_secret_key"] = "feedback-secret-key"
    tester.user.metadata["faq_id"] = "1"
    tester.user.metadata["model_answers"] = MODEL_ANSWERS_PAGE_1
    tester.user.metadata["aaq_page"] = 0
    tester.user.metadata["feedback_timestamp"] = get_current_datetime().isoformat()
    await tester.user_input("Nope...")
    tester.assert_state("state_no_question_not_answered")
    tester.assert_num_messages(1)
    message = "\n".join(
        [
            "*I'm sorry I couldn't find what you were looking for this time.* ",
            "",
            "Please tell me what you're looking for again. "
            "I'll try make sure I have the right information "
            "for you next time.",
            "",
            "_Just type and send your question again, now._" "",
            "-----",
            "*Or reply:*",
            BACK_TO_MAIN,
            GET_HELP,
        ]
    )
    tester.assert_message(message)

    assert len(rapidpro_mock.tstate.requests) == 4


@pytest.mark.asyncio
async def test_content_feedback_response(tester: AppTester, rapidpro_mock):
    """
    If this is in response to a content feedback push message, then it should be handled
    by the content feedback state
    """
    tester.user.metadata["feedback_timestamp"] = get_current_datetime().isoformat()
    tester.setup_user_address("27820001002")
    await tester.user_input("1")
    tester.assert_state("state_positive_feedback")
    tester.assert_num_messages(1)

    assert len(rapidpro_mock.tstate.requests) == 2


@pytest.mark.asyncio
async def test_facebook_crossover_feedback_response(tester: AppTester, rapidpro_mock):
    """
    If this is in response to a fb feedback push message, then it should be handled
    by the fb feedback state
    """
    # Test session resume
    tester.user.metadata["feedback_timestamp"] = get_current_datetime().isoformat()
    tester.setup_user_address("27820001003")
    await tester.user_input("yes, I did")
    tester.assert_state("state_saw_recent_facebook")
    tester.assert_num_messages(1)

    assert len(rapidpro_mock.tstate.requests) == 3


@pytest.mark.asyncio
async def test_servicefinder_feedback_response(tester: AppTester, rapidpro_mock):
    """
    If this is in response to a servicefinder feedback push message, then it should be
    handled by the servicefinder feedback application
    """
    tester.setup_user_address("27820001004")
    # test new session
    await tester.user_input("yes, thanks", session=Message.SESSION_EVENT.NEW)
    tester.assert_state("state_servicefinder_positive_feedback")
    tester.assert_num_messages(1)

    assert len(rapidpro_mock.tstate.requests) == 3


@pytest.mark.asyncio
async def test_servicefinder_feedback_2_response(tester: AppTester, rapidpro_mock):
    """
    If this is in response to the second servicefinder feedback push message, then it
    should be handled by the servicefinder feedback application
    """
    tester.user.metadata["feedback_timestamp_2"] = get_current_datetime().isoformat()
    tester.setup_user_address("27820001005")
    await tester.user_input("yes, i went")
    tester.assert_state("state_went_to_service")
    tester.assert_num_messages(1)

    assert len(rapidpro_mock.tstate.requests) == 3


@pytest.mark.asyncio
async def test_state_qa_reset_feedback_timestamp_keywords(
    tester: AppTester, rapidpro_mock
):
    old_timestamp = get_current_datetime().isoformat()
    tester.user.metadata["feedback_timestamp"] = old_timestamp
    await tester.user_input("resetfeedbacktimestampobzvmp")
    tester.assert_state(None)
    tester.assert_message(
        "QA: Success! You can now modify the timestamp in RapidPro to trigger "
        "the message early"
    )
    assert tester.user.metadata["feedback_timestamp"] != old_timestamp
