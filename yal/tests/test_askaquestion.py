import json
from datetime import datetime
from unittest import mock

import pytest
from sanic import Sanic, response

from vaccine.models import Message
from vaccine.testing import AppTester
from yal import config
from yal.main import Application


@pytest.fixture
def tester():
    return AppTester(Application)


def get_rapidpro_contact(urn):
    return {
        "fields": {
            "aaq_timeout_type": "1" if ("27820001001" in urn) else "2",
        },
    }


@pytest.fixture
async def rapidpro_mock(sanic_client):
    Sanic.test_mode = True
    app = Sanic("mock_rapidpro")
    app.requests = []

    @app.route("/api/v2/contacts.json", methods=["GET"])
    def get_contact(request):
        app.requests.append(request)

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
async def test_aaq_start(tester: AppTester, rapidpro_mock):
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
                "*0* - 🏠 Back to Main *MENU*",
            ]
        )
    )


@pytest.mark.asyncio
@mock.patch("yal.askaquestion.get_current_datetime")
async def test_start_state_response_sets_timeout(
    get_current_datetime, tester: AppTester, rapidpro_mock
):
    get_current_datetime.return_value = datetime(2022, 6, 19, 17, 30)
    tester.setup_state("state_aaq_start")

    await tester.user_input("How do you do?")

    tester.assert_state("state_display_results")

    assert len(rapidpro_mock.app.requests) == 1
    request = rapidpro_mock.app.requests[0]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {
            "next_aaq_timeout_time": "2022-06-19T17:35:00",
            "aaq_timeout_type": "1",
        },
    }


@pytest.mark.asyncio
@mock.patch("yal.askaquestion.get_current_datetime")
async def test_state_display_results_choose_an_answer(
    get_current_datetime, tester: AppTester, rapidpro_mock
):
    get_current_datetime.return_value = datetime(2022, 6, 19, 17, 30)
    tester.setup_state("state_display_results")

    await tester.user_input("AAQ Title #1")

    tester.assert_state("state_display_content")

    assert len(rapidpro_mock.app.requests) == 1
    request = rapidpro_mock.app.requests[0]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {
            "next_aaq_timeout_time": "2022-06-19T17:35:00",
            "aaq_timeout_type": "2",
        },
    }


@pytest.mark.asyncio
async def test_state_display_results_no_match(tester: AppTester, rapidpro_mock):
    tester.setup_state("state_display_results")

    await tester.user_input("None of these help")

    tester.assert_state("state_start")

    assert len(rapidpro_mock.app.requests) == 1
    request = rapidpro_mock.app.requests[0]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {"aaq_timeout_type": ""},
    }

    tester.assert_num_messages(1)
    tester.assert_message("TODO: Handle question not answered")


@pytest.mark.asyncio
async def test_state_display_content_question_answered(
    tester: AppTester, rapidpro_mock
):
    tester.setup_state("state_display_content")

    await tester.user_input("Yes")

    tester.assert_state("state_start")

    assert len(rapidpro_mock.app.requests) == 1
    request = rapidpro_mock.app.requests[0]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {"aaq_timeout_type": ""},
    }

    tester.assert_num_messages(1)
    tester.assert_message(
        "🙍🏾‍♀️*So glad I could help! If you have another question, "
        "you know what to do!* 😉"
    )


@pytest.mark.asyncio
async def test_state_display_content_question_not_answered(
    tester: AppTester, rapidpro_mock
):
    tester.setup_state("state_display_content")

    await tester.user_input("No")

    tester.assert_state("state_start")

    assert len(rapidpro_mock.app.requests) == 1
    request = rapidpro_mock.app.requests[0]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {"aaq_timeout_type": ""},
    }

    tester.assert_num_messages(1)
    tester.assert_message("TODO: Handle question not answered")


@pytest.mark.asyncio
async def test_state_handle_timeout_handles_type_1_yes(
    tester: AppTester, rapidpro_mock
):
    tester.setup_state("state_handle_timeout_response")
    await tester.user_input(session=Message.SESSION_EVENT.NEW, content="yes ask again")

    assert len(rapidpro_mock.app.requests) == 2
    request = rapidpro_mock.app.requests[1]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {"aaq_timeout_sent": "", "aaq_timeout_type": ""},
    }

    tester.assert_state("state_aaq_start")


@pytest.mark.asyncio
async def test_state_handle_timeout_handles_type_1_no(tester: AppTester, rapidpro_mock):
    tester.setup_state("state_handle_timeout_response")
    await tester.user_input(session=Message.SESSION_EVENT.NEW, content="no, I'm good")

    assert len(rapidpro_mock.app.requests) == 2
    request = rapidpro_mock.app.requests[1]
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

    assert len(rapidpro_mock.app.requests) == 2
    request = rapidpro_mock.app.requests[1]
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

    assert len(rapidpro_mock.app.requests) == 2
    request = rapidpro_mock.app.requests[1]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {"aaq_timeout_sent": "", "aaq_timeout_type": ""},
    }

    tester.assert_state("state_start")

    tester.assert_num_messages(1)
    tester.assert_message("TODO: Handle question not answered")
