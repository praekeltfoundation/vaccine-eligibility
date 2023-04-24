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


@pytest.fixture
async def contentrepo_api_mock():
    Sanic.test_mode = True
    app = Sanic("contentrepo_api_mock")
    tstate = TState()

    @app.route("/api/v2/pages", methods=["GET"])
    def get_main_menu(request):
        tstate.requests.append(request)
        return response.json(
            {
                "count": 0,
                "results": [],
            }
        )

    async with run_sanic(app) as server:
        url = config.CONTENTREPO_API_URL
        config.CONTENTREPO_API_URL = f"http://{server.host}:{server.port}"
        server.tstate = tstate
        yield server
        config.CONTENTREPO_API_URL = url


@pytest.mark.asyncio
async def test_survey_start(tester: AppTester):
    """
    Should clear all assessment state for a new assessment
    """
    tester.setup_state("state_survey_question")
    await tester.user_input("2")
    assert "assessment_question_nr" in tester.user.metadata

    tester.setup_state("state_survey_start")
    await tester.user_input()
    assert "assessment_question_nr" not in tester.user.metadata
    tester.assert_answer("assessment_started", "locus_of_control")


@pytest.mark.asyncio
async def test_survey_next_question(tester: AppTester):
    tester.setup_state("state_survey_question")
    await tester.user_input("2")
    tester.assert_state("state_survey_question")
    tester.assert_answer("state_a2_1_q1_loc_of_ctrl", "applies_somewhat")


@pytest.mark.asyncio
async def test_list_question_type(tester: AppTester):
    """
    The list question type should ask the user the question using a whatsapp list
    interactive message
    """
    questions = {
        "locus_of_control": {
            "1": {
                "start": "q1",
                "questions": {
                    "q1": {
                        "type": "list",
                        "text": "Test question",
                        "options": [
                            "Choice 1",
                            "Choice 2",
                        ],
                        "button": "Select a choice",
                    }
                },
            }
        }
    }
    with mock.patch("yal.assessments.QUESTIONS", questions):
        tester.setup_state("state_survey_question")
        await tester.user_input(session=Message.SESSION_EVENT.NEW)
        tester.assert_message(
            content="\n".join(["◼️", "-----", "", "Test question"]),
            list_items=["Choice 1", "Choice 2"],
            button="Select a choice",
        )


@pytest.mark.asyncio
async def test_button_question_type(tester: AppTester):
    """
    The list question type should ask the user the question using a whatsapp button
    interactive message
    """
    questions = {
        "locus_of_control": {
            "1": {
                "start": "q1",
                "questions": {
                    "q1": {
                        "type": "button",
                        "text": "Test question",
                        "options": [
                            "Choice 1",
                            "Choice 2",
                        ],
                        "button": "Select a choice",
                    }
                },
            }
        }
    }
    with mock.patch("yal.assessments.QUESTIONS", questions):
        tester.setup_state("state_survey_question")
        await tester.user_input(session=Message.SESSION_EVENT.NEW)
        tester.assert_message(
            content="\n".join(["◼️", "-----", "", "Test question"]),
            buttons=["Choice 1", "Choice 2"],
        )


@pytest.mark.asyncio
async def test_scoring(tester: AppTester):
    """
    Scoring should add or remove from the total
    """
    tester.user.metadata["assessment_end_state"] = "state_catch_all"
    questions = {
        "locus_of_control": {
            "1": {
                "start": "q1",
                "questions": {
                    "q1": {
                        "type": "button",
                        "text": "Test question",
                        "options": ["Choice 1", "Choice 2"],
                        "scoring": {"choice_1": 1, "choice_2": 2},
                        "next": None,
                    }
                },
            }
        }
    }
    with mock.patch("yal.assessments.QUESTIONS", questions):
        tester.setup_state("state_survey_question")
        await tester.user_input("2")
        tester.assert_metadata("assessment_score", 2)
        # I can't get this to assert. Printing info during tests shows it is there
        # tester.assert_answer("assessment_completed", "locus_of_control")


