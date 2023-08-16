import json

import pytest
from sanic import Sanic, response

from vaccine.models import Message
from vaccine.testing import AppTester, TState, run_sanic
from yal import config

# TODO: fix this import once this flow is hooked up in main application
from yal.surveys.location import Application


@pytest.fixture
def tester():
    return AppTester(Application)


@pytest.fixture(autouse=True)
async def rapidpro_mock():
    Sanic.test_mode = True
    app = Sanic("mock_rapidpro")
    tstate = TState()

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
async def test_state_location_introduction_already_completed(tester: AppTester):
    tester.setup_state("state_location_introduction")
    tester.user.metadata["ejaf_location_survey_status"] = "completed"

    await tester.user_input(session=Message.SESSION_EVENT.NEW)

    tester.assert_state("state_location_introduction")

    tester.assert_message("This number has already completed the location survey.")


@pytest.mark.asyncio
async def test_state_location_introduction_not_invited(tester: AppTester):
    tester.setup_state("state_location_introduction")
    await tester.user_input(session=Message.SESSION_EVENT.NEW)

    tester.assert_state("state_location_introduction")

    tester.assert_message(
        "Unfortunately it looks like we already have enough people answering this "
        "survey, but thank you for your interest."
    )


@pytest.mark.asyncio
async def test_state_location_introduction_pending(tester: AppTester):
    tester.setup_state("state_location_introduction")
    tester.user.metadata["ejaf_location_survey_status"] = "pending"
    await tester.user_input(session=Message.SESSION_EVENT.NEW)

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


@pytest.mark.asyncio
async def test_state_location_province(tester: AppTester):
    tester.setup_state("state_location_introduction")
    tester.user.metadata["ejaf_location_survey_status"] = "pending"
    await tester.user_input("1")

    tester.assert_state("state_location_province")
    tester.assert_message("*What province do you live in?*")


@pytest.mark.asyncio
async def test_state_location_province_excluded(tester: AppTester):
    tester.setup_state("state_location_province")
    await tester.user_input("4")

    tester.assert_state("state_location_introduction")
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
async def test_state_location_group_invite_submit(tester: AppTester, rapidpro_mock):
    tester.setup_state("state_location_group_invite")
    await tester.user_input("1")

    tester.assert_state("state_location_introduction")
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

    assert len(rapidpro_mock.tstate.requests) == 1
    request = rapidpro_mock.tstate.requests[0]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {"ejaf_location_survey_status": "completed"},
    }
