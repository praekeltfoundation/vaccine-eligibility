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
            "age": "22",
            "province": "FS",
            "suburb": "TestSuburb",
            "street_name": "test street",
            "street_number": "12",
            "location_description": "12 test street TestSuburb FS",
            "last_main_time": get_current_datetime().isoformat(),
            "last_mainmenu_time": get_current_datetime().isoformat(),
            "last_onboarding_time": get_current_datetime().isoformat(),
            "callback_check_time": get_current_datetime().isoformat(),
            "feedback_timestamp": get_current_datetime().isoformat(),
            "feedback_timestamp_2": get_current_datetime().isoformat(),
            "longitude": "123",
            "latitude": "456",
            "persona_name": "Aslan",
            "persona_emoji": "🦁",
            "emergency_contact": "123-emergency",
        }
    return contact


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

    @app.route("/api/v2/fields.json", methods=["GET"])
    def get_instance_fields(request):
        tstate.requests.append(request)
        # assert True == False
        return response.json(
            {
                "next": None,
                "previous": None,
                "results": [
                    {
                        "key": "second_phase2_send",
                        "label": "second phase2 send",
                        "value_type": "text",
                        "pinned": False,
                    },
                    {
                        "key": "assessment_reminder_name",
                        "label": "Assessment Reminder Name",
                        "value_type": "text",
                        "pinned": False,
                    },
                    {
                        "key": "phase2_invite_failed",
                        "label": "phase2 invite failed",
                        "value_type": "text",
                        "pinned": False,
                    },
                    {
                        "key": "sent_phase2_invite",
                        "label": "sent phase2 invite",
                        "value_type": "text",
                        "pinned": False,
                    },
                    {
                        "key": "sexual_health_lit_assessment_sent",
                        "label": "sexual health lit assessment sent",
                        "value_type": "text",
                        "pinned": False,
                    },
                    {
                        "key": "sexual_health_lit_score",
                        "label": "Sexual Health Lit Score",
                        "value_type": "text",
                        "pinned": False,
                    },
                    {
                        "key": "assessment_reminder",
                        "label": "Assessment Reminder",
                        "value_type": "datetime",
                        "pinned": False,
                    },
                    {
                        "key": "push_message_opt_in",
                        "label": "Push Message Opt In",
                        "value_type": "text",
                        "pinned": True,
                    },
                    {
                        "key": "pages_seen",
                        "label": "pages seen",
                        "value_type": "text",
                        "pinned": False,
                    },
                    {
                        "key": "test_day",
                        "label": "test day",
                        "value_type": "text",
                        "pinned": False,
                    },
                    {
                        "key": "self_perceived_healthcare_score",
                        "label": "self perceived healthcare score",
                        "value_type": "text",
                        "pinned": False,
                    },
                    {
                        "key": "self_perceived_healthcare_risk",
                        "label": "self perceived healthcare risk",
                        "value_type": "text",
                        "pinned": False,
                    },
                    {
                        "key": "body_image_score",
                        "label": "body image score",
                        "value_type": "text",
                        "pinned": False,
                    },
                    {
                        "key": "body_image_risk",
                        "label": "body image risk",
                        "value_type": "text",
                        "pinned": False,
                    },
                    {
                        "key": "gender_attitude_score",
                        "label": "gender attitude score",
                        "value_type": "text",
                        "pinned": False,
                    },
                    {
                        "key": "gender_attitude_risk",
                        "label": "gender attitude risk",
                        "value_type": "text",
                        "pinned": False,
                    },
                    {
                        "key": "connectedness_score",
                        "label": "connectedness score",
                        "value_type": "text",
                        "pinned": False,
                    },
                    {
                        "key": "connectedness_risk",
                        "label": "connectedness risk",
                        "value_type": "text",
                        "pinned": False,
                    },
                    {
                        "key": "depression_and_anxiety_score",
                        "label": "depression  and anxiety score",
                        "value_type": "text",
                        "pinned": False,
                    },
                    {
                        "key": "depression_and_anxiety_risk",
                        "label": "depression and anxiety risk",
                        "value_type": "text",
                        "pinned": False,
                    },
                    {
                        "key": "push_related_page_id",
                        "label": "Push Related Page Id",
                        "value_type": "text",
                        "pinned": False,
                    },
                    {
                        "key": "selfperceived_healthcare_complete",
                        "label": "SelfPerceived HealthCare Complete",
                        "value_type": "text",
                        "pinned": False,
                    },
                    {
                        "key": "body_image_content_complete",
                        "label": "Body Image Content Complete",
                        "value_type": "text",
                        "pinned": False,
                    },
                    {
                        "key": "gender_attitude_content_complete",
                        "label": "Gender Attitude Content Complete",
                        "value_type": "text",
                        "pinned": False,
                    },
                    {
                        "key": "connectedness_content_complete",
                        "label": "Connectedness Content Complete",
                        "value_type": "text",
                        "pinned": False,
                    },
                    {
                        "key": "educational_content_complete",
                        "label": "Educational Content Complete",
                        "value_type": "text",
                        "pinned": False,
                    },
                    {
                        "key": "depression_content_complete",
                        "label": "Depression Content Complete",
                        "value_type": "text",
                        "pinned": False,
                    },
                    {
                        "key": "fun_content_complete",
                        "label": "Fun Content Complete",
                        "value_type": "text",
                        "pinned": False,
                    },
                    {
                        "key": "current_content_set",
                        "label": "Current Content Set",
                        "value_type": "text",
                        "pinned": False,
                    },
                    {
                        "key": "sexual_health_lit_risk",
                        "label": "Sexual Health Lit Risk",
                        "value_type": "text",
                        "pinned": False,
                    },
                    {
                        "key": "is_tester",
                        "label": "Is Tester",
                        "value_type": "text",
                        "pinned": False,
                    },
                    {
                        "key": "privacy_reminder_sent",
                        "label": "Privacy Reminder Sent",
                        "value_type": "text",
                        "pinned": False,
                    },
                    {
                        "key": "segment_survey_complete",
                        "label": "Segment Survey Complete",
                        "value_type": "text",
                        "pinned": False,
                    },
                    {
                        "key": "feedback_timestamp_2",
                        "label": "Feedback Timestamp 2",
                        "value_type": "datetime",
                        "pinned": False,
                    },
                    {
                        "key": "feedback_type_2",
                        "label": "Feedback Type 2",
                        "value_type": "text",
                        "pinned": False,
                    },
                    {
                        "key": "feedback_survey_sent_2",
                        "label": "Feedback Survey Sent 2",
                        "value_type": "text",
                        "pinned": False,
                    },
                    {
                        "key": "engaged_on_facebook",
                        "label": "Engaged on Facebook",
                        "value_type": "text",
                        "pinned": False,
                    },
                    {
                        "key": "longitude",
                        "label": "Longitude",
                        "value_type": "text",
                        "pinned": False,
                    },
                    {
                        "key": "latitude",
                        "label": "latitude",
                        "value_type": "text",
                        "pinned": False,
                    },
                    {
                        "key": "location_description",
                        "label": "Location Description",
                        "value_type": "text",
                        "pinned": False,
                    },
                    {
                        "key": "feedback_survey_sent",
                        "label": "Feedback Survey Sent",
                        "value_type": "text",
                        "pinned": False,
                    },
                    {
                        "key": "feedback_timestamp",
                        "label": "Feedback Timestamp",
                        "value_type": "datetime",
                        "pinned": False,
                    },
                    {
                        "key": "feedback_type",
                        "label": "Feedback Type",
                        "value_type": "text",
                        "pinned": False,
                    },
                    {
                        "key": "persona_name",
                        "label": "Persona Name",
                        "value_type": "text",
                        "pinned": False,
                    },
                    {
                        "key": "age",
                        "label": "age",
                        "value_type": "numeric",
                        "pinned": False,
                    },
                    {
                        "key": "persona_emoji",
                        "label": "Persona Emoji",
                        "value_type": "text",
                        "pinned": False,
                    },
                    {
                        "key": "aaq_timeout_sent",
                        "label": "AAQ Timeout Sent",
                        "value_type": "text",
                        "pinned": False,
                    },
                    {
                        "key": "aaq_timeout_type",
                        "label": "AAQ Timeout Type",
                        "value_type": "text",
                        "pinned": False,
                    },
                    {
                        "key": "next_aaq_timeout_time",
                        "label": "Next AAQ Timeout Time",
                        "value_type": "datetime",
                        "pinned": False,
                    },
                    {
                        "key": "topics_viewed",
                        "label": "Topics Viewed",
                        "value_type": "text",
                        "pinned": False,
                    },
                    {
                        "key": "terms_accepted",
                        "label": "Terms Accepted",
                        "value_type": "text",
                        "pinned": False,
                    },
                    {
                        "key": "suburb",
                        "label": "Suburb",
                        "value_type": "text",
                        "pinned": False,
                    },
                    {
                        "key": "street_number",
                        "label": "Street Number",
                        "value_type": "text",
                        "pinned": False,
                    },
                    {
                        "key": "street_name",
                        "label": "Street Name",
                        "value_type": "text",
                        "pinned": False,
                    },
                    {
                        "key": "relationship_status",
                        "label": "Relationship Status",
                        "value_type": "text",
                        "pinned": False,
                    },
                    {
                        "key": "province",
                        "label": "Province",
                        "value_type": "text",
                        "pinned": False,
                    },
                    {
                        "key": "opted_out_timestamp",
                        "label": "Opted Out Timestamp",
                        "value_type": "datetime",
                        "pinned": False,
                    },
                    {
                        "key": "opted_out",
                        "label": "Opted Out",
                        "value_type": "text",
                        "pinned": False,
                    },
                    {
                        "key": "gender_other",
                        "label": "Gender Other",
                        "value_type": "text",
                        "pinned": False,
                    },
                    {
                        "key": "gender",
                        "label": "Gender",
                        "value_type": "text",
                        "pinned": False,
                    },
                    {
                        "key": "emergency_contact",
                        "label": "Emergency Contact",
                        "value_type": "text",
                        "pinned": False,
                    },
                    {
                        "key": "dob_year",
                        "label": "DOB Year",
                        "value_type": "text",
                        "pinned": False,
                    },
                    {
                        "key": "dob_month",
                        "label": "DOB Month",
                        "value_type": "text",
                        "pinned": False,
                    },
                    {
                        "key": "dob_day",
                        "label": "DOB Day",
                        "value_type": "text",
                        "pinned": False,
                    },
                    {
                        "key": "callback_abandon_reason",
                        "label": "Callback Abandon Reason",
                        "value_type": "text",
                        "pinned": False,
                    },
                    {
                        "key": "onboarding_completed",
                        "label": "Onboarding Completed",
                        "value_type": "text",
                        "pinned": False,
                    },
                    {
                        "key": "usertesting_feedback_complete",
                        "label": "Usertesting Feedback Complete",
                        "value_type": "text",
                        "pinned": False,
                    },
                    {
                        "key": "suggested_text",
                        "label": "Suggested Text",
                        "value_type": "text",
                        "pinned": False,
                    },
                    {
                        "key": "skip_usertesting_airtime",
                        "label": "Skip Usertesting Airtime",
                        "value_type": "text",
                        "pinned": False,
                    },
                    {
                        "key": "onboarding_reminder_type",
                        "label": "Onboarding Reminder Type",
                        "value_type": "text",
                        "pinned": False,
                    },
                    {
                        "key": "onboarding_reminder_sent",
                        "label": "Onboarding Reminder Sent",
                        "value_type": "text",
                        "pinned": False,
                    },
                    {
                        "key": "last_onboarding_time",
                        "label": "Last Onboarding Time",
                        "value_type": "datetime",
                        "pinned": False,
                    },
                    {
                        "key": "last_menu_time",
                        "label": "deleted-f98a17a9-9819-447d-81a9-6d45",
                        "value_type": "datetime",
                        "pinned": False,
                    },
                    {
                        "key": "last_mainmenu_time",
                        "label": "Last Mainmenu Time",
                        "value_type": "datetime",
                        "pinned": False,
                    },
                    {
                        "key": "last_main_time",
                        "label": "Last Main Time",
                        "value_type": "datetime",
                        "pinned": False,
                    },
                    {
                        "key": "callback_check_time",
                        "label": "Callback Check Time",
                        "value_type": "datetime",
                        "pinned": False,
                    },
                    {
                        "key": "callback_check_sent",
                        "label": "Callback Check Sent",
                        "value_type": "text",
                        "pinned": False,
                    },
                ],
            },
            status=200,
        )

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
                "🦁 *Hi!*",
                "",
                "I just received a message from you saying *stop*.",
                "",
                "*What would you like to do?*",
                "",
                "*1.* Stop receiving notifications",
                "*2.* Delete all data saved about me.",
                "*3.* No change, thanks",
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
    tester.assert_state("state_farewell_optout")