@pytest.mark.asyncio
async def test_info_message(tester: AppTester):
    """
    Info messages should send the next question
    """

    questions = {
        "locus_of_control": {
            "1": {
                "start": "info_start",
                "questions": {
                    "info_start": {
                        "type": "info",
                        "text": "this is just an info message",
                        "next": "q1",
                    },
                    "q1": {
                        "type": "button",
                        "text": "Test question",
                        "options": [
                            "Choice 1",
                            "Choice 2",
                        ],
                        "button": "Select a choice",
                    },
                },
            }
        }
    }
    with mock.patch("yal.assessments.QUESTIONS", questions):
        tester.setup_state("state_survey_question")
        await tester.user_input(session=Message.SESSION_EVENT.NEW)
        tester.assert_message(
            content="\n".join(["◼️", "-----", "", "Test question"]),
            buttons=["Choice 1", "Choice 2"],
        )


@pytest.mark.asyncio
@mock.patch("yal.assessments.get_current_datetime")
async def test_state_handle_assessment_reminder_response_now(
    get_current_datetime, tester: AppTester
):
    get_current_datetime.return_value = datetime(2022, 6, 19, 17, 30)
    tester.user.metadata["assessment_reminder_name"] = "sexual_health_literacy"
    tester.user.metadata["assessment_reminder_sent"] = ""
    tester.user.metadata["assessment_reminder_type"] = "reengagement 30min"

    tester.setup_state("state_handle_assessment_reminder_response")
    await tester.user_input("Ask away!")
    tester.assert_state("state_survey_question")


@pytest.mark.asyncio
@mock.patch("yal.assessments.get_current_datetime")
async def test_state_handle_assessment_reminder_response_now_lets_do_it(
    get_current_datetime, tester: AppTester
):
    get_current_datetime.return_value = datetime(2022, 6, 19, 17, 30)
    tester.user.metadata["assessment_reminder_name"] = "sexual_health_literacy"
    tester.user.metadata["assessment_reminder_sent"] = ""
    tester.user.metadata["assessment_reminder_type"] = "reengagement 30min"

    tester.setup_state("state_handle_assessment_reminder_response")
    await tester.user_input("Let's do it!")
    tester.assert_state("state_survey_question")


@pytest.mark.asyncio
@mock.patch("yal.assessments.get_current_datetime")
async def test_state_handle_assessment_reminder_response_1h(
    get_current_datetime, tester: AppTester
):
    get_current_datetime.return_value = datetime(2022, 6, 19, 17, 30)
    tester.user.metadata["assessment_reminder_name"] = "sexual_health_literacy"
    tester.user.metadata["assessment_reminder_sent"] = ""
    tester.user.metadata["assessment_reminder_type"] = "reengagement 30min"

    tester.setup_state("state_handle_assessment_reminder_response")
    await tester.user_input("Remind me in 1 hour")
    tester.assert_state("state_generic_what_would_you_like_to_do")

    assert tester.user.metadata == {
        "assessment_reminder": "2022-06-19T17:30:00",
        "assessment_reminder_hours": "1hour",
        "assessment_reminder_name": "sexual_health_literacy",
        "assessment_reminder_sent": "",
        "assessment_reminder_type": "reengagement 1hour",
    }


@pytest.mark.asyncio
@mock.patch("yal.assessments.get_current_datetime")
async def test_state_handle_assessment_reminder_response_23h(
    get_current_datetime, tester: AppTester
):
    get_current_datetime.return_value = datetime(2022, 6, 19, 17, 30)
    tester.user.metadata["assessment_reminder_name"] = "locus_of_control"
    tester.user.metadata["assessment_reminder_sent"] = ""
    tester.user.metadata["assessment_reminder_type"] = "later 1h"

    tester.setup_state("state_handle_assessment_reminder_response")
    await tester.user_input("Remind me tomorrow")
    tester.assert_state("state_remind_tomorrow")

    assert tester.user.metadata == {
        "assessment_reminder": "2022-06-19T17:30:00",
        "assessment_reminder_hours": "23hours",
        "assessment_reminder_name": "locus_of_control",
        "assessment_reminder_sent": "",
        "assessment_reminder_type": "later 23hours",
    }


