from datetime import datetime
from pkgutil import iter_modules
from unittest import mock

import pytablereader as ptr
import pytest
from sanic import Sanic, response

from vaccine.models import Message
from vaccine.testing import AppTester, TState, run_sanic
from yal import config
from yal.askaquestion import Application as AaqApplication
from yal.assessments import Application as SegmentSurveyApplication
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
from yal.tests.test_mainmenu import build_message_detail
from yal.usertest_feedback import Application as FeedbackApplication
from yal.utils import BACK_TO_MAIN, GET_HELP, get_current_datetime
from yal.wa_fb_crossover_feedback import Application as WaFbCrossoverFeedbackApplication


def get_state_sets():
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
    ss_states = set(s for s in dir(SegmentSurveyApplication) if s.startswith("state_"))
    wa_fb_states = set(
        s for s in dir(WaFbCrossoverFeedbackApplication) if s.startswith("state_")
    )

    return [
        m_states,
        mm_states,
        on_states,
        oo_states,
        te_states,
        cp_states,
        q_states,
        pc_states,
        sf_states,
        aaq_states,
        fb_states,
        c_fb_states,
        sf_s_states,
        ss_states,
        wa_fb_states,
    ]


def test_no_state_name_clashes():
    state_sets = get_state_sets()
    intersection = set.intersection(*state_sets) - {
        "state_name",
        "state_error",
    }

    assert len(intersection) == 0, f"Common states to both apps: {intersection}"


def test_all_states_added_to_docs():
    state_sets = get_state_sets()
    existing_states = set.union(*state_sets) - {"state_name"}

    # States from assessments are dynamic
    for assessment in iter_modules(["yal/assessment_data"]):
        module = assessment.module_finder.find_module(assessment.name).load_module()
        for section in module.ASSESSMENT_QUESTIONS.values():
            for name, details in section["questions"].items():
                if details.get("type", "info") != "info":
                    existing_states.add(name)

    loader = ptr.MarkdownTableFileLoader("yal/tests/states_dictionary.md")
    documented_states = set()
    for data in loader.load():
        documented_states = documented_states | set(
            row["state_name"] for row in data.as_dict()[data.table_name]
        )

    difference = existing_states.difference(documented_states)

    assert (
        len(difference) == 0
    ), f"{len(difference)} states are not documented. List: {difference}"


@pytest.fixture
def tester():
    return AppTester(Application)


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

        return response.json(
            {
                "results": [{"fields": tstate.contact_fields}],
                "next": None,
            },
            status=200,
        )

    @app.route("/api/v2/contacts.json", methods=["POST"])
    def update_contact(request):
        tstate.requests.append(request)
        tstate.contact_fields.update(request.json["fields"])
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

    @app.route("/api/v2/pages/444", methods=["GET"])
    def get_page_detail_444(request):
        tstate.requests.append(request)
        return response.json(
            build_message_detail(
                444,
                "Main Menu / Content Page 444",
                "Content for page 444",
            )
        )

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
    rapidpro_mock.tstate.contact_fields["onboarding_completed"] = "TRUE"
    rapidpro_mock.tstate.contact_fields["terms_accepted"] = "TRUE"
    tester.setup_state("state_catch_all")
    await tester.user_input("hi")
    tester.assert_state("state_mainmenu")
    tester.assert_num_messages(2)

    assert len(rapidpro_mock.tstate.requests) == 3
    assert len(contentrepo_api_mock.tstate.requests) == 4


@pytest.mark.asyncio
@mock.patch("yal.pleasecallme.get_current_datetime")
async def test_emergency_keywords_existing_session(
    get_current_datetime, tester: AppTester
):
    get_current_datetime.return_value = datetime(2022, 6, 21, 13, 30)

    tester.setup_state("state_catch_all")
    await tester.user_input(session=Message.SESSION_EVENT.RESUME, content="depressed")
    tester.assert_state("state_in_hours")
    tester.assert_num_messages(1)


