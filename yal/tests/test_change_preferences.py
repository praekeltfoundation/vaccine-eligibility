import json

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
    return {
        "uuid": "b733e997-b0b4-4d4d-a3ad-0546e1644aa9",
        "name": "",
        "language": "eng",
        "groups": [],
        "fields": {
            "relationship_status": None,
            "gender": "male",
            "age": "22",
            "persona_emoji": "🦸",
            "persona_name": "Caped Crusader",
            "location_description": "test street Test Suburb",
            "latitude": -3.866_651,
            "longitude": 51.195_827,
        },
        "blocked": False,
        "stopped": False,
        "created_on": "2015-11-11T08:30:24.922024+00:00",
        "modified_on": "2015-11-11T08:30:25.525936+00:00",
        "urns": [urn],
    }


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

    async with run_sanic(app) as server:
        url = config.RAPIDPRO_URL
        config.RAPIDPRO_URL = f"http://{server.host}:{server.port}"
        config.RAPIDPRO_TOKEN = "testtoken"
        server.tstate = tstate
        yield server
        config.RAPIDPRO_URL = url


@pytest.fixture
async def google_api_mock():
    Sanic.test_mode = True
    app = Sanic("mock_google_api")
    tstate = TState()
    tstate.status = "OK"

    @app.route("/maps/api/geocode/json", methods=["GET"])
    def desc_from_pin(request):
        tstate.requests.append(request)
        if tstate.errormax:
            if tstate.errors < tstate.errormax:
                tstate.errors += 1
                return response.json({}, status=500)
        if tstate.status == "OK":
            data = {
                "status": "OK",
                "results": [
                    {
                        "formatted_address": "277 Bedford Avenue, Brooklyn, NY 11211, "
                        "USA",
                        "place_id": "ChIJd8BlQ2BZwokRAFUEcm_qrcA",
                    }
                ],
            }
        else:
            data = {"status": tstate.status}
        return response.json(data, status=200)

    async with run_sanic(app) as server:
        config.GOOGLE_PLACES_KEY = "TEST-KEY"
        url = config.GOOGLE_PLACES_URL
        config.GOOGLE_PLACES_URL = f"http://{server.host}:{server.port}"
        server.tstate = tstate
        yield server
        config.GOOGLE_PLACES_URL = url


@pytest.mark.asyncio
async def test_state_display_preferences(tester: AppTester, rapidpro_mock):
    tester.user.metadata["persona_emoji"] = "🦸"
    tester.user.metadata["persona_name"] = "Caped Crusader"
    tester.setup_state("state_display_preferences")
    await tester.user_input(session=Message.SESSION_EVENT.NEW)
    tester.assert_num_messages(1)

    tester.assert_message(
        "\n".join(
            [
                "⚙️CHAT SETTINGS / *Update your info*",
                "-----",
                "Here's the info you've saved. *What info would you like to "
                "change?*",
                "",
                "🍰 *Age*",
                "22",
                "",
                "🌈Gender",
                "Male",
                "",
                "🤖*Bot Name+emoji*",
                "🦸 Caped Crusader",
                "",
                "❤️ *Relationship?*",
                "Empty",
                "",
                "📍*Location*",
                "test street Test Suburb",
                "",
                "*-----*",
                "*Or reply:*",
                "*0 -* 🏠 Back to Main *MENU*",
                "*# -* 🆘 Get *HELP*",
            ]
        ),
        list_items=["Age", "Gender", "Bot name + emoji", "Relationship?", "Location"],
    )

    assert [r.path for r in rapidpro_mock.tstate.requests] == ["/api/v2/contacts.json"]


