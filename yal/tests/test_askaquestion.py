import json
from datetime import datetime
from unittest import mock

import pytest
from sanic import Sanic, response

from vaccine.models import Message
from vaccine.testing import AppTester, TState, run_sanic
from yal import config
from yal.main import Application
from yal.utils import BACK_TO_MAIN


@pytest.fixture
def tester():
    return AppTester(Application)


def get_rapidpro_contact(urn):
    return {
        "fields": {
            "aaq_timeout_type": "1" if ("27820001001" in urn) else "2",
        },
    }


MODEL_ANSWERS_PAGE_1 = {
    "FAQ #1 Title": "This is FAQ #1's content.",
    "FAQ #2 Title that is very long": "This is FAQ #2's content.",
    "FAQ #3 Title": "This is FAQ #3's content.",
}

MODEL_ANSWERS_PAGE_2 = {
    "FAQ #4 Title": "This is FAQ #4's content.",
    "FAQ #5 Title": "This is FAQ #5's content.",
    "FAQ #6 Title": "This is FAQ #6's content.",
}


def get_aaq_response(answers, next=None, prev=None):
    top_responses = [[k, v] for k, v in answers.items()]
    response = {
        "top_responses": top_responses,
        "feedback_secret_key": "abcde12345",
        "inbound_secret_key": "secret_123",
        "inbound_id": 28,
    }
    if next:
        response["next_page_url"] = f"{next}?inbound_secret_key=secret_123"
    if prev:
        response["prev_page_url"] = f"{prev}?inbound_secret_key=secret_123"
    return response


@pytest.fixture
async def aaq_mock():
    Sanic.test_mode = True
    app = Sanic("mock_aaq")
    tstate = TState()

    @app.route("/inbound/check", methods=["POST"])
    def inbound_check(request):
        tstate.requests.append(request)
        body = get_aaq_response(MODEL_ANSWERS_PAGE_1, next="/inbound/92567/1")
        return response.json(body, status=200)

    @app.route("/inbound/92567/1", methods=["GET"])
    def inbound_check_page_2(request):
        tstate.requests.append(request)
        body = get_aaq_response(MODEL_ANSWERS_PAGE_2, prev="/inbound/92567/0")
        return response.json(body, status=200)

    @app.route("/inbound/feedback", methods=["PUT"])
    def add_feedback(request):
        tstate.requests.append(request)
        return response.json({}, status=200)

    async with run_sanic(app) as server:
        url = config.AAQ_URL
        config.AAQ_URL = f"http://{server.host}:{server.port}"
        config.AAQ_TOKEN = "testtoken"
        server.tstate = tstate
        yield server
        config.AAQ_URL = url


@pytest.fixture
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
        return response.json({}, status=200)

    async with run_sanic(app) as server:
        url = config.RAPIDPRO_URL
        config.RAPIDPRO_URL = f"http://{server.host}:{server.port}"
        config.RAPIDPRO_TOKEN = "testtoken"
        server.tstate = tstate
        yield server
        config.RAPIDPRO_URL = url


@pytest.mark.asyncio
@mock.patch("yal.askaquestion.config")
async def test_aaq_start(mock_config, tester: AppTester, rapidpro_mock):
    mock_config.AAQ_URL = "http://aaq-test.com"
    tester.setup_state("state_aaq_start")

    await tester.user_input(session=Message.SESSION_EVENT.NEW)

    tester.assert_state("state_aaq_start")
    tester.assert_num_messages(1)
    tester.assert_message(
        "\n".join(
            [
                "🙋🏿‍♂️ *QUESTIONS?*",
                "Ask A Question",
                "-----",
                "",
                "🙍🏾‍♀️*That's what I'm here for!*",
                "*Just type your Q and hit send* .🙂.",
                "",
                "e.g. _How do I know if I have an STI?_",
                "",
                "-----",
                "*Or reply:*",
                BACK_TO_MAIN,
            ]
        )
    )


