import json

# from datetime import date
from datetime import datetime
from unittest import mock

# from unittest import mock
#
import pytest
from sanic import Sanic, response

# from vaccine.models import Message
from vaccine.testing import AppTester, TState, run_sanic
from yal import config
from yal.main import Application
from yal.utils import get_current_datetime

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
        contact["fields"] = {
            "relationship_status": "yes",
            "gender": "",
            "dob_day": "22",
            "dob_month": "2",
            "dob_year": "2022",
            "province": "FS",
            "suburb": "TestSuburb",
            "street_name": "test street",
            "street_number": "12",
            "last_main_time": get_current_datetime().isoformat(),
            "last_mainmenu_time": get_current_datetime().isoformat(),
            "last_onboarding_time": get_current_datetime().isoformat(),
            "callback_check_time": get_current_datetime().isoformat(),
            "feedback_timestamp": get_current_datetime().isoformat(),
            "feedback_timestamp_2": get_current_datetime().isoformat(),
            "longitude": "123",
            "latitude": "456",
            "location_description": "Narnia",
            "persona_name": "Aslan",
            "persona_emoji": "🦁",
            "gender_other": "non conforming",
            "emergency_contact": "123-emergency",
        }
    return contact


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


@pytest.mark.asyncio
async def test_state_optout(tester: AppTester):
    tester.setup_state("state_catch_all")
    await tester.user_input("stop")
    tester.assert_state("state_optout")
    tester.assert_message(
        "\n".join(
            [
                "🤖 *Hi!*",
                "",
                "I just received a message from you saying *stop*.",
                "",
                "*What would you like to do?*",
                "",
                "*1.* I  want to stop receiving notifications",
                "*2.* I  want to delete all data saved about me.",
                "*3.* No change. I still want to receive messages from B-Wise",
            ]
        )
    )


@pytest.mark.asyncio
async def test_state_optout_survey_other(tester: AppTester):
    tester.setup_state("state_optout_survey")
    await tester.user_input("6")
    tester.assert_state("state_tell_us_more")


@pytest.mark.asyncio
async def test_state_optout_survey_message_volume(tester: AppTester, rapidpro_mock):
    tester.setup_state("state_optout_survey")
    await tester.user_input("1")
    tester.assert_state(None)


@pytest.mark.asyncio
async def test_state_optout_survey_user_friendliness(tester: AppTester, rapidpro_mock):
    tester.setup_state("state_optout_survey")
    await tester.user_input("2")
    tester.assert_state(None)


@pytest.mark.asyncio
async def test_state_optout_survey_irrelevant(tester: AppTester, rapidpro_mock):
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
async def test_state_optout_stop_notifications(
    tester: AppTester, rapidpro_mock
):

    tester.setup_state("state_optout")
    await tester.user_input("1")
    tester.assert_state("state_optout_survey")

    assert len(rapidpro_mock.tstate.requests) == 1

    assert [r.path for r in rapidpro_mock.tstate.requests] == ["/api/v2/contacts.json"]

    post_request = rapidpro_mock.tstate.requests[0]
    assert json.loads(post_request.body.decode("utf-8")) == {
        "fields": {
            "last_main_time": "",
            "last_mainmenu_time": "",
            "last_onboarding_time": "",
            "callback_check_time": "",
            "feedback_timestamp": "",
            "feedback_timestamp_2": "",
            "feedback_type": "",
        },
    }


@pytest.mark.asyncio
async def test_state_tell_us_more(tester: AppTester):
    tester.setup_state("state_tell_us_more")
    await tester.user_input("I am just a test human")
    tester.assert_state(None)


@pytest.mark.asyncio
@mock.patch("yal.optout.get_current_datetime")
async def test_state_optout_delete_saved(
        get_current_datetime, tester: AppTester, rapidpro_mock,
    ):

    get_current_datetime.return_value = datetime(2022, 6, 19, 17, 30)
    tester.setup_state("state_optout")
    await tester.user_input("2")
    tester.assert_state("state_delete_saved")

    # Two API calls:
    # Get profile to get old details, update profile
    assert len(rapidpro_mock.tstate.requests) == 2
    assert [r.path for r in rapidpro_mock.tstate.requests] == [
        "/api/v2/contacts.json"
    ] * 2

    post_request = rapidpro_mock.tstate.requests[1]
    assert json.loads(post_request.body.decode("utf-8")) == {
        "fields": {
            "onboarding_completed": "",
            "opted_out": "TRUE",
            "opted_out_timestamp": "2022-06-19T17:30:00",
            "age": "",
            "suggested_text": "",
            "terms_accepted": "",
            "engaged_on_facebook": "",
            "dob_year": "",
            "dob_month": "",
            "dob_day": "",
            "relationship_status": "",
            "gender": "",
            "province": "",
            "suburb": "",
            "street_name": "",
            "street_number": "",
            "last_main_time": "",
            "last_mainmenu_time": "",
            "last_onboarding_time": "",
            "callback_check_time": "",
            "feedback_timestamp": "",
            "feedback_timestamp_2": "",
            "feedback_type": "",
            "longitude": "",
            "latitude": "",
            "location_description": "",
            "persona_name": "",
            "persona_emoji": "",
            "gender_other": "",
            "emergency_contact": "",
        },
    }

    tester.assert_message(
        "\n".join(
            [
                "✅ *We've deleted all your saved personal data including:*",
                "",
                "*- Date of Birth:* 22/2/2022",
                "*- Relationship Status:* Yes",
                "*- Location:* 12 test street TestSuburb FS",
                "*- Gender:* Empty",
                "",
                "*------*",
                "*Reply:*",
                "*1* - to see your personal data",
                "0. 🏠 *Back* to Main *MENU*",
                "#. 🆘Get *HELP*",
            ]
        )
    )


@pytest.mark.asyncio
async def test_state_optout_delete_no_data(tester: AppTester, rapidpro_mock):
    tester.setup_user_address("27820001002")
    tester.setup_state("state_optout")
    await tester.user_input("2")
    tester.assert_state("state_delete_saved")

    tester.assert_message(
        "\n".join(
            [
                "✅ *We've deleted all your saved personal data including:*",
                "",
                "*- Date of Birth:* Empty",
                "*- Relationship Status:* Empty",
                "*- Location:* Empty",
                "*- Gender:* Empty",
                "",
                "*------*",
                "*Reply:*",
                "*1* - to see your personal data",
                "0. 🏠 *Back* to Main *MENU*",
                "#. 🆘Get *HELP*",
            ]
        )
    )


@pytest.mark.asyncio
async def test_state_optout_delete_saved_see_data(tester: AppTester, rapidpro_mock):
    tester.setup_state("state_delete_saved")
    await tester.user_input("1")
    tester.assert_state("state_display_preferences")


@pytest.mark.asyncio
async def test_state_optout_skip(tester: AppTester, rapidpro_mock):
    tester.setup_state("state_optout")
    await tester.user_input("3")
    tester.assert_state("state_mainmenu")