@pytest.mark.asyncio
async def test_state_update_gender(tester: AppTester, rapidpro_mock):
    tester.setup_state("state_display_preferences")
    await tester.user_input("gender")
    tester.assert_num_messages(1)
    tester.assert_state("state_update_gender")

    tester.assert_message(
        "\n".join(
            [
                "*CHAT SETTINGS / ⚙️ Change or update your info* / *Gender*",
                "*-----*",
                "",
                "*What's your gender?*",
                "",
                "Please click the button and select the option you think best "
                "describes you:",
                "",
                "*1* - Female",
                "*2* - Male",
                "*3* - Non-binary",
                "*4* - None of these",
                "*5* - Rather not say",
                "*6* - Skip",
            ]
        ),
        list_items=[
            "Female",
            "Male",
            "Non-binary",
            "None of these",
            "Rather not say",
            "Skip",
        ],
    )

    assert [r.path for r in rapidpro_mock.tstate.requests] == ["/api/v2/contacts.json"]


@pytest.mark.asyncio
async def test_state_update_gender_from_list(tester: AppTester, rapidpro_mock):
    tester.setup_state("state_update_gender")

    await tester.user_input("Non-Binary")

    tester.assert_answer("state_update_gender", "non_binary")
    tester.assert_num_messages(1)

    tester.assert_message(
        "\n".join(
            [
                "*CHAT SETTINGS / ⚙️ Change or update your info* / *Gender*",
                "-----",
                "",
                "*You've chosen Non-binary as your gender.*",
                "",
                "Is this correct?",
                "",
                "1. Yes",
                "2. No",
            ]
        ),
    )

    tester.assert_state("state_update_gender_confirm")

    assert [r.method for r in rapidpro_mock.tstate.requests] == ["GET"]


@pytest.mark.asyncio
async def test_state_update_gender_skip(tester: AppTester, rapidpro_mock):
    tester.setup_state("state_update_gender")

    await tester.user_input("Skip")

    tester.assert_answer("state_update_gender", "skip")
    tester.setup_state("state_display_preferences")

    assert [r.path for r in rapidpro_mock.tstate.requests] == ["/api/v2/contacts.json"]


@pytest.mark.asyncio
async def test_state_update_gender_rather_not_say(tester: AppTester, rapidpro_mock):
    tester.setup_state("state_update_gender")

    await tester.user_input("Rather Not Say")

    tester.assert_answer("state_update_gender", "rather_not_say")
    tester.setup_state("state_update_gender_confirm")


@pytest.mark.asyncio
async def test_state_update_other_gender(tester: AppTester, rapidpro_mock):
    tester.setup_state("state_update_gender")

    await tester.user_input("4")

    tester.assert_state("state_update_other_gender")
    tester.assert_num_messages(1)

    tester.assert_answer("state_update_gender", "other")

    assert [r.method for r in rapidpro_mock.tstate.requests] == ["GET"]


@pytest.mark.asyncio
async def test_state_update_gender_confirm(tester: AppTester, rapidpro_mock):
    tester.setup_answer("state_update_gender", "other")
    tester.setup_state("state_update_other_gender")

    await tester.user_input("trans man")

    tester.assert_state("state_update_gender_confirm")
    tester.assert_num_messages(1)

    tester.assert_answer("state_update_other_gender", "trans man")

    assert [r.method for r in rapidpro_mock.tstate.requests] == ["GET"]


@pytest.mark.asyncio
async def test_state_update_gender_confirm_not_correct(
    tester: AppTester, rapidpro_mock
):
    tester.setup_answer("state_update_gender", "male")
    tester.setup_state("state_update_gender_confirm")

    await tester.user_input("no")

    tester.assert_state("state_update_gender")
    tester.assert_num_messages(1)

    assert [r.method for r in rapidpro_mock.tstate.requests] == ["GET"]


@pytest.mark.asyncio
async def test_state_update_gender_submit(tester: AppTester, rapidpro_mock):
    tester.setup_answer("state_update_gender", "other")
    tester.setup_answer("state_other_gender", "gender fluid")
    tester.setup_state("state_update_gender_confirm")
    await tester.user_input("1")
    tester.assert_num_messages(1)
    tester.assert_state("state_conclude_changes")

    assert rapidpro_mock.tstate.requests[-1].path == "/api/v2/contacts.json"


