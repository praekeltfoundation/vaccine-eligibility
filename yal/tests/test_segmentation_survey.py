import pytest
from sanic import Sanic, response

from vaccine.models import Message
from vaccine.testing import AppTester, TState, run_sanic
from yal import config
from yal.segmentation_survey import Application


@pytest.fixture
def tester():
    tester = AppTester(Application)

    async def publish_message(content):
        await tester.fake_worker.publish_message(
            tester.application.inbound.reply(content)
        )

    tester.application.publish_message = publish_message
    return tester


@pytest.fixture(autouse=True)
async def rapidpro_mock():
    Sanic.test_mode = True
    app = Sanic("mock_rapidpro")
    tstate = TState()

    @app.route("/api/v2/contacts.json", methods=["GET"])
    def get_contact(request):
        tstate.requests.append(request)
        return response.json(
            {
                "results": [{"fields": tstate.contact_fields}],
                "next": None,
            },
            status=200,
        )

    @app.route("/api/v2/contacts.json", methods=["POST"])
    def update_contact(request):
        tstate.requests.append(request)
        tstate.contact_fields.update(request.json["fields"])
        return response.json({}, status=200)

    @app.route("/api/v2/flow_starts.json", methods=["POST"])
    def start_flow(request):
        tstate.requests.append(request)
        return response.json({}, status=200)

    async with run_sanic(app) as server:
        url = config.RAPIDPRO_URL
        config.SEGMENT_AIRTIME_FLOW_UUID = "segment-airtime-flow-uuid"
        config.RAPIDPRO_URL = f"http://{server.host}:{server.port}"
        config.RAPIDPRO_TOKEN = "testtoken"
        server.tstate = tstate
        yield server
        config.RAPIDPRO_URL = url


@pytest.mark.asyncio
async def test_survey_start(tester: AppTester, rapidpro_mock):
    tester.setup_state("state_start_survey")
    await tester.user_input("OK, let's start!", session=Message.SESSION_EVENT.NEW)

    [msg] = tester.fake_worker.outbound_messages
    assert msg.content == "\n".join(
        [
            "*You and your sexual health*",
            "-----",
            "",
            "🤦🏾‍♂️I've got a ton of answers and info about sex, "
            "love and relationships.",
            "",
            "To point you in the right direction, "
            "I want to quickly check what you already know.",
        ]
    )

    tester.assert_message(
        "\n".join(
            [
                "I'll ask a few questions. For each question "
                "I just need you to choose the answer that feels right to you."
            ]
        )
    )

    assert (
        rapidpro_mock.tstate.contact_fields["segment_survey_complete"] == "inprogress"
    )


@pytest.mark.asyncio
async def test_survey_next_question(tester: AppTester):
    tester.setup_state("state_survey_question")
    await tester.user_input("2")
    tester.assert_state("state_survey_question")
    tester.assert_message(
        "\n".join(
            [
                "✅◼️◽️◽️◽️◽️◽️◽️◽️",
                "-----",
                "",
                "*If Teddy goes out to a restaurant and starts chatting "
                "with someone he is sexually attracted to, what is most "
                "appropriate way Teddy can tell that person wants to "
                "have sex with him?*",
                "",
                "[persona_emoji] _Reply with the *number* " "of your chosen answer:_",
                "",
                "*1*. By the way they are looking at him",
                "*2*. By what they are wearing",
                "*3*. If they carry condoms",
                "*4*. If Teddy has had sex with them before",
                "*5*. If they verbally consent to have sex",
                "*6*. I don't know",
            ]
        )
    )
    tester.assert_answer("state_s1_1_sex_health_lit_sti", "2")