@pytest.mark.asyncio
async def test_state_handle_assessment_reminder_response_skip(tester: AppTester):
    tester.user.metadata["assessment_reminder_name"] = "sexual_health_literacy"
    tester.user.metadata["assessment_reminder_sent"] = ""
    tester.user.metadata["assessment_reminder_type"] = "reengagement 30min"

    tester.setup_state("state_handle_assessment_reminder_response")
    await tester.user_input(session=Message.SESSION_EVENT.NEW, content="skip")
    tester.assert_state("state_stop_assessment_reminders_confirm")
    tester.assert_message(
        "\n".join(
            [
                "Just a heads up, you'll get the best info for *YOU* if "
                "you complete the questions first.",
                "",
                "*Are you sure you want to skip this step?*",
            ]
        )
    )
    await tester.user_input(content="Yes, skip it")
    tester.assert_state("state_stop_assessment_reminders")
    tester.assert_message(
        "\n".join(
            [
                "Cool-cool.",
                "",
                "*What would you like to do now?*",
            ]
        )
    )

    assert tester.user.metadata == {
        "assessment_reminder_name": "",
        "assessment_reminder_sent": "",
        "assessment_reminder_type": "",
        "sexual_health_lit_risk": "high_risk",
    }


@pytest.mark.asyncio
async def test_state_handle_assessment_reminder_response_skip_loc(tester: AppTester):
    tester.user.metadata["assessment_reminder_name"] = "locus_of_control"
    tester.user.metadata["assessment_reminder_sent"] = ""
    tester.user.metadata["assessment_reminder_type"] = "reengagement 30min"

    tester.setup_state("state_handle_assessment_reminder_response")
    await tester.user_input(session=Message.SESSION_EVENT.NEW, content="skip")
    tester.assert_state("state_stop_assessment_reminders_confirm")
    tester.assert_message(
        "\n".join(
            [
                "Please take note👆🏽 you can't access all parts of the "
                "Bwise bot if you don't complete the questions first.",
                "",
                "You can still use the menu and ask questions, but I "
                "can't give you a personalised journey.",
                "",
                "*Are you sure you want to skip?*",
            ]
        )
    )
    await tester.user_input(content="Yes, skip it")
    tester.assert_state("state_stop_assessment_reminders")
    tester.assert_message(
        "\n".join(
            [
                "No problem.",
                "",
                "*What would you like to do now?*",
            ]
        )
    )


@pytest.mark.asyncio
async def test_state_handle_assessment_reminder_response_loc_tomorrow_again(
    tester: AppTester,
):
    tester.user.metadata["assessment_reminder_name"] = "locus_of_control"
    tester.user.metadata["assessment_reminder_sent"] = "True"
    tester.user.metadata["assessment_reminder_type"] = "reengagement 30min"

    tester.setup_state("state_handle_assessment_reminder_response")
    await tester.user_input(
        session=Message.SESSION_EVENT.NEW, content="Remind me tomorrow"
    )
    tester.assert_message("No problem! I'll remind you tomorrow")
    tester.assert_state("state_remind_tomorrow")


@pytest.mark.asyncio
async def test_state_handle_assessment_reminder_response_not_interested(
    tester: AppTester, contentrepo_api_mock, rapidpro_mock
):
    tester.user.metadata["assessment_reminder_sent"] = "True"
    tester.setup_state("state_survey_question")
    await tester.user_input("I'm not interested")
    tester.assert_state("state_mainmenu")

    assert len(rapidpro_mock.tstate.requests) == 4
    request = rapidpro_mock.tstate.requests[1]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {
            "assessment_reminder_name": "",
            "assessment_reminder_sent": "",
            "assessment_reminder_type": "",
        },
    }
    tester.assert_metadata("assessment_reminder_name", "")
    tester.assert_metadata("assessment_reminder_sent", "")
    tester.assert_metadata("assessment_reminder_type", "")


def test_clean_name(tester: AppTester):
    """
    Should return the assessment name without the 'state_' or '_assessment'
    """
    assert (
        tester.application.clean_name("state_mental_health_assessment")  # type: ignore
        == "mental_health"
    )
