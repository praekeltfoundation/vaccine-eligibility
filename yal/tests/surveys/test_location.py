import json
from datetime import datetime
from unittest import mock

import pytest
from sanic import Sanic, response

from vaccine.models import Message
from vaccine.testing import AppTester, TState, run_sanic
from yal import config
from yal.main import Application


@pytest.fixture
def tester():
    return AppTester(Application)


def get_rapidpro_contact(urn):
    status = "pending"
    survey_group = "1"
    if "27820001002" in urn:
        status = "completed"
    if "27820001003" in urn:
        status = None
        survey_group = None
    if "27820001004" in urn:
        survey_group = "2"
    if "27820001005" in urn:
        status = "invalid_province"
    if "27820001006" in urn:
        status = None
    return {
        "fields": {
            "ejaf_location_survey_status": status,
            "ejaf_location_survey_group": survey_group,
        },
    }


def get_rapidpro_group(name):
    count = 315
    if name == "EJAF location survey completed 2":
        count = 431
    return {"count": count}


@pytest.fixture(autouse=True)
async def rapidpro_mock():
    Sanic.test_mode = True
    app = Sanic("mock_rapidpro")
    tstate = TState()

    @app.route("/api/v2/contacts.json", methods=["POST"])
    def update_contact(request):
        tstate.requests.append(request)
        return response.json({}, status=200)

    @app.route("/api/v2/contacts.json", methods=["GET"])
    def get_contact(request):
        tstate.requests.append(request)

        urn = request.args.get("urn")
        contacts = [get_rapidpro_contact(urn)]

        return response.json(
            {
                "results": contacts,
                "next": None,
            },
            status=200,
        )

    @app.route("/api/v2/groups.json", methods=["GET"])
    def get_group(request):
        tstate.requests.append(request)

        name = request.args.get("name")
        groups = [get_rapidpro_group(name)]

        return response.json(
            {
                "results": groups,
                "next": None,
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
async def test_state_location_introduction_already_completed(tester: AppTester):
    tester.setup_user_address("27820001002")
    tester.setup_state("state_location_introduction")

    await tester.user_input(session=Message.SESSION_EVENT.NEW)

    tester.assert_state("state_location_already_completed")

    tester.assert_message("This number has already completed the location survey.")


@pytest.mark.asyncio
async def test_state_location_introduction_invalid_province(tester: AppTester):
    tester.setup_user_address("27820001005")
    tester.setup_state("state_location_introduction")

    await tester.user_input(session=Message.SESSION_EVENT.NEW)

    tester.assert_state("state_start")

    tester.assert_message(
        "\n".join(
            [
                "Unfortunately, this number is not eligible for this survey at this "
                "moment.",
                "",
                "Reply with “menu” to return to the main menu”.",
            ]
        )
    )


@pytest.mark.asyncio
async def test_state_location_introduction_not_invited(tester: AppTester):
    tester.setup_user_address("27820001003")
    tester.setup_state("state_location_introduction")
    await tester.user_input(session=Message.SESSION_EVENT.NEW)

    tester.assert_state("state_location_not_invited")

    tester.assert_message(
        "Unfortunately it looks like we already have enough people answering this "
        "survey, but thank you for your interest."
    )


@pytest.mark.asyncio
async def test_state_location_introduction_not_invited_with_group(tester: AppTester):
    tester.setup_user_address("27820001006")
    tester.setup_state("state_location_introduction")
    await tester.user_input(session=Message.SESSION_EVENT.NEW)

    tester.assert_state("state_location_not_invited")

    tester.assert_message(
        "Unfortunately it looks like we already have enough people answering this "
        "survey, but thank you for your interest."
    )


@pytest.mark.asyncio
async def test_state_location_introduction_group_max(tester: AppTester):
    tester.setup_user_address("27820001004")
    tester.setup_state("state_location_introduction")
    await tester.user_input(session=Message.SESSION_EVENT.NEW)

    tester.assert_state("state_location_not_invited")

    tester.assert_message(
        "Unfortunately it looks like we already have enough people answering this "
        "survey, but thank you for your interest."
    )


@pytest.mark.asyncio
async def test_state_location_introduction_pending(tester: AppTester):
    tester.setup_state("state_location_introduction")
    tester.user.metadata["ejaf_location_survey_status"] = "pending"
    await tester.user_input("start survey")

    tester.assert_state("state_location_introduction")

    tester.assert_message(
        "\n".join(
            [
                "*Fantastic! 👏🏾 🎉 And thank you 🙏🏽*",
                "",
                "*Before we start, here are a few important notes.* 📈",
                "",
                "This survey is just to understand who may be interested in "
                "joining a focus group discussion in September and where would be "
                "convenient for those users to meet. You do not have to be "
                "interested in participating in focus groups to complete this "
                "survey. If you indicate that you`re interested, we may phone you "
                "about being part of a focus group in the future, however you do "
                "not need to agree to participate in any future discussion.",
                "",
                "*It should only take 3 mins and we'll give you R10 airtime at the "
                "end.*",
                "",
                "👤 Your answers are anonymous and confidential. In order to "
                "respect your privacy we only ask about which city or town you "
                "live in. We won`t share data outside the BWise WhatsApp Chatbot "
                "team.",
                "",
                "✅ This study is voluntary and you can leave at any time by "
                "responding with the keyword *“menu”* however, if you exit before "
                "completing the survey, you will *not* be able to receive the R10 "
                "airtime voucher.",
                "",
                "🔒 You`ve seen and agreed to the BWise privacy policy. Just a "
                "reminder that we promise to keep all your info private and "
                "secure.",
                "",
                "Are you comfortable for us to continue? Otherwise you can leave "
                "the survey at any time by responding with the keyword “menu”. If "
                "you have any questions, please email bwise@praekelt.org",
            ]
        )
    )

    tester.assert_answer("ejaf_location_survey_group", "1")


@pytest.mark.asyncio
async def test_state_location_decline(tester: AppTester):
    tester.setup_state("state_location_introduction")
    await tester.user_input("2")

    tester.assert_state("state_start")
    tester.assert_message(
        "That's completely okay, there are no consequences to not taking part in this "
        "study. Please enjoy the BWise tool and stay safe."
    )


@pytest.mark.asyncio
async def test_state_location_question(tester: AppTester):
    tester.setup_state("state_location_introduction")
    await tester.user_input("3")

    tester.assert_state("state_location_question")
    tester.assert_message(
        "\n".join(
            [
                "You should be able to find the answer to any questions you have in "
                "the consent doc we sent you. If you still have questions, please "
                "email bwise@praekelt.org",
                "",
                "Would you like to continue?",
            ]
        )
    )

    [msg] = tester.fake_worker.outbound_messages
    assert msg.helper_metadata == {
        "document": "https://contenrepo/documents/1/sample.pdf"
    }


@pytest.mark.asyncio
async def test_state_location_question_continue(tester: AppTester):
    tester.setup_state("state_location_question")
    await tester.user_input("1")

    tester.assert_state("state_location_province")


@pytest.mark.asyncio
async def test_state_location_question_decline(tester: AppTester):
    tester.setup_state("state_location_question")
    await tester.user_input("2")

    tester.assert_state("state_start")
    tester.assert_message(
        "That's completely okay, there are no consequences to not taking part in this "
        "study. Please enjoy the BWise tool and stay safe."
    )


@pytest.mark.asyncio
async def test_state_location_province(tester: AppTester):
    tester.setup_state("state_location_introduction")
    await tester.user_input("1")

    tester.assert_state("state_location_province")
    tester.assert_message("*What province do you live in?*")


@pytest.mark.asyncio
async def test_state_location_province_excluded(tester: AppTester, rapidpro_mock):
    tester.setup_state("state_location_province")
    await tester.user_input("4")

    tester.assert_state("state_start")
    tester.assert_message(
        "\n".join(
            [
                "Sorry, we`re only recruiting people for group discussions in "
                "Gauteng, KZN and the Western Cape."
                "",
                "Reply with “menu” to return to the main menu",
            ]
        )
    )

    assert len(rapidpro_mock.tstate.requests) == 2
    request = rapidpro_mock.tstate.requests[1]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {"ejaf_location_survey_status": "invalid_province"},
    }


@pytest.mark.asyncio
async def test_state_location_name_city(tester: AppTester):
    tester.setup_state("state_location_province")
    await tester.user_input("1")

    tester.assert_state("state_location_name_city")
    tester.assert_message(
        "\n".join(
            [
                "*What is the name of the city or town you live in or live closest "
                "to?*",
                "",
                "Please *TYPE* in the name of the city or town.",
            ]
        )
    )


@pytest.mark.asyncio
async def test_state_location_name_city_invalid(tester: AppTester):
    tester.setup_state("state_location_name_city")
    await tester.user_input(
        "",
        transport_metadata={
            "message": {
                "type": "image",
                "image": {"id": "img1", "mime_type": "image/jpeg"},
            }
        },
    )

    tester.assert_state("state_location_name_city")
    tester.assert_message(
        "\n".join(
            [
                "*What is the name of the city or town you live in or live closest "
                "to?*",
                "",
                "Please *TYPE* in the name of the city or town.",
            ]
        )
    )


@pytest.mark.asyncio
async def test_state_location_area_type(tester: AppTester):
    tester.setup_state("state_location_name_city")
    await tester.user_input("jhb")

    tester.assert_state("state_location_area_type")
    tester.assert_message("What type of area are you living in?")


@pytest.mark.asyncio
async def test_state_location_group_invite(tester: AppTester):
    tester.setup_state("state_location_area_type")
    await tester.user_input("1")

    tester.assert_state("state_location_group_invite")
    tester.assert_message(
        "\n".join(
            [
                "All good, thank you! 🙌🏾",
                "",
                "We are organising group discussions for BWise users in September. "
                "The focus groups will be with other users aged 15-24 years.",
                "",
                "We'd ask about your experiences on the platform and how feasible, "
                "usable and effective the BWise chatbot is as a mobile health "
                "platform for young South Africans.",
                "",
                "*Remember that you do not have to be interested in joining the "
                "focus groups to complete this survey. If you indicate you are "
                "interested you can still reject any invitation if we do contact "
                "you.*",
                "",
                "Are you interested in being invited to one of these discussions "
                "in the future?",
            ]
        )
    )


@pytest.mark.asyncio
@mock.patch("yal.surveys.location.get_current_datetime")
async def test_state_location_group_invite_submit(
    get_current_datetime, tester: AppTester, rapidpro_mock
):
    get_current_datetime.return_value = datetime(2022, 6, 19, 17, 30)
    tester.setup_state("state_location_group_invite")
    await tester.user_input("1")

    tester.assert_state("state_location_end")
    tester.assert_message(
        "\n".join(
            [
                "*And that's a wrap!*",
                "",
                "Thank you for taking part in our survey 🙏🏽",
                "",
                "*You will get your R10 airtime within 24 hours.*",
                "",
                "You can engage with the B-Wise chatbot at any time for some "
                "helpful messages or to ask any questions.",
            ]
        )
    )

    assert len(rapidpro_mock.tstate.requests) == 2
    request = rapidpro_mock.tstate.requests[1]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {
            "ejaf_location_survey_status": "completed",
            "ejaf_location_survey_optin": "yes",
            "ejaf_location_survey_complete_time": "2022-06-19T17:30:00",
        },
    }


@pytest.mark.asyncio
@mock.patch("yal.surveys.location.get_current_datetime")
async def test_state_location_group_invite_submit_dont_understand(
    get_current_datetime, tester: AppTester, rapidpro_mock
):
    get_current_datetime.return_value = datetime(2022, 6, 19, 17, 30)
    tester.setup_state("state_location_group_invite")
    await tester.user_input("3")

    tester.assert_state("state_location_end")
    tester.assert_message(
        "\n".join(
            [
                "No problem! If you would like to learn more about the platform, "
                "please email the Bwise team at bwise@praekelt.org",
                "",
                "Thank you for taking part in our survey 🙏🏽",
                "",
                "*You will get your R10 airtime within 24 hours*",
                "",
                "You can engage with the B-Wise chatbot at any time for some helpful "
                "messages or to ask any questions.",
            ]
        )
    )

    assert len(rapidpro_mock.tstate.requests) == 2
    request = rapidpro_mock.tstate.requests[1]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {
            "ejaf_location_survey_status": "completed",
            "ejaf_location_survey_optin": "dont_understand",
            "ejaf_location_survey_complete_time": "2022-06-19T17:30:00",
        },
    }
