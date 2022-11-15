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
        "fields": {
            "segment_survey_sent": "True" if urn == "27820001001" else "False",
        },
    }


@pytest.fixture
async def rapidpro_mock():
    Sanic.test_mode = True
    app = Sanic("mock_rapidpro")
    tstate = TState()

    @app.route("/api/v2/contacts.json", methods=["GET"])
    def get_contact(request):
        tstate.requests.append(request)
        urn = request.args.get("urn").split(":")[1]
        contacts = [get_rapidpro_contact(urn)]
        return response.json(
            {
                "results": contacts,
                "next": None,
            },
            status=200,
        )

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
    await tester.user_input("Hell Yeah!")
    tester.assert_state("state_survey_question")

    [msg] = tester.fake_worker.outbound_messages
    assert msg.content == "\n".join(
        [
            "*Awesome, let's get straight into it.*",
            "",
            "There are 4 sections to the survey. Each section should take around *5-10 "
            "min* to complete.",
            "",
            "-----",
            "*Or reply:*",
            "0. 🏠 Back to Main *MENU*",
        ]
    )

    tester.assert_message(
        "\n".join(
            [
                "*BWise / Survey*",
                "-----",
                "Section 1",
                "1/4",
                "",
                "*How much does everyone in your house make altogether, before paying "
                "for regular monthly items?*",
                "",
                "1. No income",
                "2. R1 - R400",
                "3. R401 - R800",
                "4. R801 - R1 600",
                "5. R1 601 - R3 200",
                "6. R3 201 - R6 400",
                "7. R6 401 - R12 800",
                "8. R12 801 - R25 600",
                "9. R25 601 - R51 200",
                "10. R51 201 - R102 400",
                "11. R102 401 - R204 800",
                "12. R204 801 or more",
                "",
                "-----",
                "*Or reply:*",
                "0. 🏠 Back to Main *MENU*",
                "#. 🆘Get *HELP*",
            ]
        )
    )


@pytest.mark.asyncio
async def test_survey_start_not_invited(tester: AppTester, rapidpro_mock):
    tester.setup_user_address("27820002002")
    await tester.user_input("Hell Yeah!")
    tester.assert_state("state_start")


@pytest.mark.asyncio
async def test_survey_start_decline(tester: AppTester, rapidpro_mock):
    await tester.user_input("No, rather not")
    tester.assert_state("state_survey_decline")

    tester.assert_message(
        "\n".join(
            [
                "*No problem and no pressure!* 😎",
                "",
                "What would you like to do next?",
                "",
                "1. Ask a question",
                "2. Go to Main Menu",
                "-----",
                "*Or reply:*",
                "0. 🏠 Back to Main *MENU*",
            ]
        )
    )


@pytest.mark.asyncio
async def test_survey_next_question(tester: AppTester):
    tester.setup_state("state_survey_question")
    await tester.user_input("2")
    tester.assert_state("state_survey_question")
    tester.assert_message(
        "\n".join(
            [
                "*BWise / Survey*",
                "-----",
                "Section 1",
                "2/4",
                "",
                "*What is your present relationship status?*",
                "",
                "1. Not currently dating",
                "2. In a serious relationship",
                "3. In a relationship, but not a serious one",
                "",
                "-----",
                "*Or reply:*",
                "0. 🏠 Back to Main *MENU*",
                "#. 🆘Get *HELP*",
            ]
        )
    )
    tester.assert_answer("state_s1_4_income", "R1-R400")


@pytest.mark.asyncio
async def test_survey_next_question_branch(tester: AppTester):
    tester.user.metadata["segment_question"] = "state_s1_6_monthly_sex_partners"
    tester.setup_state("state_survey_question")
    await tester.user_input("3")
    tester.assert_state("state_survey_question")
    tester.assert_message(
        "\n".join(
            [
                "*BWise / Survey*",
                "-----",
                "Section 1",
                "2/4",
                "",
                "**Ok. You can tell me how many sexual partners you had here.*",
                "",
                "_Just type and send_*",
                "",
                "-----",
                "*Or reply:*",
                "0. 🏠 Back to Main *MENU*",
                "#. 🆘Get *HELP*",
            ]
        )
    )


@pytest.mark.asyncio
async def test_survey_freetext_question(tester: AppTester):
    tester.user.metadata["segment_section"] = 1
    tester.user.metadata["segment_question"] = "state_s1_6_detail_monthly_sex_partners"

    tester.setup_state("state_survey_question")
    await tester.user_input(session=Message.SESSION_EVENT.NEW)

    tester.assert_message(
        "\n".join(
            [
                "*BWise / Survey*",
                "-----",
                "Section 1",
                "1/4",
                "",
                "**Ok. You can tell me how many sexual partners you had here.*",
                "",
                "_Just type and send_*",
                "",
                "-----",
                "*Or reply:*",
                "0. 🏠 Back to Main *MENU*",
                "#. 🆘Get *HELP*",
            ]
        )
    )

    await tester.user_input("11")

    tester.assert_state("state_survey_question")

    tester.assert_answer("state_s1_6_detail_monthly_sex_partners", "11")


@pytest.mark.asyncio
async def test_survey_next_section(tester: AppTester):
    tester.user.metadata["segment_section"] = 2
    tester.user.metadata["segment_question"] = "state_s2_2_knowledge_2"

    tester.setup_state("state_survey_question")
    await tester.user_input("1")
    tester.assert_state("state_survey_question")

    tester.assert_message(
        "\n".join(
            [
                "*BWise / Survey*",
                "-----",
                "Section 3",
                "1/2",
                "",
                "*_The following statements may apply more or less to you. To what "
                "extent do you think each statement applies to you personally?_ ",
                "",
                "*I’m my own boss.**",
                "",
                "1. Does not apply at all",
                "2. Applies somewhat",
                "3. Applies",
                "4. Applies a lot",
                "5. Applies completely",
                "",
                "-----",
                "*Or reply:*",
                "0. 🏠 Back to Main *MENU*",
                "#. 🆘Get *HELP*",
            ]
        )
    )

    [msg] = tester.fake_worker.outbound_messages
    assert msg.content == "\n".join(
        [
            "*BWise / Survey*",
            "-----",
            "",
            "😎 *CONGRATS. YOU'RE HALFWAY THERE!*",
            "",
            "Section 2 complete, keep going. *Let's move onto section 3!* 👍🏾",
            "",
            "-----",
            "*Or reply:*",
            "0. 🏠 Back to Main *MENU*",
            "#. 🆘Get *HELP*",
        ]
    )


@pytest.mark.asyncio
async def test_survey_end(tester: AppTester):
    tester.user.metadata["segment_section"] = 3
    tester.user.metadata["segment_question"] = "state_s3_2_loc_2_work"

    tester.setup_state("state_survey_question")
    await tester.user_input("1")
    tester.assert_state("state_survey_done")

    # Make sure metadata was cleaned up and survey can be repeated
    tester.setup_state("state_start_survey")
    await tester.user_input("1")
    tester.assert_state("state_survey_question")


@pytest.mark.asyncio
async def test_state_survey_done(tester: AppTester, rapidpro_mock):
    tester.setup_state("state_survey_done")
    await tester.user_input("Get Airtime")
    tester.assert_state("state_prompt_next_action")

    assert len(rapidpro_mock.tstate.requests) == 1
    request = rapidpro_mock.tstate.requests[0]
    assert json.loads(request.body.decode("utf-8")) == {
        "flow": "segment-airtime-flow-uuid",
        "urns": ["whatsapp:27820001001"],
    }
