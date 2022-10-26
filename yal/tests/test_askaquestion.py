import json
from datetime import datetime
from unittest import mock

import pytest
from sanic import Sanic, response

from vaccine.models import Message
from vaccine.testing import AppTester, MockServer, TState, run_sanic
from yal import config
from yal.main import Application
from yal.utils import BACK_TO_MAIN, GET_HELP


@pytest.fixture
def tester():
    return AppTester(Application)


def get_rapidpro_contact(urn):
    return {
        "fields": {
            "feedback_type": "ask_a_question"
            if ("27820001001" in urn)
            else "ask_a_question_2",
            "feedback_sent": "TRUE",
        },
    }


MODEL_ANSWERS_PAGE_1 = {
    "FAQ #1 Title": {"id": "1", "body": "This is FAQ #1's content."},
    "FAQ #2 Title that is very long": {"id": "2", "body": "This is FAQ #2's content."},
    "FAQ #3 Title": {"id": "3", "body": "This is FAQ #3's content."},
    "FAQ #4 Title": {"id": "4", "body": "This is FAQ #4's content."},
    "FAQ #5 Title": {"id": "5", "body": "This is FAQ #5's content."},
}

MODEL_ANSWERS_PAGE_2 = {
    "FAQ #6 Title": {"id": "6", "body": "This is FAQ #6's content."},
    "FAQ #7 Title": {"id": "7", "body": "This is FAQ #7's content."},
    "FAQ #8 Title": {"id": "8", "body": "This is FAQ #8's content."},
}