@pytest.mark.asyncio
async def test_state_update_age(tester: AppTester, rapidpro_mock):
    tester.setup_state("state_display_preferences")
    await tester.user_input("age")
    tester.assert_num_messages(1)
    tester.assert_state("state_update_age")

    tester.assert_message(
        "\n".join(
            [
                "*CHAT SETTINGS / ⚙️ Change or update your info* / *Age*",
                "-----",
                "",
                "*What is your age?*",
                "_Type in the number only (e.g. 24)_",
                "",
                "*-----*",
                "Rather not say?",
                "No stress! Just tap SKIP",
            ]
        )
    )

    assert [r.path for r in rapidpro_mock.tstate.requests] == ["/api/v2/contacts.json"]


@pytest.mark.asyncio
async def test_state_update_age_confirm(tester: AppTester, rapidpro_mock):
    tester.setup_state("state_update_age")
    await tester.user_input("32")
    tester.assert_num_messages(1)
    tester.assert_state("state_update_age_confirm")

    assert [r.method for r in rapidpro_mock.tstate.requests] == ["GET"]


@pytest.mark.asyncio
async def test_state_update_age_confirm_not_correct(tester: AppTester, rapidpro_mock):
    tester.setup_answer("state_update_age", "32")
    tester.setup_state("state_update_age_confirm")
    await tester.user_input("no")
    tester.assert_num_messages(1)
    tester.assert_state("state_update_age")

    assert [r.method for r in rapidpro_mock.tstate.requests] == ["GET"]


@pytest.mark.asyncio
async def test_state_update_age_submit(tester: AppTester, rapidpro_mock):
    tester.setup_answer("state_update_age", "32")
    tester.setup_state("state_update_age_confirm")
    await tester.user_input("1")
    tester.assert_num_messages(1)
    tester.assert_state("state_conclude_changes")

    assert rapidpro_mock.tstate.requests[-1].path == "/api/v2/contacts.json"


@pytest.mark.asyncio
async def test_state_update_relationship_status(tester: AppTester, rapidpro_mock):
    tester.setup_state("state_display_preferences")
    await tester.user_input("4")
    tester.assert_num_messages(1)
    tester.assert_state("state_update_relationship_status")

    tester.assert_message(
        "\n".join(
            [
                "*CHAT SETTINGS / ⚙️ Change or update your info* / *Relationship?*",
                "-----",
                "",
                "🦸 *Are you currently in a relationship or seeing "
                "someone special right now?",
                "",
                "1. Yes, in relationship",
                "2. It's complicated",
                "3. Not seeing anyone",
                "4. Skip",
            ]
        )
    )

    assert [r.path for r in rapidpro_mock.tstate.requests] == ["/api/v2/contacts.json"]


@pytest.mark.asyncio
async def test_state_update_relationship_status_confirm(
    tester: AppTester, rapidpro_mock
):
    tester.setup_state("state_update_relationship_status")
    await tester.user_input("it's complicated")
    tester.assert_num_messages(1)
    tester.assert_state("state_update_relationship_status_confirm")

    assert [r.method for r in rapidpro_mock.tstate.requests] == ["GET"]


@pytest.mark.asyncio
async def test_state_update_relationship_status_confirm_not_correct(
    tester: AppTester, rapidpro_mock
):
    tester.setup_answer("state_update_relationship_status", "yes")
    tester.setup_state("state_update_relationship_status_confirm")
    await tester.user_input("no")
    tester.assert_num_messages(1)
    tester.assert_state("state_update_relationship_status")

    assert [r.method for r in rapidpro_mock.tstate.requests] == ["GET"]


