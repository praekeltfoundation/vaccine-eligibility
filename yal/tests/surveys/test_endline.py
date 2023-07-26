from datetime import datetime
from unittest import mock

import pytest
from sanic import Sanic, response

from vaccine.models import Message, StateData, User
from vaccine.testing import AppTester, TState, run_sanic
from yal import config
from yal.main import Application
from yal.utils import GENERIC_ERRORS, replace_persona_fields


@pytest.fixture
def tester():
    return AppTester(Application)


def get_generic_errors():
    errors = []
    for error in GENERIC_ERRORS:
        errors.append(replace_persona_fields(error))
    return errors


def get_rapidpro_contact(urn):
    return {
        "fields": {
            "emergency_contact": "" if ("27820001001" in urn) else "+27831231234",
        },
    }


@pytest.fixture(autouse=True)
async def rapidpro_mock():
    Sanic.test_mode = True
    app = Sanic("mock_rapidpro")
    tstate = TState()

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

    @app.route("/api/v2/contacts.json", methods=["POST"])
    def update_contact(request):
        tstate.requests.append(request)
        if tstate.errormax:
            if tstate.errors < tstate.errormax:
                tstate.errors += 1
                return response.json({}, status=500)
        return response.json({}, status=200)

    async with run_sanic(app) as server:
        url = config.RAPIDPRO_URL
        config.RAPIDPRO_URL = f"http://{server.host}:{server.port}"
        config.RAPIDPRO_TOKEN = "testtoken"
        server.tstate = tstate
        yield server
        config.RAPIDPRO_URL = url


@pytest.mark.asyncio
async def test_endline_invitation_i_want_to_answer(tester: AppTester, rapidpro_mock):

    user = User(
        addr="278201234567",
        state=StateData(),
        session_id=1,
        metadata={"baseline_survey_completed": True},
    )
    app = Application(user)
    msg = Message(
        content="Yes, I want to answer",
        to_addr="27820001002",
        from_addr="27820001003",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )

    [reply] = await app.process_message(msg)

    assert user.state.name == "state_start_terms"

@pytest.mark.asyncio
async def test_endline_invitation_remind_me_tomorrow(
    tester: AppTester, rapidpro_mock,
):
    user = User(
        addr="278201234567",
        state=StateData(),
        session_id=1,
        metadata={"baseline_survey_completed": True},
    )
    app = Application(user)
    msg = Message(
        content="Remind me tomorrow",
        to_addr="27820001002",
        from_addr="27820001003",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )

    [reply] = await app.process_message(msg)

    assert user.state.name == "state_handle_assessment_reminder_response"

@pytest.mark.asyncio
async def test_endline_invitation_not_interested(
    tester: AppTester, rapidpro_mock,
):
    user = User(
        addr="278201234567",
        state=StateData(),
        session_id=1,
        metadata={"baseline_survey_completed": True},
    )
    app = Application(user)
    msg = Message(
        content="I'm not interested",
        to_addr="27820001002",
        from_addr="27820001003",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )

    [reply] = await app.process_message(msg)

    assert user.state.name == "state_no_consent"


@pytest.mark.asyncio
async def test_endline_invitation_answer(tester: AppTester, rapidpro_mock):

    user = User(
        addr="278201234567",
        state=StateData(),
        session_id=1,
        metadata={"baseline_survey_completed": True},
    )
    app = Application(user)
    msg = Message(
        content="answer",
        to_addr="27820001002",
        from_addr="27820001003",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )

    [reply] = await app.process_message(msg)

    assert user.state.name == "state_start_terms"


@pytest.mark.asyncio
async def test_state_platform_review_endline(tester: AppTester, rapidpro_mock):
    await tester.user_input(
        "test",
        transport_metadata={
            "message": {"button": {"payload": "state_alcohol_assessment_endline_end"}}
        },
    )

    tester.assert_state("state_survey_question")
    tester.assert_metadata("assessment_name", "platform_review_endline")
    tester.assert_metadata("assessment_end_state", "state_submit_endline_completed")


