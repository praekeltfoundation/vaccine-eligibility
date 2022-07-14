import json

# from datetime import date
# from unittest import mock
#
import pytest
from sanic import Sanic, response

# from vaccine.models import Message
from vaccine.testing import AppTester
from yal import config
from yal.main import Application

# TODO: add number of messages assertions


@pytest.fixture
def tester():
    return AppTester(Application)


def get_rapidpro_contact(urn):
    return {
        "uuid": "b733e997-b0b4-4d4d-a3ad-0546e1644aa9",
        "name": "Test Human",
        "language": "eng",
        "groups": [],
        "fields": {
            "relationship_status": "yes",
            "gender": "boy_man",
            "dob_day": "22",
            "dob_month": "2",
            "dob_year": "2022",
            "province": "FS",
            "suburb": "TestSuburb",
            "street_name": "test street",
            "street_number": "12",
        },
        "blocked": False,
        "stopped": False,
        "created_on": "2015-11-11T08:30:24.922024+00:00",
        "modified_on": "2015-11-11T08:30:25.525936+00:00",
        "urns": [urn],
    }


@pytest.fixture
async def rapidpro_mock(sanic_client):
    Sanic.test_mode = True
    app = Sanic("mock_rapidpro")
    app.requests = []
    app.errors = 0
    app.errormax = 0

    @app.route("/api/v2/contacts.json", methods=["GET"])
    def get_contact(request):
        app.requests.append(request)
        if app.errormax:
            if app.errors < app.errormax:
                app.errors += 1
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
        app.requests.append(request)
        return response.json({}, status=200)

    client = await sanic_client(app)
    url = config.RAPIDPRO_URL
    config.RAPIDPRO_URL = f"http://{client.host}:{client.port}"
    config.RAPIDPRO_TOKEN = "testtoken"
    yield client
    config.RAPIDPRO_URL = url


@pytest.mark.asyncio
async def test_state_optout_stop_messages(tester: AppTester):
    tester.setup_state("state_optout")
    await tester.user_input("1")
    tester.assert_state("state_optout_survey")
    tester.assert_answer("state_optout", "stop messages")


@pytest.mark.asyncio
async def test_state_optout_survey_other(tester: AppTester):
    tester.setup_state("state_optout_survey")
    await tester.user_input("6")
    tester.assert_state("state_tell_us_more")


@pytest.mark.asyncio
async def test_state_optout_survey_message_volume(tester: AppTester):
    tester.setup_state("state_optout_survey")
    await tester.user_input("1")
    tester.assert_state(None)


@pytest.mark.asyncio
async def test_state_optout_survey_user_friendliness(tester: AppTester):
    tester.setup_state("state_optout_survey")
    await tester.user_input("2")
    tester.assert_state(None)


@pytest.mark.asyncio
async def test_state_optout_survey_irrelevant(tester: AppTester):
    tester.setup_state("state_optout_survey")
    await tester.user_input("3")
    tester.assert_state(None)


@pytest.mark.asyncio
async def test_state_optout_survey_boring(tester: AppTester):
    tester.setup_state("state_optout_survey")
    await tester.user_input("4")
    tester.assert_state(None)


@pytest.mark.asyncio
async def test_state_optout_survey_lengthy(tester: AppTester):
    tester.setup_state("state_optout_survey")
    await tester.user_input("5")
    tester.assert_state(None)


@pytest.mark.asyncio
async def test_state_optout_survey_none(tester: AppTester):
    tester.setup_state("state_optout_survey")
    await tester.user_input("7")
    tester.assert_state(None)


@pytest.mark.asyncio
async def test_state_optout_survey_skip(tester: AppTester):
    tester.setup_state("state_optout_survey")
    await tester.user_input("8")
    tester.assert_state(None)


@pytest.mark.asyncio
async def test_state_optout_stop_notifications(tester: AppTester):
    tester.setup_state("state_optout")
    await tester.user_input("2")
    tester.assert_state("state_optout_survey")


@pytest.mark.asyncio
async def test_state_optout_delete_saved(tester: AppTester, rapidpro_mock):
    tester.setup_state("state_optout")
    await tester.user_input("3")
    tester.assert_state("state_change_info_prompt")

    # Three API calls:
    # Get profile to get old details, update profile
    # and redirect to change preferences menu
    assert len(rapidpro_mock.app.requests) == 3
    assert [r.path for r in rapidpro_mock.app.requests] == ["/api/v2/contacts.json"] * 3

    post_request = rapidpro_mock.app.requests[1]
    assert json.loads(post_request.body.decode("utf-8")) == {
        "fields": {
            "onboarding_completed": "True",
            "dob_year": "",
            "dob_month": "",
            "dob_day": "",
            "relationship_status": "",
            "gender": "",
            "gender_other": "",
            "province": "",
            "suburb": "",
            "street_name": "",
            "street_number": "",
        },
    }


@pytest.mark.asyncio
async def test_state_optout_skip(tester: AppTester):
    tester.setup_state("state_optout")
    await tester.user_input("4")
    tester.assert_state(None)