@pytest.mark.asyncio
@mock.patch("yal.pleasecallme.get_current_datetime")
async def test_emergency_keywords_new_session(get_current_datetime, tester: AppTester):
    get_current_datetime.return_value = datetime(2022, 6, 21, 13, 30)

    tester.setup_state("state_catch_all")
    await tester.user_input(session=Message.SESSION_EVENT.NEW, content="I want to die")
    tester.assert_state("state_in_hours")
    tester.assert_num_messages(1)


@pytest.mark.asyncio
@mock.patch("yal.pleasecallme.get_current_datetime")
async def test_emergency_keywords_go_back(get_current_datetime, tester: AppTester):
    get_current_datetime.return_value = datetime(2022, 6, 21, 13, 30)

    tester.setup_state("state_catch_all")
    await tester.user_input(content="edpressed")
    tester.assert_state("state_confirm_redirect_please_call_me")
    tester.assert_num_messages(1)
    await tester.user_input("no")
    tester.assert_state("state_start")


@pytest.mark.asyncio
@mock.patch("yal.pleasecallme.get_current_datetime")
async def test_emergency_keywords_need_help(get_current_datetime, tester: AppTester):
    get_current_datetime.return_value = datetime(2022, 6, 21, 13, 30)
    tester.setup_state("state_catch_all")
    await tester.user_input(content="want to die")
    tester.assert_message(
        "\n".join(
            [
                'Hi, would you like to talk to someone about "want to die"?',
                "",
                "----",
                "*Or reply:*",
                BACK_TO_MAIN,
            ]
        )
    )
    tester.assert_state("state_confirm_redirect_please_call_me")
    await tester.user_input("yes")
    tester.assert_state("state_in_hours")


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
    rapidpro_mock.tstate.contact_fields["onboarding_completed"] = "TRUE"
    rapidpro_mock.tstate.contact_fields["terms_accepted"] = "TRUE"
    rapidpro_mock.tstate.contact_fields["latitude"] = "-26.2031026"
    rapidpro_mock.tstate.contact_fields["longitude"] = "28.0251783"
    rapidpro_mock.tstate.contact_fields[
        "location_description"
    ] = "99 high level, cape town, FS"
    await tester.user_input("hi")
    tester.assert_state("state_mainmenu")
    tester.assert_num_messages(2)

    assert len(rapidpro_mock.tstate.requests) == 3
    assert len(contentrepo_api_mock.tstate.requests) == 4

    tester.assert_metadata("longitude", "28.0251783")
    tester.assert_metadata("latitude", "-26.2031026")
    tester.assert_metadata("location_description", "99 high level, cape town, FS")


@pytest.mark.asyncio
async def test_state_start_contact_fields(
    tester: AppTester, rapidpro_mock, contentrepo_api_mock
):
    rapidpro_mock.tstate.contact_fields["onboarding_completed"] = "TRUE"
    rapidpro_mock.tstate.contact_fields["terms_accepted"] = "TRUE"
    rapidpro_mock.tstate.contact_fields["blankfield"] = None
    await tester.user_input("hi")

    tester.assert_metadata("onboarding_completed", "TRUE")
    assert "blankfield" not in tester.user.metadata


@pytest.mark.asyncio
async def test_tracked_keywords_saved(
    tester: AppTester, rapidpro_mock, contentrepo_api_mock
):
    rapidpro_mock.tstate.contact_fields["onboarding_completed"] = "TRUE"
    rapidpro_mock.tstate.contact_fields["terms_accepted"] = "TRUE"
    await tester.user_input("howzit")
    tester.assert_state("state_mainmenu")
    tester.assert_num_messages(2)

    tester.assert_answer("state_source_tracking", "howzit")


@pytest.mark.asyncio
async def test_tracked_keywords_saved_for_new_user(
    tester: AppTester, rapidpro_mock, contentrepo_api_mock
):
    await tester.user_input("heita")
    tester.assert_state("state_welcome")
    tester.assert_num_messages(1)

    tester.assert_answer("state_source_tracking", "heita")