@pytest.mark.asyncio
@mock.patch("yal.surveys.endline.get_current_datetime")
async def test_state_submit_endline_completed(
    get_current_datetime, tester: AppTester, rapidpro_mock
):
    get_current_datetime.return_value = datetime(2022, 6, 19, 17, 30)
    tester.setup_state("state_submit_endline_completed")
    await tester.user_input(session=Message.SESSION_EVENT.NEW)

    tester.assert_state("state_endline_end")

    tester.assert_metadata("endline_survey_completed", "True")
    tester.assert_metadata("ejaf_endline_airtime_incentive_sent", "False")
    tester.assert_metadata("ejaf_endline_completed_on", "2022-06-19T17:30:00")

    tester.assert_answer("endline_survey_completed", "True")


@pytest.mark.asyncio
async def test_state_submit_endline_completed_error(tester: AppTester, rapidpro_mock):
    rapidpro_mock.tstate.errormax = 3
    u = User(addr="27820001003", state=StateData(name="state_submit_endline_completed"))
    app = Application(u)
    msg = Message(
        content=None,
        to_addr="27820001002",
        from_addr="27820001003",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
        session_event=Message.SESSION_EVENT.NEW,
    )
    [resp] = await app.process_message(msg)

    assert resp.content == ("Something went wrong. Please try again later.")


@pytest.mark.asyncio
async def test_state_endline_end_invalid_input(tester: AppTester):

    tester.setup_state("state_endline_end")

    await tester.user_input("invalid")

    tester.assert_state("state_endline_end")

    [message] = tester.application.messages
    assert (
        message.content in get_generic_errors()
    ), f"Message content not in provided list, it is {message.content}"


@pytest.mark.asyncio
async def test_state_self_esteem_assessment_endline(tester: AppTester):

    await tester.user_input(
        "test",
        transport_metadata={
            "message": {"button": {"payload": "state_self_esteem_assessment_endline"}}
        },
    )

    tester.assert_state("state_survey_question")
    tester.assert_metadata("assessment_name", "self_esteem_endline")
    tester.assert_metadata(
        "assessment_end_state", "state_self_esteem_assessment_endline_end"
    )


@pytest.mark.asyncio
async def test_state_self_esteem_assessment_endline_end(tester: AppTester):

    await tester.user_input(
        "test",
        transport_metadata={
            "message": {
                "button": {"payload": "state_self_esteem_assessment_endline_end"}
            }
        },
    )

    message = "\n".join(
        [
            "◼️",
            "-----",
            "",
            "*Do you have someone to talk to when you have a worry or problem?*",
        ]
    )

    tester.assert_message(message)
    tester.assert_state("state_survey_question")
    tester.assert_metadata("assessment_name", "connectedness_endline")
    tester.assert_metadata(
        "assessment_end_state", "state_connectedness_assessment_endline_end"
    )


@pytest.mark.asyncio
async def test_state_self_esteem_assessment_end_error(tester: AppTester, rapidpro_mock):

    rapidpro_mock.tstate.errormax = 3
    u = User(
        addr="27820001003",
        state=StateData(name="state_self_esteem_assessment_endline_end"),
    )
    app = Application(u)
    msg = Message(
        content=None,
        to_addr="27820001002",
        from_addr="27820001003",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
        session_event=Message.SESSION_EVENT.NEW,
    )
    [resp] = await app.process_message(msg)

    assert resp.content == ("Something went wrong. Please try again later.")


@pytest.mark.asyncio
async def test_state_connectedness_assessment_end(tester: AppTester):

    await tester.user_input(
        "test",
        transport_metadata={
            "message": {
                "button": {"payload": "state_connectedness_assessment_endline_end"}
            }
        },
    )

    message = "\n".join(
        [
            "◼️◽️",
            "-----",
            "",
            "*Do you agree with this statement?*",
            "",
            "I feel good about myself.",
        ]
    )

    tester.assert_message(message)
    tester.assert_state("state_survey_question")
    tester.assert_metadata("assessment_name", "body_image_endline")
    tester.assert_metadata(
        "assessment_end_state", "state_body_image_assessment_endline_end"
    )


@pytest.mark.asyncio
async def test_state_connectedness_assessment_endline(tester: AppTester):

    await tester.user_input(
        "test",
        transport_metadata={
            "message": {"button": {"payload": "state_connectedness_assessment_endline"}}
        },
    )

    tester.assert_state("state_survey_question")
    tester.assert_metadata("assessment_name", "connectedness_endline")
    tester.assert_metadata(
        "assessment_end_state", "state_connectedness_assessment_endline_end"
    )


