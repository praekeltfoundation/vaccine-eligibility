import pytest
from sanic import Sanic, response

from vaccine.models import Message
from vaccine.testing import AppTester
from yal import config
from yal.change_preferences import Application


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
            "relationship_status": "single",
            "gender": "male",
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
async def test_state_display_preferences(tester: AppTester, rapidpro_mock):
    tester.setup_state("state_display_preferences")
    await tester.user_input(session=Message.SESSION_EVENT.NEW)
    tester.assert_num_messages(1)

    [msg] = tester.fake_worker.outbound_messages
    assert msg.content == "\n".join(
        [
            "*CHAT SETTINGS*",
            "⚙️ Change or update your info",
            "-----",
            "*👩🏾 No problem. Here's the info you've saved:*",
            "",
            "☑️ 🎂 *Birthday*",
            "22/2/2022",
            "",
            "☑️ 💟 *In a Relationship?*",
            "single",
            "",
            "☑️ 📍 *Location*",
            "12 test street TestSuburb Free State",
            "",
            "☑️ 🌈  *Identity*",
            "male",
        ]
    )

    tester.assert_message(
        "\n".join(
            [
                "👩🏾 *What info would you like to change?*",
                "",
                "1. Birthday",
                "2. Relationship Status",
                "3. Location",
                "4. Identity",
                "-----",
                "*Or reply:*",
                "*0* - 🏠 Back to *Main MENU*",
                "*#* - 🆘 Get *HELP*",
            ]
        )
    )

    assert [r.path for r in rapidpro_mock.app.requests] == ["/api/v2/contacts.json"]


@pytest.mark.asyncio
async def test_state_update_relationship_status(tester: AppTester, rapidpro_mock):
    tester.setup_state("state_display_preferences")
    await tester.user_input("2")
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

    assert [r.path for r in rapidpro_mock.app.requests] == ["/api/v2/contacts.json"]


@pytest.mark.asyncio
async def test_state_update_relationship_status_submit(
    tester: AppTester, rapidpro_mock
):
    tester.setup_state("state_update_relationship_status")
    await tester.user_input("2")
    tester.assert_num_messages(1)
    tester.assert_state("state_change_info_prompt")

    assert [r.path for r in rapidpro_mock.app.requests] == [
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
    tester.assert_state("state_change_info_prompt")

    assert [r.path for r in rapidpro_mock.app.requests] == [
        "/api/v2/contacts.json",
        "/api/v2/contacts.json",
    ]