@pytest.mark.asyncio
async def test_tracked_keywords_saved_ads_round_2(
    tester: AppTester, rapidpro_mock, contentrepo_api_mock
):
    rapidpro_mock.tstate.contact_fields["onboarding_completed"] = "True"
    rapidpro_mock.tstate.contact_fields["terms_accepted"] = "True"
    await tester.user_input("join")
    tester.assert_state("state_mainmenu")
    tester.assert_num_messages(2)

    tester.assert_answer("state_source_tracking", "join")


@pytest.mark.asyncio
async def test_tracked_keywords_saved_for_new_user_ads_round_2(
    tester: AppTester, rapidpro_mock, contentrepo_api_mock
):
    rapidpro_mock.tstate.contact_fields["onboarding_completed"] = ""
    rapidpro_mock.tstate.contact_fields["terms_accepted"] = ""
    await tester.user_input("Hi")
    tester.assert_state("state_welcome")
    tester.assert_num_messages(1)

    tester.assert_answer("state_source_tracking", "hi")


@pytest.mark.asyncio
async def test_onboarding_reminder_response_to_reminder_handler(
    tester: AppTester, rapidpro_mock
):
    rapidpro_mock.tstate.contact_fields["onboarding_reminder_sent"] = "TRUE"
    await tester.user_input(session=Message.SESSION_EVENT.NEW, content="not interested")
    tester.assert_state("state_stop_onboarding_reminders")
    tester.assert_num_messages(1)

    assert len(rapidpro_mock.tstate.requests) == 2


@pytest.mark.asyncio
async def test_push_message_buttons_to_display_page(
    tester: AppTester, rapidpro_mock, contentrepo_api_mock
):
    """
    If there's a button payload that indicates the user should be shown a content page
    then we should take them there
    """
    rapidpro_mock.tstate.contact_fields["push_related_page_id"] = "444"
    # Set the current_menu_level to 5 so we can test that it gets reset to 1
    tester.user.metadata["current_menu_level"] = 5
    await tester.user_input(
        "test",
        transport_metadata={
            "message": {"button": {"payload": "state_prep_push_msg_related_page"}}
        },
    )

    tester.assert_state("state_display_page")
    tester.assert_num_messages(1)
    tester.assert_message(
        "\n".join(
            [
                "Main Menu / Content Page 444",
                "-----",
                "",
                "Content for page 444",
                "",
                "-----",
                "*Or reply:*",
                "0. 🏠 Back to Main *MENU*",
                "#. 🆘Get *HELP*",
            ]
        )
    )
    tester.assert_metadata("topics_viewed", ["123"])
    tester.assert_metadata("current_menu_level", 1)
    assert len(rapidpro_mock.tstate.requests) == 4
    assert len(contentrepo_api_mock.tstate.requests) == 2


@pytest.mark.asyncio
async def test_push_message_page_id_buttons_display_page(
    tester: AppTester, rapidpro_mock, contentrepo_api_mock
):
    """
    If there's a button payload that indicates the user should be shown a content page
    then we should take them there
    """
    rapidpro_mock.tstate.contact_fields["push_related_page_id"] = "444"
    # Set the current_menu_level to 5 so we can test that it gets reset to 1
    tester.user.metadata["current_menu_level"] = 5
    await tester.user_input(
        "test",
        transport_metadata={"message": {"button": {"payload": "page_id_444"}}},
    )

    tester.assert_state("state_display_page")
    tester.assert_num_messages(1)
    tester.assert_message(
        "\n".join(
            [
                "Main Menu / Content Page 444",
                "-----",
                "",
                "Content for page 444",
                "",
                "-----",
                "*Or reply:*",
                "0. 🏠 Back to Main *MENU*",
                "#. 🆘Get *HELP*",
            ]
        )
    )
    tester.assert_metadata("topics_viewed", ["123"])
    tester.assert_metadata("current_menu_level", 1)
    assert len(rapidpro_mock.tstate.requests) == 4
    assert len(contentrepo_api_mock.tstate.requests) == 2