def get_aaq_response(answers, next=None, prev=None):
    top_responses = [[v["id"], k, v["body"]] for k, v in answers.items()]
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
        data = json.loads(request.body)
        if data["text_to_match"] == "empty":
            body = get_aaq_response({})
        else:
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
                "🙋🏿‍♂️ QUESTIONS? / *Ask A Question*",
                "-----",
                "",
                "🤖 *That's what I'm here for!*",
                "*Just type your Q and hit send* 🙂",
                "",
                "e.g. _How do I know if I have an STI?_",
                "",
                "-----",
                "*Or reply:*",
                BACK_TO_MAIN,
                GET_HELP,
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
            "feedback_timestamp": "2022-06-19T17:35:00",
            "feedback_type": "ask_a_question",
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
                "🙋🏿‍♂️ QUESTIONS? / Ask A Question / *1st 5 matches*",
                "-----",
                "",
                "🤖 Here are some answers to your question.",
                "",
                "*What would you like to read first?* Reply with the number of the "
                "topic you're interested in.",
                "",
                "*1*. FAQ #1 Title",
                "*2*. FAQ #2 Title that is very long",
                "*3*. FAQ #3 Title",
                "*4*. FAQ #4 Title",
                "*5*. FAQ #5 Title",
                "",
                "or",
                "*6*. See more options",
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
            "FAQ #4 Title",
            "FAQ #5 Title",
            "See more options",
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
            "feedback_timestamp": "2022-06-19T17:35:00",
            "feedback_type": "ask_a_question_2",
        },
    }

    [msg] = tester.fake_worker.outbound_messages
    assert msg.content == "\n".join(
        [
            "🙋🏿‍♂️ QUESTIONS? / *FAQ #1 Title*",
            "-----",
            "",
            "🤖 This is FAQ #1's content.",
        ]
    )

    tester.assert_message(
        "\n".join(
            [
                "🤖 *Did I answer your question?*",
                "",
                "*Reply:*",
                "*1*. Yes",
                "*2*. No, go back to list",
                "*3*. Nope...",
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

    await tester.user_input("See more options")

    tester.assert_state("state_display_results")

    tester.assert_num_messages(1)
    tester.assert_message(
        "\n".join(
            [
                "🙋🏿‍♂️ QUESTIONS? / Ask A Question / *2nd 3 matches*",
                "-----",
                "",
                "🤖 Here are some more topics that might answer your question.",
                "",
                "*Which of these would you like to explore?* To see the answer, reply "
                "with the number of the topic you're interested in.",
                "",
                "*1*. FAQ #6 Title",
                "*2*. FAQ #7 Title",
                "*3*. FAQ #8 Title",
                "",
                "or",
                "*4*. Back to first list",
                "*5*. Talk to a counsellor",
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
@mock.patch("yal.askaquestion.get_current_datetime")
async def test_state_display_results_no_answers(
    get_current_datetime, tester: AppTester, rapidpro_mock, aaq_mock
):
    get_current_datetime.return_value = datetime(2022, 6, 19, 17, 30)
    tester.setup_state("state_aaq_start")

    await tester.user_input("empty")

    tester.assert_state("state_aaq_start")
    tester.assert_answer("state_no_answers", "empty")

    assert len(rapidpro_mock.tstate.requests) == 1
    request = rapidpro_mock.tstate.requests[0]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {
            "feedback_timestamp": "2022-06-19T17:35:00",
            "feedback_type": "ask_a_question",
        },
    }
    assert len(aaq_mock.tstate.requests) == 1
    request = aaq_mock.tstate.requests[0].json
    request["metadata"].pop("message_id")
    request["metadata"].pop("session_id")
    assert request == {
        "text_to_match": "empty",
        "metadata": {"whatsapp_id": "27820001001"},
    }
    tester.assert_num_messages(1)
    tester.assert_message(
        "\n".join(
            [
                "🤖 *Hmm. I couldn't find an answer for that, but "
                "maybe I misunderstood the question.*",
                "",
                "Do you mind trying again?",
                "",
                "-----",
                "*Or reply:*",
                GET_HELP,
                BACK_TO_MAIN,
            ]
        )
    )


@pytest.mark.asyncio
@mock.patch("yal.pleasecallme.get_current_datetime")
async def test_state_display_results_pleasecallme(
    get_current_datetime, tester: AppTester, aaq_mock
):
    get_current_datetime.return_value = datetime(2022, 6, 20, 17, 30)
    tester.setup_state("state_display_results")
    tester.user.metadata["aaq_page"] = 1
    tester.user.metadata["inbound_id"] = "inbound-id"
    tester.user.metadata["feedback_secret_key"] = "feedback-secret-key"
    tester.user.metadata["model_answers"] = MODEL_ANSWERS_PAGE_2

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
    tester.user.metadata["faq_id"] = "1"
    tester.setup_state("state_get_content_feedback")

    await tester.user_input("Yes")

    tester.assert_state("state_yes_question_answered")

    assert len(rapidpro_mock.tstate.requests) == 1
    request = rapidpro_mock.tstate.requests[0]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {"feedback_type": ""},
    }

    assert len(aaq_mock.tstate.requests) == 1
    request = aaq_mock.tstate.requests[0]
    assert json.loads(request.body.decode("utf-8")) == {
        "feedback": {"feedback_type": "positive", "faq_id": "1"},
        "feedback_secret_key": "feedback-secret-key",
        "inbound_id": "inbound-id",
    }

    tester.assert_num_messages(1)
    message = "\n".join(
        [
            "*That's great - I'm so happy I could help.* 😊 ",
            "",
            "Is there anything that you would change about my answer?",
            "",
            "*Reply:*",
            "1. No changes",
            "2. Yes, I have a change",
            "",
            "-----",
            "*Or reply:*",
            BACK_TO_MAIN,
            GET_HELP,
        ]
    )
    tester.assert_message(message)


@pytest.mark.asyncio
async def test_state_display_content_question_not_answered(
    tester: AppTester, rapidpro_mock, aaq_mock
):
    tester.user.metadata["inbound_id"] = "inbound-id"
    tester.user.metadata["feedback_secret_key"] = "feedback-secret-key"
    tester.user.metadata["faq_id"] = "1"
    tester.user.metadata["model_answers"] = MODEL_ANSWERS_PAGE_1
    tester.user.metadata["aaq_page"] = 0
    tester.setup_state("state_display_content")
    tester.setup_answer("state_display_results", "FAQ #1 Title")

    await tester.user_input("Nope...")

    tester.assert_state("state_no_question_not_answered")

    message = "\n".join(
        [
            "*I'm sorry I couldn't find what you were looking for this time.* ",
            "",
            "Please tell me what you're looking for again. "
            "I'll try make sure I have the right information "
            "for you next time.",
            "",
            "_Just type and send your question again, now._" "",
            "-----",
            "*Or reply:*",
            BACK_TO_MAIN,
            GET_HELP,
        ]
    )

    tester.assert_message(message)

    assert len(aaq_mock.tstate.requests) == 1
    request = aaq_mock.tstate.requests[0]
    assert json.loads(request.body.decode("utf-8")) == {
        "feedback": {"feedback_type": "negative", "faq_id": "1"},
        "feedback_secret_key": "feedback-secret-key",
        "inbound_id": "inbound-id",
    }


@pytest.mark.asyncio
async def test_state_no_question_not_answered(
    tester: AppTester, rapidpro_mock, aaq_mock
):
    tester.setup_state("state_no_question_not_answered")

    await tester.user_input("how do I get someone to love me")

    tester.assert_state("state_no_question_not_answered_thank_you")

    message = "\n".join(
        [
            "Ok got it. I'll start working on this right away 👍🏾",
            "",
            "Thank you for the feedback, you're helping this service improve.",
            "",
            "What would you like to do now?",
            "",
            "1. Find a clinic",
            "2. Talk to a counsellor",
            "",
            "-----",
            "*Or reply:*",
            BACK_TO_MAIN,
            GET_HELP,
        ]
    )

    tester.assert_message(message)


@pytest.mark.asyncio
async def test_timeout_invalid_keyword(tester: AppTester, rapidpro_mock: MockServer):
    """If the user responds with a keyword we don't recognise, show them the error"""
    tester.setup_state("state_handle_timeout_response")
    await tester.user_input("invalid")
    tester.assert_state("state_aaq_timeout_unrecognised_option")


@pytest.mark.asyncio
async def test_timeout_invalid_keyword_back_to_feedback(
    tester: AppTester, rapidpro_mock: MockServer
):
    """If the user responds with a keyword we don't recognise, show them the error"""
    tester.setup_state("state_handle_timeout_response")
    await tester.user_input("invalid")
    tester.assert_state("state_aaq_timeout_unrecognised_option")

    await tester.user_input("reply to last text")
    tester.assert_state("state_handle_list_timeout")


@pytest.mark.asyncio
async def test_state_display_content_question_back_to_list(
    tester: AppTester, rapidpro_mock, aaq_mock
):
    tester.user.metadata["inbound_id"] = "inbound-id"
    tester.user.metadata["feedback_secret_key"] = "feedback-secret-key"
    tester.user.metadata["faq_id"] = "1"
    tester.user.metadata["model_answers"] = MODEL_ANSWERS_PAGE_1
    tester.user.metadata["aaq_page"] = 0
    tester.setup_state("state_display_content")
    tester.setup_answer("state_display_results", "FAQ #1 Title")

    await tester.user_input("No, go back to list")

    tester.assert_state("state_display_results")

    assert len(aaq_mock.tstate.requests) == 1
    request = aaq_mock.tstate.requests[0]
    assert json.loads(request.body.decode("utf-8")) == {
        "feedback": {"feedback_type": "negative", "faq_id": "1"},
        "feedback_secret_key": "feedback-secret-key",
        "inbound_id": "inbound-id",
    }


@pytest.mark.asyncio
@mock.patch("yal.askaquestion.config")
async def test_state_handle_timeout_handles_type_1_yes(
    mock_config, tester: AppTester, rapidpro_mock
):
    mock_config.AAQ_URL = "http://aaq-test.com"
    tester.setup_state("state_handle_timeout_response")
    await tester.user_input("yes, ask again")

    assert len(rapidpro_mock.tstate.requests) == 2
    request = rapidpro_mock.tstate.requests[-1]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {"feedback_survey_sent": "", "feedback_timestamp": ""},
    }
    tester.assert_metadata("feedback_timestamp", "")

    tester.assert_state("state_aaq_start")


@pytest.mark.asyncio
async def test_state_handle_timeout_handles_type_1_no(tester: AppTester, rapidpro_mock):
    tester.setup_state("state_handle_timeout_response")
    await tester.user_input("no, I'm good")

    assert len(rapidpro_mock.tstate.requests) == 3
    request = rapidpro_mock.tstate.requests[1]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {"feedback_survey_sent": "", "feedback_timestamp": ""},
    }
    tester.assert_metadata("feedback_timestamp", "")

    tester.assert_state("state_mainmenu")


@pytest.mark.asyncio
async def test_state_handle_timeout_handles_type_2_yes(
    tester: AppTester, rapidpro_mock, aaq_mock
):
    tester.setup_user_address("27820001002")
    tester.setup_state("state_handle_timeout_response")
    tester.user.metadata["inbound_id"] = "inbound-id"
    tester.user.metadata["feedback_secret_key"] = "feedback-secret-key"
    tester.user.metadata["faq_id"] = "1"
    tester.user.metadata["model_answers"] = MODEL_ANSWERS_PAGE_1
    tester.user.metadata["aaq_page"] = 0
    await tester.user_input(content="yes")

    assert len(rapidpro_mock.tstate.requests) == 3
    request = rapidpro_mock.tstate.requests[1]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {"feedback_survey_sent": "", "feedback_timestamp": ""},
    }
    tester.assert_metadata("feedback_timestamp", "")

    tester.assert_state("state_yes_question_answered")

    tester.assert_num_messages(1)
    message = "\n".join(
        [
            "*That's great - I'm so happy I could help.* 😊 ",
            "",
            "Is there anything that you would change about my answer?",
            "",
            "*Reply:*",
            "1. No changes",
            "2. Yes, I have a change",
            "",
            "-----",
            "*Or reply:*",
            BACK_TO_MAIN,
            GET_HELP,
        ]
    )
    tester.assert_message(message)

    assert len(aaq_mock.tstate.requests) == 1
    request = aaq_mock.tstate.requests[0]
    assert json.loads(request.body.decode("utf-8")) == {
        "feedback": {"feedback_type": "positive", "faq_id": "1"},
        "feedback_secret_key": "feedback-secret-key",
        "inbound_id": "inbound-id",
    }


@pytest.mark.asyncio
async def test_state_handle_timeout_handles_type_2_no(
    tester: AppTester, rapidpro_mock, aaq_mock
):
    tester.setup_user_address("27820001002")
    tester.setup_state("state_handle_timeout_response")
    tester.user.metadata["inbound_id"] = "inbound-id"
    tester.user.metadata["feedback_secret_key"] = "feedback-secret-key"
    tester.user.metadata["faq_id"] = "1"
    tester.user.metadata["model_answers"] = MODEL_ANSWERS_PAGE_1
    tester.user.metadata["aaq_page"] = 0
    await tester.user_input(content="nope...")

    assert len(rapidpro_mock.tstate.requests) == 3
    request = rapidpro_mock.tstate.requests[1]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {"feedback_survey_sent": "", "feedback_timestamp": ""},
    }
    tester.assert_metadata("feedback_timestamp", "")

    tester.assert_state("state_no_question_not_answered")

    tester.assert_num_messages(1)
    message = "\n".join(
        [
            "*I'm sorry I couldn't find what you were looking for this time.* ",
            "",
            "Please tell me what you're looking for again. "
            "I'll try make sure I have the right information "
            "for you next time.",
            "",
            "_Just type and send your question again, now._" "",
            "-----",
            "*Or reply:*",
            BACK_TO_MAIN,
            GET_HELP,
        ]
    )
    tester.assert_message(message)

    assert len(aaq_mock.tstate.requests) == 1
    request = aaq_mock.tstate.requests[0]
    assert json.loads(request.body.decode("utf-8")) == {
        "feedback": {"feedback_type": "negative", "faq_id": "1"},
        "feedback_secret_key": "feedback-secret-key",
        "inbound_id": "inbound-id",
    }