@pytest.mark.asyncio
async def test_aaq_start_coming_soon(tester: AppTester):
    tester.setup_state("state_aaq_start")

    await tester.user_input(session=Message.SESSION_EVENT.NEW)

    tester.assert_state("state_start")
    tester.assert_message("Coming soon...")


@pytest.mark.asyncio
@mock.patch("yal.askaquestion.get_current_datetime")
async def test_start_state_response_sets_timeout(
    get_current_datetime, tester: AppTester, rapidpro_mock, aaq_mock
):
    get_current_datetime.return_value = datetime(2022, 6, 19, 17, 30)
    tester.setup_state("state_aaq_start")

    await tester.user_input("How do you do?")

    tester.assert_state("state_display_results")

    assert len(rapidpro_mock.tstate.requests) == 1
    request = rapidpro_mock.tstate.requests[0]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {
            "next_aaq_timeout_time": "2022-06-19T17:35:00",
            "aaq_timeout_type": "1",
        },
    }
    assert len(aaq_mock.tstate.requests) == 1
    request = aaq_mock.tstate.requests[0].json
    request["metadata"].pop("message_id")
    request["metadata"].pop("session_id")
    assert request == {
        "text_to_match": "How do you do?",
        "metadata": {"whatsapp_id": "27820001001"},
    }

    tester.assert_message(
        "\n".join(
            [
                "🙋🏿‍♂️ QUESTIONS?",
                "*Ask A Question*",
                "-----",
                "",
                "🙍🏾‍♀️Here are some FAQs that might answer your question." "",
                "*To see the answer, reply with the number of the FAQ "
                "you're interested in:*",
                "",
                "1. FAQ #1 Title",
                "2. FAQ #2 Title that is very long",
                "3. FAQ #3 Title",
                "4. Show me more",
                "",
                "-----",
                "*Or reply:*",
                "0. 🏠 *Back* to Main *MENU*",
                "#. 🆘Get *HELP*",
            ]
        ),
        button="Choose an option",
        list_items=[
            "FAQ #1 Title",
            "FAQ #2 Title that is",
            "FAQ #3 Title",
            "Show me more",
        ],
    )


@pytest.mark.asyncio
@mock.patch("yal.askaquestion.get_current_datetime")
async def test_state_display_results_choose_an_answer(
    get_current_datetime, tester: AppTester, rapidpro_mock
):
    get_current_datetime.return_value = datetime(2022, 6, 19, 17, 30)
    tester.setup_state("state_display_results")
    tester.user.metadata["aaq_page"] = 0
    tester.user.metadata["inbound_id"] = "inbound-id"
    tester.user.metadata["feedback_secret_key"] = "feedback-secret-key"
    tester.user.metadata["model_answers"] = MODEL_ANSWERS_PAGE_1

    await tester.user_input("FAQ #1 Title")

    tester.assert_state("state_get_content_feedback")

    assert len(rapidpro_mock.tstate.requests) == 1
    request = rapidpro_mock.tstate.requests[0]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {
            "next_aaq_timeout_time": "2022-06-19T17:35:00",
            "aaq_timeout_type": "2",
        },
    }

    [msg] = tester.fake_worker.outbound_messages
    assert msg.content == "\n".join(
        ["🙋🏿‍♂️ QUESTIONS?", "FAQ #1 Title", "-----", "", "This is FAQ #1's content."]
    )

    tester.assert_message(
        "\n".join(
            [
                "*Did we answer your question?*",
                "",
                "*Reply:*",
                "*1* - Yes 👍",
                "*2* - No, go back to list",
            ]
        )
    )


