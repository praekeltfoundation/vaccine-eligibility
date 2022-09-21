import json

# from datetime import date
from datetime import datetime
from unittest import mock

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
        }
    return contact


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
async def test_state_optout(tester: AppTester):
    tester.setup_state("state_catch_all")
    await tester.user_input("stop")
    tester.assert_state("state_optout")
    tester.assert_message(
        "\n".join(
            [
                "*🙍🏾‍♀️Hi!*",
                "",
                "I just received a message from you saying *stop*.",
                "",
                "*What would you like to do?*",
                "",
                "*1* - I  want to stop receiving notifications",
                "*2* - I  want to delete all data saved about me.",
                "*3* - No change. I still want to receive messages from B-Wise",
            ]
        )
    )


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
@mock.patch("yal.optout.get_current_datetime")
async def test_state_optout_stop_notifications(
    get_current_datetime, tester: AppTester, rapidpro_mock
):
    get_current_datetime.return_value = datetime(2022, 6, 19, 17, 30)

    tester.setup_state("state_optout")
    await tester.user_input("1")
    tester.assert_state("state_optout_survey")

    assert len(rapidpro_mock.app.requests) == 1

    assert [r.path for r in rapidpro_mock.app.requests] == ["/api/v2/contacts.json"]

    post_request = rapidpro_mock.app.requests[0]
    assert json.loads(post_request.body.decode("utf-8")) == {
        "fields": {
            "onboarding_completed": "",
            "opted_out": "TRUE",
            "opted_out_timestamp": "2022-06-19T17:30:00",
        },
    }


@pytest.mark.asyncio
async def test_state_tell_us_more(tester: AppTester):
    tester.setup_state("state_tell_us_more")
    await tester.user_input("I am just a test human")
    tester.assert_state(None)


@pytest.mark.asyncio
async def test_state_optout_delete_saved(tester: AppTester, rapidpro_mock):
    tester.setup_state("state_optout")
    await tester.user_input("2")
    tester.assert_state("state_delete_saved")

    # Two API calls:
    # Get profile to get old details, update profile
    assert len(rapidpro_mock.app.requests) == 2
    assert [r.path for r in rapidpro_mock.app.requests] == ["/api/v2/contacts.json"] * 2

    post_request = rapidpro_mock.app.requests[1]
    assert json.loads(post_request.body.decode("utf-8")) == {
        "fields": {
            "dob_year": "",
            "dob_month": "",
            "dob_day": "",
            "relationship_status": "",
            "gender": "",
            "province": "",
            "suburb": "",
            "street_name": "",
            "street_number": "",
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
    tester.assert_state("state_change_info_prompt")


@pytest.mark.asyncio
async def test_state_optout_skip(tester: AppTester):
    tester.setup_state("state_optout")
    await tester.user_input("3")
    tester.assert_state(None)
