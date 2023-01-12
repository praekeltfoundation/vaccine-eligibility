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


@pytest.mark.asyncio
async def test_survey_next_question(tester: AppTester):
    tester.setup_state("state_survey_question")
    await tester.user_input("2")
    tester.assert_state("state_survey_question")
    tester.assert_answer("state_a2_1_q1_loc_of_ctrl", "a_little_true")


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