@pytest.mark.asyncio
async def test_state_update_relationship_status_submit(
    tester: AppTester, rapidpro_mock
):
    tester.setup_answer("state_update_relationship_status", "yes")
    tester.setup_state("state_update_relationship_status_confirm")
    await tester.user_input("1")
    tester.assert_num_messages(1)
    tester.assert_state("state_conclude_changes")

    assert [r.method for r in rapidpro_mock.tstate.requests] == ["GET", "POST"]


@pytest.mark.asyncio
async def test_state_update_bot_name(tester: AppTester, rapidpro_mock):
    tester.user.metadata["persona_emoji"] = "🦸"
    tester.user.metadata["persona_name"] = "Caped Crusader"
    tester.setup_state("state_display_preferences")
    await tester.user_input("3")
    tester.assert_num_messages(1)
    tester.assert_state("state_update_bot_name")

    tester.assert_message(
        "\n".join(
            [
                "🦸 PERSONALISE YOUR B-WISE BOT / *Give me a name*",
                "-----",
                "",
                "*What would you like to call me?*",
                "It can be any name you like or one that reminds you of someone you "
                "trust.",
                "",
                "Just type and send me your new bot name.",
                "",
                '_If you want to do this later, just click the "skip" button._',
            ]
        )
    )

    assert [r.path for r in rapidpro_mock.tstate.requests] == ["/api/v2/contacts.json"]


@pytest.mark.asyncio
async def test_state_update_bot_name_submit(tester: AppTester, rapidpro_mock):
    tester.user.metadata["persona_emoji"] = "🦸"
    tester.user.metadata["persona_name"] = "Caped Crusader"
    tester.setup_state("state_update_bot_name")
    await tester.user_input("johnny")

    [msg] = tester.fake_worker.outbound_messages
    assert msg.content == "\n".join(
        [
            "Great - from now on you can call me johnny.",
            "",
            "_You can change this later from the main *MENU*._",
        ]
    )
    tester.assert_num_messages(1)
    tester.assert_message(
        "\n".join(
            [
                "🦸 PERSONALISE YOUR B-WISE BOT / *Choose an emoji*",
                "*-----*",
                "",
                "*Why not use an emoji to accompany my new name?*",
                "Send in the new emoji you'd like to use now.",
                "",
                '_If you want to do this later, just click the "skip" button._',
            ]
        )
    )

    tester.assert_state("state_update_bot_emoji")
    tester.assert_metadata("persona_name", "johnny")

    assert [r.method for r in rapidpro_mock.tstate.requests] == ["GET", "POST"]


@pytest.mark.asyncio
async def test_state_update_bot_name_skip(tester: AppTester, rapidpro_mock):
    tester.user.metadata["persona_emoji"] = "🦸"
    tester.user.metadata["persona_name"] = "Caped Crusader"
    tester.setup_state("state_update_bot_name")
    await tester.user_input("skip")

    assert len(tester.fake_worker.outbound_messages) == 0

    tester.assert_num_messages(1)
    tester.assert_message(
        "\n".join(
            [
                "🦸 PERSONALISE YOUR B-WISE BOT / *Choose an emoji*",
                "*-----*",
                "",
                "*Why not use an emoji to accompany my new name?*",
                "Send in the new emoji you'd like to use now.",
                "",
                '_If you want to do this later, just click the "skip" button._',
            ]
        )
    )

    tester.assert_state("state_update_bot_emoji")
    tester.assert_metadata("persona_name", "Caped Crusader")

    assert [r.method for r in rapidpro_mock.tstate.requests] == ["GET"]