@pytest.mark.asyncio
async def test_state_optout_survey_user_friendliness(tester: AppTester, rapidpro_mock):
    tester.setup_state("state_optout_survey")
    await tester.user_input("2")
    tester.assert_state("state_farewell_optout")


@pytest.mark.asyncio
async def test_state_optout_survey_irrelevant(tester: AppTester, rapidpro_mock):
    tester.setup_state("state_optout_survey")
    await tester.user_input("3")
    tester.assert_state("state_farewell_optout")


@pytest.mark.asyncio
async def test_state_optout_survey_boring(tester: AppTester):
    tester.setup_state("state_optout_survey")
    await tester.user_input("4")
    tester.assert_state("state_farewell_optout")


@pytest.mark.asyncio
async def test_state_optout_survey_lengthy(tester: AppTester):
    tester.setup_state("state_optout_survey")
    await tester.user_input("5")
    tester.assert_state("state_farewell_optout")


@pytest.mark.asyncio
async def test_state_optout_survey_none(tester: AppTester):
    tester.setup_state("state_optout_survey")
    await tester.user_input("7")
    tester.assert_state("state_farewell_optout")


@pytest.mark.asyncio
async def test_state_optout_survey_skip(tester: AppTester):
    tester.setup_state("state_optout_survey")
    await tester.user_input("8")
    tester.assert_state("state_farewell_optout")