@pytest.mark.asyncio
async def test_state_connectedness_assessment_endline_end_error(
    tester: AppTester, rapidpro_mock
):

    rapidpro_mock.tstate.errormax = 3
    u = User(
        addr="27820001003",
        state=StateData(name="state_connectedness_assessment_endline_end"),
    )
    app = Application(u)
    msg = Message(
        content=None,
        to_addr="27820001002",
        from_addr="27820001003",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
        session_event=Message.SESSION_EVENT.NEW,
    )
    [resp] = await app.process_message(msg)

    assert resp.content == ("Something went wrong. Please try again later.")


@pytest.mark.asyncio
async def test_state_body_image_assessment_endline(tester: AppTester):

    await tester.user_input(
        "test",
        transport_metadata={
            "message": {"button": {"payload": "state_body_image_assessment_endline"}}
        },
    )

    tester.assert_state("state_survey_question")
    tester.assert_metadata("assessment_name", "body_image_endline")
    tester.assert_metadata(
        "assessment_end_state", "state_body_image_assessment_endline_end"
    )


@pytest.mark.asyncio
async def test_state_body_image_assessment_end(tester: AppTester):

    await tester.user_input(
        "test",
        transport_metadata={
            "message": {
                "button": {"payload": "state_body_image_assessment_endline_end"}
            }
        },
    )

    message = "\n".join(
        [
            "◼️◽️",
            "-----",
            "",
            "Feeling nervous, anxious or on edge",
        ]
    )

    tester.assert_message(message)
    tester.assert_state("state_survey_question")
    tester.assert_metadata("assessment_name", "anxiety_endline")
    tester.assert_metadata(
        "assessment_end_state", "state_anxiety_assessment_endline_end"
    )


@pytest.mark.asyncio
async def test_state_body_image_assessment_endline_end_error(
    tester: AppTester, rapidpro_mock
):

    rapidpro_mock.tstate.errormax = 3
    u = User(
        addr="27820001003",
        state=StateData(name="state_body_image_assessment_endline_end"),
    )
    app = Application(u)
    msg = Message(
        content=None,
        to_addr="27820001002",
        from_addr="27820001003",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
        session_event=Message.SESSION_EVENT.NEW,
    )
    [resp] = await app.process_message(msg)

    assert resp.content == ("Something went wrong. Please try again later.")


@pytest.mark.asyncio
async def test_state_depression_assessment_endline(tester: AppTester):

    await tester.user_input(
        "test",
        transport_metadata={
            "message": {"button": {"payload": "state_depression_assessment_endline"}}
        },
    )

    tester.assert_state("state_survey_question")
    tester.assert_metadata("assessment_name", "depression_endline")
    tester.assert_metadata(
        "assessment_end_state", "state_depression_assessment_endline_end"
    )


@pytest.mark.asyncio
async def test_depression_assessment_endline_end(tester: AppTester):

    await tester.user_input(
        "test",
        transport_metadata={
            "message": {
                "button": {"payload": "state_depression_assessment_endline_end"}
            }
        },
    )

    message = "\n".join(
        [
            "◼️◽️◽️",
            "-----",
            "",
            "*How good a job do you feel you are doing in taking"
            " care of your health?*",
        ]
    )

    tester.assert_message(message)
    tester.assert_state("state_survey_question")
    tester.assert_metadata("assessment_name", "self_perceived_healthcare_endline")
    tester.assert_metadata(
        "assessment_end_state", "state_self_perceived_healthcare_assessment_endline_end"
    )


@pytest.mark.asyncio
async def test_state_depression_assessment_endline_end_error(
    tester: AppTester, rapidpro_mock
):

    rapidpro_mock.tstate.errormax = 3
    u = User(
        addr="27820001003",
        state=StateData(name="state_depression_assessment_endline_end"),
    )
    app = Application(u)
    msg = Message(
        content=None,
        to_addr="27820001002",
        from_addr="27820001003",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
        session_event=Message.SESSION_EVENT.NEW,
    )
    [resp] = await app.process_message(msg)

    assert resp.content == ("Something went wrong. Please try again later.")


@pytest.mark.asyncio
async def test_state_anxiety_assessment_endline(tester: AppTester):

    await tester.user_input(
        "test",
        transport_metadata={
            "message": {"button": {"payload": "state_anxiety_assessment_endline"}}
        },
    )

    tester.assert_state("state_survey_question")
    tester.assert_metadata("assessment_name", "anxiety_endline")
    tester.assert_metadata(
        "assessment_end_state", "state_anxiety_assessment_endline_end"
    )


