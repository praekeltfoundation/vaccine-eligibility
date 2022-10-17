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
            "province": "FS",
            "suburb": "TestSuburb",
            "street_name": "test street",
            "street_number": "12",
            "persona_emoji": "🦸",
            "persona_name": "Caped Crusader",
        },
        "blocked": False,
        "stopped": False,
        "created_on": "2015-11-11T08:30:24.922024+00:00",
        "modified_on": "2015-11-11T08:30:25.525936+00:00",
        "urns": [urn],
    }


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
                "12 test street TestSuburb Free State",
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
    await tester.user_input("2")
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
            ]
        ),
        list_items=["Female", "Male", "Non-binary", "None of these", "Rather not say"],
    )

    assert [r.path for r in rapidpro_mock.tstate.requests] == ["/api/v2/contacts.json"]


@pytest.mark.asyncio
async def test_state_update_gender_from_list(tester: AppTester, rapidpro_mock):
    tester.setup_state("state_update_gender")

    await tester.user_input("2")

    tester.assert_state("state_update_gender_confirm")
    tester.assert_num_messages(1)

    tester.assert_answer("state_update_gender", "male")

    assert [r.path for r in rapidpro_mock.tstate.requests] == []


@pytest.mark.asyncio
async def test_state_update_other_gender(tester: AppTester, rapidpro_mock):
    tester.setup_state("state_update_gender")

    await tester.user_input("4")

    tester.assert_state("state_update_other_gender")
    tester.assert_num_messages(1)

    tester.assert_answer("state_update_gender", "other")

    assert [r.path for r in rapidpro_mock.tstate.requests] == []


@pytest.mark.asyncio
async def test_state_update_gender_confirm(tester: AppTester, rapidpro_mock):
    tester.setup_answer("state_update_gender", "other")
    tester.setup_state("state_update_other_gender")

    await tester.user_input("trans man")

    tester.assert_state("state_update_gender_confirm")
    tester.assert_num_messages(1)

    tester.assert_answer("state_update_other_gender", "trans man")

    assert [r.path for r in rapidpro_mock.tstate.requests] == []


@pytest.mark.asyncio
async def test_state_update_gender_confirm_not_correct(
    tester: AppTester, rapidpro_mock
):
    tester.setup_state("state_update_gender_confirm")

    await tester.user_input("2")

    tester.assert_state("state_update_gender")
    tester.assert_num_messages(1)

    assert [r.path for r in rapidpro_mock.tstate.requests] == []


@pytest.mark.asyncio
async def test_state_update_gender_submit(tester: AppTester, rapidpro_mock):
    tester.setup_answer("state_update_gender", "other")
    tester.setup_answer("state_other_gender", "gender fluid")
    tester.setup_state("state_update_gender_confirm")
    await tester.user_input("1")
    tester.assert_num_messages(1)
    tester.assert_state("state_conclude_changes")

    assert [r.path for r in rapidpro_mock.tstate.requests] == [
        "/api/v2/contacts.json",
    ]


@pytest.mark.asyncio
async def test_state_update_age(tester: AppTester, rapidpro_mock):
    tester.setup_state("state_display_preferences")
    await tester.user_input("1")
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

    assert [r.path for r in rapidpro_mock.tstate.requests] == []


@pytest.mark.asyncio
async def test_state_update_age_confirm_not_correct(tester: AppTester, rapidpro_mock):
    tester.setup_answer("state_update_age", "32")
    tester.setup_state("state_update_age_confirm")
    await tester.user_input("2")
    tester.assert_num_messages(1)
    tester.assert_state("state_update_age")

    assert [r.path for r in rapidpro_mock.tstate.requests] == []


@pytest.mark.asyncio
async def test_state_update_age_submit(tester: AppTester, rapidpro_mock):
    tester.setup_answer("state_update_age", "32")
    tester.setup_state("state_update_age_confirm")
    await tester.user_input("1")
    tester.assert_num_messages(1)
    tester.assert_state("state_conclude_changes")

    assert [r.path for r in rapidpro_mock.tstate.requests] == [
        "/api/v2/contacts.json",
    ]


