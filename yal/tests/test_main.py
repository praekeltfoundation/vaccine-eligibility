from datetime import datetime
from unittest import mock

import pytest
from sanic import Sanic, response

from vaccine.testing import AppTester
from yal import config, turn
from yal.change_preferences import Application as ChangePreferencesApplication
from yal.main import Application
from yal.mainmenu import Application as MainMenuApplication
from yal.onboarding import Application as OnboardingApplication
from yal.pleasecallme import Application as PleaseCallMeApplication
from yal.quiz import Application as QuizApplication
from yal.servicefinder import Application as ServiceFinderApplication
from yal.terms_and_conditions import Application as TermsApplication


def test_no_state_name_clashes():
    mm_states = set(s for s in dir(MainMenuApplication) if s.startswith("state_"))
    on_states = set(s for s in dir(OnboardingApplication) if s.startswith("state_"))
    te_states = set(s for s in dir(TermsApplication) if s.startswith("state_"))
    cp_states = set(
        s for s in dir(ChangePreferencesApplication) if s.startswith("state_")
    )
    q_states = set(s for s in dir(QuizApplication) if s.startswith("state_"))
    pc_states = set(s for s in dir(PleaseCallMeApplication) if s.startswith("state_"))
    sf_states = set(s for s in dir(ServiceFinderApplication) if s.startswith("state_"))
    intersection = (
        mm_states & on_states & te_states & cp_states & q_states & pc_states & sf_states
    ) - {
        "state_name",
        "state_error",
    }
    assert len(intersection) == 0, f"Common states to both apps: {intersection}"


@pytest.fixture
def tester():
    return AppTester(Application)


@pytest.fixture
async def turn_api_mock(sanic_client, tester):
    Sanic.test_mode = True
    app = Sanic("mock_turn_api")
    app.requests = []
    app.errors = 0
    app.errormax = 0

    @app.route("/v1/contacts/<msisdn:int>/profile", methods=["GET"])
    def callback(request, msisdn):
        app.requests.append(request)
        if app.errormax:
            if app.errors < app.errormax:
                app.errors += 1
                return response.json({}, status=500)
        return response.json(
            {
                "fields": {
                    "prototype_user": msisdn == 27820001001,
                    "onboarding_completed": msisdn == 27820001001,
                    "terms_accepted": msisdn == 27820001001,
                    "province": "FS",
                    "suburb": "cape town",
                    "street_name": "high level",
                    "street_number": "99",
                }
            }
        )

    client = await sanic_client(app)
    get_profile_url = turn.get_profile_url

    host = f"http://{client.host}:{client.port}"
    turn.get_profile_url = (
        lambda whatsapp_id: f"{host}/v1/contacts/{whatsapp_id}/profile"
    )

    yield client
    turn.get_profile_url = get_profile_url


@pytest.fixture
async def contentrepo_api_mock(sanic_client):
    Sanic.test_mode = True
    app = Sanic("contentrepo_api_mock")
    app.requests = []

    @app.route("/api/v2/pages", methods=["GET"])
    def get_main_menu(request):
        app.requests.append(request)
        return response.json(
            {
                "count": 1,
                "results": [{"id": 111, "title": "Main Menu 1 💊"}],
            }
        )

    client = await sanic_client(app)
    url = config.CONTENTREPO_API_URL
    config.CONTENTREPO_API_URL = f"http://{client.host}:{client.port}"
    yield client
    config.CONTENTREPO_API_URL = url


@pytest.mark.asyncio
async def test_reset_keyword(tester: AppTester, turn_api_mock, contentrepo_api_mock):
    tester.setup_state("state_catch_all")
    await tester.user_input("hi")
    tester.assert_state("state_mainmenu")
    tester.assert_num_messages(1)

    assert len(turn_api_mock.app.requests) == 1
    assert len(contentrepo_api_mock.app.requests) == 2


@pytest.mark.asyncio
@mock.patch("yal.pleasecallme.get_current_datetime")
async def test_help_keyword(get_current_datetime, tester: AppTester):
    get_current_datetime.return_value = datetime(2022, 6, 21, 13, 30)

    tester.setup_state("state_catch_all")
    await tester.user_input("help")
    tester.assert_state("state_in_hours")
    tester.assert_num_messages(1)


@pytest.mark.asyncio
async def test_state_start_to_catch_all(tester: AppTester, turn_api_mock):
    await tester.user_input("AAA")
    tester.assert_state("state_start")
    tester.assert_num_messages(1)
    tester.assert_message("TODO: Catch all temp flow")

    assert len(turn_api_mock.app.requests) == 1


@pytest.mark.asyncio
async def test_state_start_to_mainmenu(
    tester: AppTester, turn_api_mock, contentrepo_api_mock
):
    await tester.user_input("hi")
    tester.assert_state("state_mainmenu")
    tester.assert_num_messages(1)

    assert len(turn_api_mock.app.requests) == 1
    assert len(contentrepo_api_mock.app.requests) == 2

    tester.assert_metadata("province", "FS")
    tester.assert_metadata("suburb", "cape town")
    tester.assert_metadata("street_name", "high level")
    tester.assert_metadata("street_number", "99")


@pytest.mark.asyncio
async def test_state_start_to_coming_soon(tester: AppTester, turn_api_mock):
    tester.setup_user_address("27820001002")
    await tester.user_input("hi")
    tester.assert_state("state_start")
    tester.assert_num_messages(1)
    tester.assert_message("TODO: coming soon")

    assert len(turn_api_mock.app.requests) == 1