@pytest.mark.asyncio
async def test_state_display_results_next(tester: AppTester, aaq_mock):
    tester.setup_state("state_display_results")
    tester.user.metadata["aaq_page"] = 0
    tester.user.metadata["next_page_url"] = "/inbound/92567/1"
    tester.user.metadata["inbound_id"] = "inbound-id"
    tester.user.metadata["feedback_secret_key"] = "feedback-secret-key"
    tester.user.metadata["model_answers"] = MODEL_ANSWERS_PAGE_1

    await tester.user_input("Show me more")

    tester.assert_state("state_display_results")

    tester.assert_num_messages(1)
    tester.assert_message(
        "\n".join(
            [
                "🙋🏿‍♂️ QUESTIONS?",
                "*Ask A Question*",
                "-----",
                "",
                "🙍🏾‍♀️Here are some FAQs that might answer your question." "",
                "*To see the answer, reply with the number of the FAQ "
                "you're interested in:*",
                "",
                "1. FAQ #4 Title",
                "2. FAQ #5 Title",
                "3. FAQ #6 Title",
                "4. Back to first list",
                "5. Please call me",
                "",
                "-----",
                "*Or reply:*",
                "0. 🏠 *Back* to Main *MENU*",
                "#. 🆘Get *HELP*",
            ]
        )
    )

    [add_feedback, next_page] = aaq_mock.tstate.requests

    assert json.loads(add_feedback.body.decode("utf-8")) == {
        "feedback": {"page_number": "1", "feedback_type": "negative"},
        "feedback_secret_key": "feedback-secret-key",
        "inbound_id": "inbound-id",
    }


@pytest.mark.asyncio
@mock.patch("yal.pleasecallme.get_current_datetime")
async def test_state_display_results_pleasecallme(
    get_current_datetime, tester: AppTester, aaq_mock
):
    get_current_datetime.return_value = datetime(2022, 6, 20, 17, 30)
    tester.setup_state("state_display_results")
    tester.user.metadata["aaq_page"] = 0
    tester.user.metadata["inbound_id"] = "inbound-id"
    tester.user.metadata["feedback_secret_key"] = "feedback-secret-key"
    tester.user.metadata["model_answers"] = MODEL_ANSWERS_PAGE_1

    await tester.user_input("5")

    tester.assert_state("state_in_hours")

    [add_feedback] = aaq_mock.tstate.requests

    assert json.loads(add_feedback.body.decode("utf-8")) == {
        "feedback": {"page_number": "2", "feedback_type": "negative"},
        "feedback_secret_key": "feedback-secret-key",
        "inbound_id": "inbound-id",
    }


@pytest.mark.asyncio
async def test_state_display_results_back(tester: AppTester, aaq_mock):
    tester.setup_state("state_display_results")
    tester.user.metadata["aaq_page"] = 1
    tester.user.metadata["inbound_id"] = "inbound-id"
    tester.user.metadata["feedback_secret_key"] = "feedback-secret-key"
    tester.user.metadata["prev_page_url"] = "/inbound/92567/1"
    tester.user.metadata["model_answers"] = MODEL_ANSWERS_PAGE_2

    await tester.user_input("Back to first list")

    tester.assert_state("state_display_results")


@pytest.mark.asyncio
async def test_state_get_content_feedback_question_answered(
    tester: AppTester, rapidpro_mock, aaq_mock
):
    tester.user.metadata["inbound_id"] = "inbound-id"
    tester.user.metadata["feedback_secret_key"] = "feedback-secret-key"
    tester.setup_state("state_get_content_feedback")

    await tester.user_input("Yes")

    tester.assert_state("state_start")

    assert len(rapidpro_mock.tstate.requests) == 1
    request = rapidpro_mock.tstate.requests[0]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {"aaq_timeout_type": ""},
    }

    assert len(aaq_mock.tstate.requests) == 1
    request = aaq_mock.tstate.requests[0]
    assert json.loads(request.body.decode("utf-8")) == {
        "feedback": {"feedback_type": "positive", "faq_id": "-1"},
        "feedback_secret_key": "feedback-secret-key",
        "inbound_id": "inbound-id",
    }

    tester.assert_num_messages(1)
    tester.assert_message(
        "🙍🏾‍♀️*So glad I could help! If you have another question, "
        "you know what to do!* 😉"
    )