@pytest.mark.asyncio
async def test_state_anxiety_assessment_endline_end(tester: AppTester):

    await tester.user_input(
        "test",
        transport_metadata={
            "message": {"button": {"payload": "state_anxiety_assessment_endline_end"}}
        },
    )

    message = "\n".join(
        [
            "◼️◽️",
            "-----",
            "",
            "*Over the last 2 weeks, how often have you been "
            "bothered by the following problems?*",
            "",
            "Feeling down, depressed or hopeless",
        ]
    )
    tester.assert_message(message)
    tester.assert_state("state_survey_question")


@pytest.mark.asyncio
async def test_state_anxiety_assessment_endline_end_error(
    tester: AppTester, rapidpro_mock
):
    rapidpro_mock.tstate.errormax = 3
    u = User(
        addr="27820001003", state=StateData(name="state_anxiety_assessment_endline_end")
    )
    app = Application(u)
    msg = Message(
        content=None,
        to_addr="27820001002",
        from_addr="27820001003",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
        session_event=Message.SESSION_EVENT.NEW,
    )
    [resp] = await app.process_message(msg)

    assert resp.content == ("Something went wrong. Please try again later.")


@pytest.mark.asyncio
async def test_state_endline_start(tester: AppTester, rapidpro_mock):
    await tester.user_input(
        "test",
        transport_metadata={"message": {"button": {"payload": "state_endline_start"}}},
    )

    message = "\n".join(["◼️◽️◽️◽️", "-----", "", "*I'm my own boss.* 😎"])
    tester.assert_message(message)


@pytest.mark.asyncio
async def test_state_depression_and_anxiety_endline_end_error(
    tester: AppTester, rapidpro_mock
):
    rapidpro_mock.tstate.errormax = 3
    u = User(
        addr="27820001003",
        state=StateData(name="state_depression_and_anxiety_endline_end"),
    )
    app = Application(u)
    msg = Message(
        content=None,
        to_addr="27820001002",
        from_addr="27820001003",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
        session_event=Message.SESSION_EVENT.NEW,
    )
    [resp] = await app.process_message(msg)

    assert resp.content == ("Something went wrong. Please try again later.")


@pytest.mark.asyncio
async def test_state_perceived_healthcare_assessment_endline(tester: AppTester):

    await tester.user_input(
        "test",
        transport_metadata={
            "message": {
                "button": {
                    "payload": "state_self_perceived_healthcare_assessment_endline"
                }
            }
        },
    )

    tester.assert_state("state_survey_question")
    tester.assert_metadata("assessment_name", "self_perceived_healthcare_endline")
    tester.assert_metadata(
        "assessment_end_state", "state_self_perceived_healthcare_assessment_endline_end"
    )


@pytest.mark.asyncio
async def test_state_self_perceived_healthcare_assessment_endline_end(
    tester: AppTester,
):

    await tester.user_input(
        "test",
        transport_metadata={
            "message": {
                "button": {
                    "payload": "state_self_perceived_healthcare_assessment_endline_end"
                }
            }
        },
    )

    message = "\n".join(
        [
            "◼️◽️◽️◽️◽️◽️◽️◽️◽️◽️◽️◽️",
            "-----",
            "",
            "*Is the following statement true or false?*",
            "",
            "People can reduce the risk of getting sexually"
            " transmitted infections (STIs) "
            "by using condoms every time they have sex.",
        ]
    )

    tester.assert_message(message)
    tester.assert_state("state_survey_question")
    tester.assert_metadata("assessment_name", "sexual_health_literacy_endline")
    tester.assert_metadata(
        "assessment_end_state", "state_sexual_health_lit_assessment_endline_end"
    )


@pytest.mark.asyncio
async def test_state_state_self_perceived_healthcare_assessment_endline_end_error(
    tester: AppTester, rapidpro_mock
):

    rapidpro_mock.tstate.errormax = 3
    u = User(
        addr="27820001003",
        state=StateData(name="state_self_perceived_healthcare_assessment_endline_end"),
    )
    app = Application(u)
    msg = Message(
        content=None,
        to_addr="27820001002",
        from_addr="27820001003",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
        session_event=Message.SESSION_EVENT.NEW,
    )
    [resp] = await app.process_message(msg)

    assert resp.content == ("Something went wrong. Please try again later.")