@pytest.mark.asyncio
async def test_state_yes_question_answered_no_changes(tester: AppTester, rapidpro_mock):
    tester.setup_user_address("27820001002")
    tester.setup_state("state_yes_question_answered")

    await tester.user_input("No changes")

    tester.assert_state("state_yes_question_answered_no_changes")

    tester.assert_num_messages(1)
    message = "\n".join(
        [
            "Thank you so much for your feedback.",
            "",
            "🤖 *If you have another question, " "you know what to do!* 😉 ",
            "",
            "*What would you like to do now?*",
            "",
            "1. Ask another question",
            "2. Talk to a counsellor",
            "",
            "-----",
            "*Or reply:*",
            BACK_TO_MAIN,
            GET_HELP,
        ]
    )
    tester.assert_message(message)


@pytest.mark.asyncio
async def test_state_yes_question_answered_changes(tester: AppTester, aaq_mock):
    tester.setup_user_address("27820001002")
    tester.setup_state("state_yes_question_answered")

    await tester.user_input("Yes, I have a change")

    tester.assert_state("state_yes_question_answered_changes")

    tester.assert_num_messages(1)
    message = "\n".join(
        [
            "Please tell me what was missing or "
            "what you would have changed in my answer.",
            "",
            "_Just type and send it now._",
            "",
            "-----",
            "*Or reply:*",
            BACK_TO_MAIN,
            GET_HELP,
        ]
    )
    tester.assert_message(message)


@pytest.mark.asyncio
async def test_state_yes_question_answered_changes_given(
    tester: AppTester, rapidpro_mock
):
    tester.setup_user_address("27820001002")
    tester.setup_state("state_yes_question_answered_changes")

    await tester.user_input("Please change stuff")

    tester.assert_state("state_no_question_not_answered_thank_you")

    tester.assert_num_messages(1)
    message = "\n".join(
        [
            "Ok got it. I'll start working on this right away 👍🏾",
            "",
            "Thank you for the feedback, you're helping this service improve.",
            "",
            "What would you like to do now?",
            "",
            "1. Find a clinic",
            "2. Talk to a counsellor",
            "",
            "-----",
            "*Or reply:*",
            BACK_TO_MAIN,
            GET_HELP,
        ]
    )
    tester.assert_message(message)