@pytest.mark.asyncio
async def test_callback_check_response_to_handler(tester: AppTester):
    await tester.user_input(session=Message.SESSION_EVENT.NEW, content="callback")
    tester.assert_state("state_handle_callback_check_response")
    tester.assert_num_messages(1)


@pytest.mark.asyncio
async def test_aaq_timeout_response_to_handler(
    tester: AppTester, rapidpro_mock, aaq_mock
):
    rapidpro_mock.tstate.contact_fields["feedback_survey_sent"] = "TRUE"
    rapidpro_mock.tstate.contact_fields["feedback_type"] = "ask_a_question_2"
    rapidpro_mock.tstate.contact_fields[
        "feedback_timestamp"
    ] = get_current_datetime().isoformat()
    tester.user.metadata["inbound_id"] = "inbound-id"
    tester.user.metadata["feedback_secret_key"] = "feedback-secret-key"
    tester.user.metadata["faq_id"] = "1"
    tester.user.metadata["model_answers"] = MODEL_ANSWERS_PAGE_1
    tester.user.metadata["aaq_page"] = 0
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

    assert len(rapidpro_mock.tstate.requests) == 3


@pytest.mark.asyncio
async def test_content_feedback_response(tester: AppTester, rapidpro_mock):
    """
    If this is in response to a content feedback push message, then it should be handled
    by the content feedback state
    """
    rapidpro_mock.tstate.contact_fields[
        "feedback_timestamp"
    ] = get_current_datetime().isoformat()
    rapidpro_mock.tstate.contact_fields["feedback_type"] = "content"
    rapidpro_mock.tstate.contact_fields["feedback_survey_sent"] = "TRUE"
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
    rapidpro_mock.tstate.contact_fields[
        "feedback_timestamp"
    ] = get_current_datetime().isoformat()
    rapidpro_mock.tstate.contact_fields["feedback_type"] = "facebook_banner"
    rapidpro_mock.tstate.contact_fields["feedback_survey_sent"] = "TRUE"
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
    rapidpro_mock.tstate.contact_fields["feedback_type"] = "servicefinder"
    rapidpro_mock.tstate.contact_fields[
        "feedback_timestamp"
    ] = get_current_datetime().isoformat()
    rapidpro_mock.tstate.contact_fields["feedback_survey_sent"] = "TRUE"
    # test new session
    await tester.user_input("yes, thanks", session=Message.SESSION_EVENT.NEW)
    tester.assert_state("state_servicefinder_positive_feedback")
    tester.assert_num_messages(1)

    assert len(rapidpro_mock.tstate.requests) == 2


@pytest.mark.asyncio
async def test_servicefinder_feedback_2_response(tester: AppTester, rapidpro_mock):
    """
    If this is in response to the second servicefinder feedback push message, then it
    should be handled by the servicefinder feedback application
    """
    tester.user.metadata["feedback_timestamp_2"] = get_current_datetime().isoformat()
    rapidpro_mock.tstate.contact_fields["feedback_type_2"] = "servicefinder"
    rapidpro_mock.tstate.contact_fields["feedback_timestamp_2"] = "2022-03-04T05:06:07"
    rapidpro_mock.tstate.contact_fields["feedback_survey_sent_2"] = "true"
    await tester.user_input("yes, i went")
    tester.assert_state("state_went_to_service")
    tester.assert_num_messages(1)

    assert len(rapidpro_mock.tstate.requests) == 2


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


@pytest.mark.asyncio
async def test_template_message_button_payload(tester: AppTester):
    """
    If there's a button payload that points to a valid state, then send the user to that
    state.
    """
    await tester.user_input(
        "test",
        transport_metadata={"message": {"button": {"payload": "state_catch_all"}}},
    )
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


@pytest.mark.asyncio
async def test_sexual_health_literacy_assessment(tester: AppTester):
    """
    If there's a button payload that indicates that the sexual health literacy
    assessment should start, then we should start it
    """
    await tester.user_input(
        "test",
        transport_metadata={
            "message": {
                "button": {"payload": "state_sexual_health_literacy_assessment"}
            }
        },
    )
    tester.assert_state("state_survey_question")
    tester.assert_metadata("assessment_name", "sexual_health_literacy")
    tester.assert_metadata(
        "assessment_end_state", "state_sexual_health_literacy_assessment_end"
    )