@pytest.mark.asyncio
async def test_state_update_bot_emoji_submit(tester: AppTester, rapidpro_mock):
    tester.user.metadata["persona_emoji"] = "🦸"
    tester.user.metadata["persona_name"] = "Caped Crusader"
    tester.setup_state("state_update_bot_emoji")
    await tester.user_input("🙋🏿‍♂️")

    tester.assert_num_messages(1)
    tester.assert_message(
        "\n".join(
            [
                "🙋🏿‍♂️ PERSONALISE YOUR B-WISE BOT / *Choose an emoji*",
                "*-----*",
                "",
                "Wonderful! 🙋🏿‍♂️",
                "",
                "*What would you like to do now?*",
                "",
                "1. Go to the menu",
                "2. Ask a question",
            ]
        )
    )

    tester.assert_state("state_update_bot_emoji_submit")
    tester.assert_metadata("persona_emoji", "🙋🏿‍♂️")

    assert [r.method for r in rapidpro_mock.tstate.requests] == ["GET", "POST"]


@pytest.mark.asyncio
async def test_state_update_bot_emoji_skip(tester: AppTester, rapidpro_mock):
    tester.user.metadata["persona_emoji"] = "🦸"
    tester.user.metadata["persona_name"] = "Caped Crusader"
    tester.setup_state("state_update_bot_emoji")
    await tester.user_input("skip")

    tester.assert_state("state_display_preferences")
    tester.assert_metadata("persona_emoji", "🦸")

    assert [r.method for r in rapidpro_mock.tstate.requests] == ["GET"]


@pytest.mark.asyncio
async def test_state_update_location_confirm(tester: AppTester, google_api_mock):
    tester.setup_state("state_update_location")

    await tester.user_input(
        "test location",
        transport_metadata={
            "message": {"location": {"longitude": 12.34, "latitude": 56.78}}
        },
    )
    tester.assert_state("state_update_location_confirm")

    tester.assert_metadata("new_latitude", 56.78)
    tester.assert_metadata("new_longitude", 12.34)
    tester.assert_metadata("place_id", "ChIJd8BlQ2BZwokRAFUEcm_qrcA")
    tester.assert_metadata(
        "new_location_description", "277 Bedford Avenue, Brooklyn, NY 11211, USA"
    )

    assert [r.path for r in google_api_mock.tstate.requests] == [
        "/maps/api/geocode/json"
    ]

    tester.assert_num_messages(1)
    tester.assert_message(
        "\n".join(
            [
                "*CHAT SETTINGS / ⚙️ Change or update your info* / *Location?*",
                "-----",
                "",
                "*You've entered 277 Bedford Avenue, Brooklyn, NY 11211, USA as your "
                "location.*",
                "",
                "Is this correct?",
                "",
                "1. Yes",
                "2. No",
            ]
        )
    )


@pytest.mark.asyncio
async def test_state_update_location_skip(
    tester: AppTester, google_api_mock, rapidpro_mock
):
    tester.setup_state("state_update_location")

    await tester.user_input("Skip")
    tester.assert_state("state_display_preferences")

    assert [r.path for r in google_api_mock.tstate.requests] == []


@pytest.mark.asyncio
async def test_state_update_location_confirm_incorrect(
    tester: AppTester, google_api_mock, rapidpro_mock
):
    tester.user.metadata["latitude"] = 56.78
    tester.user.metadata["longitude"] = 12.34
    tester.user.metadata["location_description"] = "277 Bedford Avenue, Brooklyn, NY"
    tester.setup_state("state_update_location_confirm")

    await tester.user_input("no")
    tester.assert_state("state_update_location")


@pytest.mark.asyncio
async def test_state_update_location_submit(tester: AppTester, rapidpro_mock):
    tester.user.metadata["new_latitude"] = 56.78
    tester.user.metadata["new_longitude"] = 12.34
    tester.user.metadata[
        "new_location_description"
    ] = "277 Bedford Avenue, Brooklyn, NY"
    tester.setup_state("state_update_location_confirm")

    await tester.user_input("yes")

    tester.assert_num_messages(1)
    tester.assert_state("state_conclude_changes")

    assert len(rapidpro_mock.tstate.requests) == 2
    request = rapidpro_mock.tstate.requests[1]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {
            "latitude": 56.78,
            "longitude": 12.34,
            "location_description": "277 Bedford Avenue, Brooklyn, NY",
        },
    }
