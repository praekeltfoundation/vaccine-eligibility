import pytest
from sanic import Sanic, response

from vaccine.models import Message
from vaccine.testing import AppTester
from yal import turn
from yal.change_preferences import Application


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
    def get_profile(request, msisdn):
        app.requests.append(request)
        if app.errormax:
            if app.errors < app.errormax:
                app.errors += 1
                return response.json({}, status=500)
        return response.json(
            {
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
                }
            }
        )

    @app.route("/v1/contacts/<msisdn:int>/profile", methods=["PATCH"])
    def update_profile(request, msisdn):
        app.requests.append(request)
        if app.errormax:
            if app.errors < app.errormax:
                app.errors += 1
                return response.json({}, status=500)
        return response.json({})

    client = await sanic_client(app)
    get_profile_url = turn.get_profile_url

    host = f"http://{client.host}:{client.port}"
    turn.get_profile_url = (
        lambda whatsapp_id: f"{host}/v1/contacts/{whatsapp_id}/profile"
    )

    yield client
    turn.get_profile_url = get_profile_url


@pytest.mark.asyncio
async def test_state_display_preferences(tester: AppTester, turn_api_mock):
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

    assert [r.path for r in turn_api_mock.app.requests] == [
        "/v1/contacts/27820001001/profile"
    ]


@pytest.mark.asyncio
async def test_state_update_relationship_status(tester: AppTester, turn_api_mock):
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


@pytest.mark.asyncio
async def test_state_update_relationship_status_submit(
    tester: AppTester, turn_api_mock
):
    tester.setup_state("state_update_relationship_status")
    await tester.user_input("2")
    tester.assert_num_messages(1)
    tester.assert_state("state_change_info_prompt")