@pytest.mark.asyncio
async def test_locus_of_control_assessment(tester: AppTester):
    """
    If there's a button payload that indicates that the locus_of_control
    assessment should start, then we should start it
    """
    await tester.user_input(
        "test",
        transport_metadata={
            "message": {"button": {"payload": "state_locus_of_control_assessment"}}
        },
    )
    tester.assert_state("state_survey_question")
    tester.assert_metadata("assessment_name", "locus_of_control")
    tester.assert_metadata(
        "assessment_end_state", "state_locus_of_control_assessment_end"
    )


@pytest.mark.asyncio
async def test_depression_and_anxiety_assessment(tester: AppTester):
    """
    If there's a button payload that indicates that the depression_and_anxiety
    assessment should start, then we should start it
    """
    await tester.user_input(
        "test",
        transport_metadata={
            "message": {
                "button": {"payload": "state_depression_and_anxiety_assessment"}
            }
        },
    )
    tester.assert_state("state_survey_question")
    tester.assert_metadata("assessment_name", "depression_and_anxiety")
    tester.assert_metadata(
        "assessment_end_state", "state_depression_and_anxiety_assessment_end"
    )


@pytest.mark.asyncio
async def test_connectedness_assessment(tester: AppTester):
    """
    If there's a button payload that indicates that the connectedness
    assessment should start, then we should start it
    """
    await tester.user_input(
        "test",
        transport_metadata={
            "message": {"button": {"payload": "state_connectedness_assessment"}}
        },
    )
    tester.assert_state("state_survey_question")
    tester.assert_metadata("assessment_name", "connectedness")
    tester.assert_metadata("assessment_end_state", "state_connectedness_assessment_end")


@pytest.mark.asyncio
async def test_gender_attitude_assessment(tester: AppTester):
    """
    If there's a button payload that indicates that the gender_attitude
    assessment should start, then we should start it
    """
    await tester.user_input(
        "test",
        transport_metadata={
            "message": {"button": {"payload": "state_gender_attitude_assessment"}}
        },
    )
    tester.assert_state("state_survey_question")
    tester.assert_metadata("assessment_name", "gender_attitude")
    tester.assert_metadata(
        "assessment_end_state", "state_gender_attitude_assessment_end"
    )


@pytest.mark.asyncio
async def test_body_image_assessment(tester: AppTester):
    """
    If there's a button payload that indicates that the body_image
    assessment should start, then we should start it
    """
    await tester.user_input(
        "test",
        transport_metadata={
            "message": {"button": {"payload": "state_body_image_assessment"}}
        },
    )
    tester.assert_state("state_survey_question")
    tester.assert_metadata("assessment_name", "body_image")
    tester.assert_metadata("assessment_end_state", "state_body_image_assessment_end")


@pytest.mark.asyncio
async def test_self_perceived_healthcare_assessment(tester: AppTester):
    """
    If there's a button payload that indicates that the self_perceived_healthcare
    assessment should start, then we should start it
    """
    await tester.user_input(
        "test",
        transport_metadata={
            "message": {
                "button": {"payload": "state_self_perceived_healthcare_assessment"}
            }
        },
    )
    tester.assert_state("state_survey_question")
    tester.assert_metadata("assessment_name", "self_perceived_healthcare")
    tester.assert_metadata(
        "assessment_end_state", "state_self_perceived_healthcare_assessment_end"
    )


@pytest.mark.asyncio
async def test_state_generic_what_would_you_like_to_do(tester: AppTester):
    tester.setup_state("state_generic_what_would_you_like_to_do")
    await tester.user_input("Go to the menu")
    tester.assert_state("state_mainmenu")


@pytest.mark.asyncio
async def test_state_self_perceived_healthcare_assessment_go_to_generic(
    tester: AppTester,
):
    tester.setup_state("state_self_perceived_healthcare_assessment_risk_message")
    await tester.user_input(session=Message.session_event.NEW)
    tester.assert_state("state_generic_what_would_you_like_to_do")