@pytest.mark.asyncio
async def test_state_sexual_health_lit_assessment_endline(tester: AppTester):

    await tester.user_input(
        "test",
        transport_metadata={
            "message": {
                "button": {"payload": "state_sexual_health_lit_assessment_endline"}
            }
        },
    )

    tester.assert_state("state_survey_question")
    tester.assert_metadata("assessment_name", "sexual_health_literacy_endline")
    tester.assert_metadata(
        "assessment_end_state", "state_sexual_health_lit_assessment_endline_end"
    )


@pytest.mark.asyncio
async def test_state_sexual_health_lit_assessment_endline_end(tester: AppTester):

    await tester.user_input(
        "test",
        transport_metadata={
            "message": {
                "button": {"payload": "state_sexual_health_lit_assessment_endline_end"}
            }
        },
    )

    message = "\n".join(
        [
            "◼️◽️◽️◽️",
            "-----",
            "",
            "**How do you feel about each of the following statements?* *",
            "",
            "There are times when a woman deserves to be beaten",
        ]
    )

    tester.assert_message(message)
    tester.assert_state("state_survey_question")
    tester.assert_metadata("assessment_name", "gender_attitude_endline")
    tester.assert_metadata(
        "assessment_end_state", "state_gender_attitude_assessment_endline_end"
    )


@pytest.mark.asyncio
async def test_state_sexual_health_lit_assessment_endline_end_error(
    tester: AppTester, rapidpro_mock
):

    rapidpro_mock.tstate.errormax = 3
    u = User(
        addr="27820001003",
        state=StateData(name="state_sexual_health_lit_assessment_endline_end"),
    )
    app = Application(u)
    msg = Message(
        content=None,
        to_addr="27820001002",
        from_addr="27820001003",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
        session_event=Message.SESSION_EVENT.NEW,
    )
    [resp] = await app.process_message(msg)

    assert resp.content == ("Something went wrong. Please try again later.")


@pytest.mark.asyncio
async def test_state_gender_attitude_assessment_endline_end(tester: AppTester):

    await tester.user_input(
        "test",
        transport_metadata={
            "message": {
                "button": {"payload": "state_gender_attitude_assessment_endline_end"}
            }
        },
    )

    message = "\n".join(
        [
            "◼️◽️",
            "-----",
            "",
            "Robert and Samantha have been dating for 5 years and"
            " love each other very much."
            " 👩🏾\u200d❤️\u200d👨🏾\n\nEvery year on Robert's birthday, "
            "Samantha promises him sex for his birthday. "
            "This year, Samantha tells Robert that she is too tired for sex. ",
            "",
            "*To what extent do you agree with this statement:*",
            "",
            "Robert has the right to force Samantha to have sex.",
        ]
    )

    tester.assert_message(message)
    tester.assert_state("state_survey_question")
    tester.assert_metadata("assessment_name", "sexual_consent_endline")
    tester.assert_metadata(
        "assessment_end_state", "state_sexual_consent_assessment_endline_end"
    )


@pytest.mark.asyncio
async def test_state_gender_attitudes_assessment_endline(tester: AppTester):

    await tester.user_input(
        "test",
        transport_metadata={
            "message": {
                "button": {"payload": "state_gender_attitude_assessment_endline"}
            }
        },
    )

    tester.assert_state("state_survey_question")
    tester.assert_metadata("assessment_name", "gender_attitude_endline")
    tester.assert_metadata(
        "assessment_end_state", "state_gender_attitude_assessment_endline_end"
    )


@pytest.mark.asyncio
async def test_state_gender_attitude_assessment_endline_end_error(
    tester: AppTester, rapidpro_mock
):

    rapidpro_mock.tstate.errormax = 3
    u = User(
        addr="27820001003",
        state=StateData(name="state_gender_attitude_assessment_endline_end"),
    )
    app = Application(u)
    msg = Message(
        content=None,
        to_addr="27820001002",
        from_addr="27820001003",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
        session_event=Message.SESSION_EVENT.NEW,
    )
    [resp] = await app.process_message(msg)

    assert resp.content == ("Something went wrong. Please try again later.")