@pytest.mark.asyncio
async def test_state_optout_stop_notifications(tester: AppTester, rapidpro_mock):

    tester.setup_state("state_optout")
    await tester.user_input("1")
    tester.assert_state("state_optout_survey")

    assert len(rapidpro_mock.tstate.requests) == 2

    assert [r.path for r in rapidpro_mock.tstate.requests] == [
        "/api/v2/contacts.json"
    ] * 2

    post_request = rapidpro_mock.tstate.requests[1]
    assert json.loads(post_request.body.decode("utf-8")) == {
        "fields": {
            "last_main_time": "",
            "last_mainmenu_time": "",
            "last_onboarding_time": "",
            "callback_check_time": "",
            "feedback_timestamp": "",
            "feedback_timestamp_2": "",
            "feedback_type": "",
            "push_message_opt_in": "False",
        },
    }


@pytest.mark.asyncio
async def test_state_tell_us_more(tester: AppTester):
    tester.setup_state("state_tell_us_more")
    await tester.user_input("I am just a test human")
    tester.assert_state("state_farewell_optout")


@pytest.mark.asyncio
@mock.patch("yal.optout.get_current_datetime")
async def test_state_optout_delete_saved(
    get_current_datetime,
    tester: AppTester,
    rapidpro_mock,
):

    get_current_datetime.return_value = datetime(2022, 6, 19, 17, 30)
    tester.setup_state("state_optout")
    await tester.user_input("2")
    tester.assert_state("state_delete_saved")

    # Three API calls:
    # Get profile to get old details, get all instance fields, update profile
    assert len(rapidpro_mock.tstate.requests) == 3
    expected_paths = [
        "/api/v2/contacts.json",
        "/api/v2/fields.json",
        "/api/v2/contacts.json",
    ]
    assert expected_paths == [r.path for r in rapidpro_mock.tstate.requests]
    post_request = rapidpro_mock.tstate.requests[2]
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
            "push_message_opt_in": "False",
            "longitude": "",
            "latitude": "",
            "location_description": "",
            "persona_name": "",
            "persona_emoji": "",
            "emergency_contact": "",
        },
    }
    tester.assert_message(
        "\n".join(
            [
                "✅ *We've deleted all your saved personal data including:*",
                "",
                "*- Age:* 22",
                "*- Relationship Status:* Yes",
                "*- Location:* 12 test street TestSuburb FS",
                "*- Gender:* Empty",
                "",
                "*------*",
                "*Reply:*",
                "1 - to see your personal data",
                "0. 🏠 Back to Main *MENU*",
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
                "*- Age:* Empty",
                "*- Relationship Status:* Empty",
                "*- Location:* Empty",
                "*- Gender:* Empty",
                "",
                "*------*",
                "*Reply:*",
                "1 - to see your personal data",
                "0. 🏠 Back to Main *MENU*",
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
    tester.assert_state("state_opt_out_no_changes")