@pytest.mark.asyncio
async def test_state_sexual_health_literacy_assessment_go_to_generic(tester: AppTester):
    tester.setup_state("state_sexual_health_literacy_send_risk_message")
    await tester.user_input(session=Message.session_event.NEW)
    tester.assert_state("state_generic_what_would_you_like_to_do")


@pytest.mark.asyncio
async def test_state_depression_and_anxiety_assessment_go_to_generic(tester: AppTester):
    tester.setup_state("state_depression_and_anxiety_assessment_risk_message")
    await tester.user_input(session=Message.session_event.NEW)
    tester.assert_state("state_generic_what_would_you_like_to_do")


@pytest.mark.asyncio
async def test_state_connectedness_assessment_go_to_generic(tester: AppTester):
    tester.setup_state("state_connectedness_assessment_risk_message")
    await tester.user_input(session=Message.session_event.NEW)
    tester.assert_state("state_generic_what_would_you_like_to_do")


@pytest.mark.asyncio
async def test_state_gender_attitude_assessment_go_to_generic(tester: AppTester):
    tester.setup_state("state_gender_attitude_assessment_risk_message")
    await tester.user_input(session=Message.session_event.NEW)
    tester.assert_state("state_generic_what_would_you_like_to_do")


@pytest.mark.asyncio
async def test_state_body_image_assessment_go_to_generic(tester: AppTester):
    tester.setup_state("state_body_image_assessment_risk_message")
    await tester.user_input(session=Message.session_event.NEW)
    tester.assert_state("state_generic_what_would_you_like_to_do")


@pytest.mark.asyncio
async def test_state_generic_what_would_you_like_to_do_aaq(tester: AppTester, aaq_mock):
    tester.setup_state("state_generic_what_would_you_like_to_do")
    await tester.user_input("Ask a question")
    tester.assert_state("state_aaq_start")


@pytest.mark.asyncio
async def test_state_generic_what_would_you_like_to_do_(tester: AppTester):
    tester.setup_state("state_generic_what_would_you_like_to_do")
    await tester.user_input("Update settings")
    tester.assert_state("state_display_preferences")


@pytest.mark.asyncio
async def test_mainmenu_payload(tester: AppTester, rapidpro_mock, contentrepo_api_mock):
    """
    If there's a button payload that indicates that the user should be shown the main
    menu, then we should send them there
    """
    await tester.user_input(
        "test",
        transport_metadata={"message": {"button": {"payload": "state_pre_mainmenu"}}},
    )
    tester.assert_state("state_mainmenu")
    tester.assert_num_messages(2)

    assert len(rapidpro_mock.tstate.requests) == 3
    assert len(contentrepo_api_mock.tstate.requests) == 4


@pytest.mark.asyncio
async def test_phase2_payload_message_directs_to_onboarding_gender(
    tester: AppTester, rapidpro_mock
):
    """
    If there's a button payload that indicates the user is responding to the phase2
    invite, then we should send them to the onboarding state that handles that
    """
    await tester.user_input(
        "test",
        transport_metadata={
            "message": {
                "button": {"payload": "state_phase2_update_exising_user_profile"}
            }
        },
    )
    tester.assert_state("state_gender")

    assert len(rapidpro_mock.tstate.requests) == 2


@pytest.mark.asyncio
async def test_phase2_payload_message_directs_to_onboarding_rel_status(
    tester: AppTester, rapidpro_mock
):
    """
    If there's a button payload that indicates the user is responding to the phase2
    invite, then we should send them to the onboarding state that handles that
    """
    rapidpro_mock.tstate.contact_fields["gender"] = "male"
    await tester.user_input(
        "test",
        transport_metadata={
            "message": {
                "button": {"payload": "state_phase2_update_exising_user_profile"}
            }
        },
    )
    tester.assert_state("state_rel_status")

    assert len(rapidpro_mock.tstate.requests) == 2