@pytest.mark.asyncio
async def test_state_sexual_consent_assessment_endline(tester: AppTester):

    await tester.user_input(
        "test",
        transport_metadata={
            "message": {
                "button": {"payload": "state_sexual_consent_assessment_endline"}
            }
        },
    )

    tester.assert_state("state_survey_question")
    tester.assert_metadata("assessment_name", "sexual_consent_endline")
    tester.assert_metadata(
        "assessment_end_state", "state_sexual_consent_assessment_endline_end"
    )


@pytest.mark.asyncio
async def test_state_sexual_consent_assessment_endline_end(tester: AppTester):

    await tester.user_input(
        "test",
        transport_metadata={
            "message": {
                "button": {"payload": "state_sexual_consent_assessment_endline_end"}
            }
        },
    )

    message = "\n".join(
        [
            "◼️◽️◽️◽️",
            "-----",
            "",
            "*Have you ever felt guilty about drinking or drug use?* 🍻💉",
        ]
    )

    tester.assert_message(message)
    tester.assert_state("state_survey_question")
    tester.assert_metadata("assessment_name", "alcohol_endline")
    tester.assert_metadata(
        "assessment_end_state", "state_alcohol_assessment_endline_end"
    )


@pytest.mark.asyncio
async def test_state_sexual_consent_assessment_endline_end_error(
    tester: AppTester, rapidpro_mock
):

    rapidpro_mock.tstate.errormax = 3
    u = User(
        addr="27820001003",
        state=StateData(name="state_sexual_consent_assessment_endline_end"),
    )
    app = Application(u)
    msg = Message(
        content=None,
        to_addr="27820001002",
        from_addr="27820001003",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
        session_event=Message.SESSION_EVENT.NEW,
    )
    [resp] = await app.process_message(msg)

    assert resp.content == ("Something went wrong. Please try again later.")


@pytest.mark.asyncio
async def test_state_alcohol_assessment_endline_end(tester: AppTester):

    await tester.user_input(
        "test",
        transport_metadata={
            "message": {"button": {"payload": "state_alcohol_assessment_endline_end"}}
        },
    )

    message = "\n".join(
        [
            "◼️◽️◽️◽️◽️◽️◽️◽️◽️",
            "-----",
            "",
            "You have received a lot of content from BWise.",
            "",
            "*Did BWise send you content that related to your sexual needs?*",
        ]
    )

    tester.assert_message(message)
    tester.assert_state("state_survey_question")


@pytest.mark.asyncio
async def test_state_alcohol_assessment_endline_end_error(
    tester: AppTester, rapidpro_mock
):

    rapidpro_mock.tstate.errormax = 3
    u = User(
        addr="27820001003", state=StateData(name="state_alcohol_assessment_endline_end")
    )
    app = Application(u)
    msg = Message(
        content=None,
        to_addr="27820001002",
        from_addr="27820001003",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
        session_event=Message.SESSION_EVENT.NEW,
    )
    [resp] = await app.process_message(msg)

    assert resp.content == ("Something went wrong. Please try again later.")


@pytest.mark.asyncio
@mock.patch("yal.surveys.endline.get_current_datetime")
async def test_state_body_image_assessment_endline_reminder(
    get_current_datetime, tester: AppTester, rapidpro_mock
):
    get_current_datetime.return_value = datetime(2022, 6, 19, 17, 30)
    tester.setup_state("set_endline_reminder_timer")
    await tester.user_input(session=Message.SESSION_EVENT.NEW)

    tester.assert_metadata("assessment_reminder", "2022-06-19T17:30:00")
    tester.assert_metadata("assessment_reminder_name", "locus_of_control_endline")
    tester.assert_metadata("assessment_reminder_type", "endline reengagement 30min")