@pytest.mark.asyncio
async def test_state_display_content_question_not_answered(
    tester: AppTester, rapidpro_mock, aaq_mock
):
    tester.user.metadata["inbound_id"] = "inbound-id"
    tester.user.metadata["feedback_secret_key"] = "feedback-secret-key"
    tester.user.metadata["model_answers"] = MODEL_ANSWERS_PAGE_1
    tester.setup_state("state_display_content")
    tester.setup_answer("state_display_results", "FAQ #1 Title")

    await tester.user_input("No")

    tester.assert_state("state_start")

    assert len(rapidpro_mock.tstate.requests) == 1
    request = rapidpro_mock.tstate.requests[0]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {"aaq_timeout_type": ""},
    }

    assert len(aaq_mock.tstate.requests) == 1
    request = aaq_mock.tstate.requests[0]
    assert json.loads(request.body.decode("utf-8")) == {
        "feedback": {"feedback_type": "negative", "faq_id": "-1"},
        "feedback_secret_key": "feedback-secret-key",
        "inbound_id": "inbound-id",
    }

    tester.assert_num_messages(1)
    tester.assert_message("TODO: Handle question not answered")


@pytest.mark.asyncio
@mock.patch("yal.askaquestion.config")
async def test_state_handle_timeout_handles_type_1_yes(
    mock_config, tester: AppTester, rapidpro_mock
):
    mock_config.AAQ_URL = "http://aaq-test.com"
    tester.setup_state("state_handle_timeout_response")
    await tester.user_input(session=Message.SESSION_EVENT.NEW, content="yes ask again")

    assert len(rapidpro_mock.tstate.requests) == 2
    request = rapidpro_mock.tstate.requests[1]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {"aaq_timeout_sent": "", "aaq_timeout_type": ""},
    }

    tester.assert_state("state_aaq_start")


@pytest.mark.asyncio
async def test_state_handle_timeout_handles_type_1_no(tester: AppTester, rapidpro_mock):
    tester.setup_state("state_handle_timeout_response")
    await tester.user_input(session=Message.SESSION_EVENT.NEW, content="no, I'm good")

    assert len(rapidpro_mock.tstate.requests) == 2
    request = rapidpro_mock.tstate.requests[1]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {"aaq_timeout_sent": "", "aaq_timeout_type": ""},
    }

    tester.assert_state("state_start")


@pytest.mark.asyncio
async def test_state_handle_timeout_handles_type_2_yes(
    tester: AppTester, rapidpro_mock
):
    tester.setup_user_address("27820001002")
    tester.setup_state("state_handle_timeout_response")
    await tester.user_input(session=Message.SESSION_EVENT.NEW, content="yes")

    assert len(rapidpro_mock.tstate.requests) == 2
    request = rapidpro_mock.tstate.requests[1]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {"aaq_timeout_sent": "", "aaq_timeout_type": ""},
    }

    tester.assert_state("state_start")

    tester.assert_num_messages(1)
    tester.assert_message(
        "🙍🏾‍♀️*So glad I could help! If you have another question, "
        "you know what to do!* 😉"
    )


@pytest.mark.asyncio
async def test_state_handle_timeout_handles_type_2_no(tester: AppTester, rapidpro_mock):
    tester.setup_user_address("27820001002")
    tester.setup_state("state_handle_timeout_response")
    await tester.user_input(session=Message.SESSION_EVENT.NEW, content="no")

    assert len(rapidpro_mock.tstate.requests) == 2
    request = rapidpro_mock.tstate.requests[1]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {"aaq_timeout_sent": "", "aaq_timeout_type": ""},
    }

    tester.assert_state("state_start")

    tester.assert_num_messages(1)
    tester.assert_message("TODO: Handle question not answered")