@pytest.mark.asyncio
async def test_state_update_relationship_status(tester: AppTester, rapidpro_mock):
    tester.setup_state("state_display_preferences")
    await tester.user_input("4")
    tester.assert_num_messages(1)
    tester.assert_state("state_update_relationship_status")

    tester.assert_message(
        "\n".join(
            [
                "*CHAT SETTINGS*",
                "⚙️ Change or update your info",
                "-----",
                "",
                "*And what about love? Seeing someone special right now?*",
                "",
                "*1*. Yes",
                "*2*. It's complicated",
                "*3*. No",
                "*4*. Skip",
            ]
        )
    )

    assert [r.path for r in rapidpro_mock.tstate.requests] == ["/api/v2/contacts.json"]


@pytest.mark.asyncio
async def test_state_update_relationship_status_submit(
    tester: AppTester, rapidpro_mock
):
    tester.setup_state("state_update_relationship_status")
    await tester.user_input("2")
    tester.assert_num_messages(1)
    tester.assert_state("state_display_preferences")

    assert [r.path for r in rapidpro_mock.tstate.requests] == [
        "/api/v2/contacts.json",
        "/api/v2/contacts.json",
    ]


@pytest.mark.asyncio
async def test_state_update_location_submit(tester: AppTester, rapidpro_mock):
    tester.setup_state("state_update_location_submit")

    tester.setup_answer("state_update_province", "FS")
    tester.setup_answer("state_update_suburb", "SomeSuburb")
    tester.setup_answer("state_update_street_name", "Good street")
    tester.setup_answer("state_update_street_number", "12")

    await tester.user_input(session=Message.SESSION_EVENT.NEW)

    tester.assert_metadata("province", "FS")
    tester.assert_metadata("suburb", "SomeSuburb")
    tester.assert_metadata("street_name", "Good street")
    tester.assert_metadata("street_number", "12")

    tester.assert_num_messages(1)
    tester.assert_state("state_display_preferences")

    assert [r.path for r in rapidpro_mock.tstate.requests] == [
        "/api/v2/contacts.json",
        "/api/v2/contacts.json",
    ]


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
            "_You can change this later by typing in *9* from the main *MENU*._",
        ]
    )
    tester.assert_num_messages(1)
    tester.assert_message(
        "\n".join(
            [
                "🦸 PERSONALISE YOUR B-WISE BOT / *Choose an emoji*",
                "-----",
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

    assert [r.path for r in rapidpro_mock.tstate.requests] == [
        "/api/v2/contacts.json",
    ]


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
                "-----",
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

    assert [r.path for r in rapidpro_mock.tstate.requests] == []


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
                "-----",
                "",
                "Wonderful! 🙋🏿‍♂️",
                "",
                "*What would you like to do now?*",
                "",
                "1. Main Menu",
                "2. Ask a question",
            ]
        )
    )

    tester.assert_state("state_update_bot_emoji_submit")
    tester.assert_metadata("persona_emoji", "🙋🏿‍♂️")

    assert [r.path for r in rapidpro_mock.tstate.requests] == [
        "/api/v2/contacts.json",
    ]


@pytest.mark.asyncio
async def test_state_update_bot_emoji_skip(tester: AppTester, rapidpro_mock):
    tester.user.metadata["persona_emoji"] = "🦸"
    tester.user.metadata["persona_name"] = "Caped Crusader"
    tester.setup_state("state_update_bot_emoji")
    await tester.user_input("skip")

    tester.assert_state("state_display_preferences")
    tester.assert_metadata("persona_emoji", "🦸")

    assert [r.path for r in rapidpro_mock.tstate.requests] == [
        "/api/v2/contacts.json",
    ]