@pytest.mark.asyncio
async def test_endline_flow(tester: AppTester, rapidpro_mock):
    await tester.user_input(
        "test",
        transport_metadata={"message": {"button": {"payload": "state_endline_start"}}},
    )

    # LOC
    message = "\n".join(["◼️◽️◽️◽️", "-----", "", "*I'm my own boss.* 😎"])
    tester.assert_message(message)
    await tester.user_input("Applies")
    await tester.user_input("Applies")
    await tester.user_input("Applies")
    await tester.user_input("Applies")

    # Self Esteem
    message = "\n".join(
        [
            "◼️◽️◽️◽️◽️◽️◽️◽️◽️",
            "-----",
            "",
            "How do you feel about the following statements?",
            "",
            "*I feel that I am a person of worth,"
            " at least on an equal plane with others.*",
        ]
    )
    tester.assert_message(message)
    await tester.user_input("Agree")
    await tester.user_input("Agree")
    await tester.user_input("Agree")
    await tester.user_input("Skip question")
    await tester.user_input("Disagree")
    await tester.user_input("Agree")
    await tester.user_input("Agree")
    await tester.user_input("Skip question")
    await tester.user_input("Skip question")

    # Connectedness
    message = "\n".join(
        [
            "◼️",
            "-----",
            "",
            "*Do you have someone to talk to when you have a worry or problem?*",
        ]
    )

    tester.assert_message(message)
    await tester.user_input("All of the time")

    # Body Image
    message = "\n".join(
        [
            "◼️◽️",
            "-----",
            "",
            "*Do you agree with this statement?*",
            "",
            "I feel good about myself.",
        ]
    )

    tester.assert_message(message)
    await tester.user_input("Yes")
    await tester.user_input("No")

    # # Anxiety
    message = "\n".join(
        [
            "◼️◽️",
            "-----",
            "",
            "Feeling nervous, anxious or on edge",
        ]
    )

    tester.assert_message(message)

    await tester.user_input("Not at all")
    await tester.user_input("Not at all")

    # Depression
    message = "\n".join(
        [
            "◼️◽️",
            "-----",
            "",
            "*Over the last 2 weeks, how often have you been "
            "bothered by the following problems?*",
            "",
            "Feeling down, depressed or hopeless",
        ]
    )

    tester.assert_message(message)
    await tester.user_input("Not at all")
    await tester.user_input("Not at all")

    # self percieved health
    message = "\n".join(
        [
            "◼️◽️◽️",
            "-----",
            "",
            "*How good a job do you feel you are doing in taking"
            " care of your health?*",
        ]
    )

    tester.assert_message(message)
    await tester.user_input("Excellent")
    await tester.user_input("None")
    await tester.user_input("Yes")

    # sexual literacy
    message = "\n".join(
        [
            "◼️◽️◽️◽️◽️◽️◽️◽️◽️◽️◽️◽️",
            "-----",
            "",
            "*Is the following statement true or false?*",
            "",
            "People can reduce the risk of getting sexually"
            " transmitted infections (STIs) "
            "by using condoms every time they have sex.",
        ]
    )

    tester.assert_message(message)

    await tester.user_input("True")
    await tester.user_input("True")
    await tester.user_input("Agree")
    await tester.user_input("Very true")
    await tester.user_input("Skip question")
    await tester.user_input("Very true")
    await tester.user_input("Skip question")
    await tester.user_input("Skip question")
    await tester.user_input("Pill")
    await tester.user_input("None")
    await tester.user_input("Yes")

    # Gender

    message = "\n".join(
        [
            "◼️◽️◽️◽️",
            "-----",
            "",
            "**How do you feel about each of the following statements?* *",
            "",
            "There are times when a woman deserves to be beaten",
        ]
    )

    tester.assert_message(message)

    await tester.user_input("Skip question")
    await tester.user_input("Strongly agree")
    await tester.user_input("Skip question")
    await tester.user_input("Strongly agree")

    # Sexual Consent
    message = "\n".join(
        [
            "◼️◽️",
            "-----",
            "",
            "Robert and Samantha have been dating for 5 years and"
            " love each other very much."
            " 👩🏾\u200d❤️\u200d👨🏾\n\nEvery year on Robert's birthday, "
            "Samantha promises him sex for his birthday. "
            "This year, Samantha tells Robert that she is too tired for sex. ",
            "",
            "*To what extent do you agree with this statement:*",
            "",
            "Robert has the right to force Samantha to have sex.",
        ]
    )

    tester.assert_message(message)

    await tester.user_input("Strongly agree")
    await tester.user_input("Skip question")

    message = "\n".join(
        [
            "◼️◽️◽️◽️",
            "-----",
            "",
            "*Have you ever felt guilty about drinking or drug use?* 🍻💉",
        ]
    )

    tester.assert_message(message)

    await tester.user_input("Yes")
    await tester.user_input("No")
    await tester.user_input("Yes")
    await tester.user_input("No")

    # Platform
    message = "\n".join(
        [
            "◼️◽️◽️◽️◽️◽️◽️◽️◽️",
            "-----",
            "",
            "You have received a lot of content from BWise.",
            "",
            "*Did BWise send you content that related to your sexual needs?*",
        ]
    )

    tester.assert_message(message)
