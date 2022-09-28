import pytest
from sanic import Sanic, response

from vaccine import ask_a_question_config as config
from vaccine.ask_a_question import Application
from vaccine.models import Message
from vaccine.testing import AppTester, TState, run_sanic


@pytest.fixture
def tester():
    return AppTester(Application)


@pytest.fixture
async def model_mock():
    Sanic.test_mode = True
    app = Sanic("mock_model")
    tstate = TState()
    tstate.no_response = False

    @app.route("/inbound/check", methods=["POST"])
    def check(request):
        tstate.requests.append(request)
        if tstate.errormax:
            if tstate.errors < tstate.errormax:
                tstate.errors += 1
                return response.json({}, status=500)
        if tstate.no_response:
            return response.json({"top_responses": []})
        return response.file_stream(
            "vaccine/tests/aaq_model_response.json", mime_type="application/json"
        )

    @app.route("/inbound/feedback", methods=["POST"])
    def feedback(request):
        tstate.requests.append(request)
        if tstate.errormax:
            if tstate.errors < tstate.errormax:
                tstate.errors += 1
                return response.json({}, status=500)
        return response.json({})

    async with run_sanic(app) as server:
        url = config.MODEL_API_URL
        token = config.MODEL_API_TOKEN
        config.MODEL_API_URL = f"http://{server.host}:{server.port}"
        config.MODEL_API_TOKEN = "testtoken"
        server.tstate = tstate
        yield server
        config.MODEL_API_URL = url
        config.MODEL_API_TOKEN = token


@pytest.mark.asyncio
async def test_exit_keywords(tester: AppTester):
    await tester.user_input("menu")
    tester.assert_message("", session=Message.SESSION_EVENT.CLOSE)
    assert tester.application.messages[0].helper_metadata["automation_handle"] is True
    tester.assert_state(None)
    assert tester.user.answers == {}


@pytest.mark.asyncio
async def test_timeout(tester: AppTester):
    await tester.user_input(session=Message.SESSION_EVENT.CLOSE)
    tester.assert_message(
        "\n".join(
            [
                "❓ *YOUR VACCINE QUESTIONS*",
                "",
                "We haven’t heard from you in a while!",
                "",
                "The question session has timed out due to inactivity. You will "
                "need to start again. Just TYPE the word ASK.",
                "",
                "-----",
                "📌 Reply *0* to return to the main *MENU*",
            ]
        ),
        session=Message.SESSION_EVENT.CLOSE,
    )


@pytest.mark.asyncio
async def test_question(tester: AppTester, model_mock):
    await tester.user_input("ask", session=Message.SESSION_EVENT.NEW)
    tester.assert_message(
        "\n".join(
            [
                "❓ *ASK*  your questions about vaccines",
                "",
                "Try *typing your own question* or sharing/forwarding a '*rumour*' "
                "that's going around to get the facts!",
                "",
                '[💡Tip: Reply with a question like: _"Are vaccines safe?"_ ]',
            ]
        )
    )
    tester.assert_state("state_question")

    await tester.user_input("Is the vaccine safe?")
    tester.assert_state("state_display_response_choices")


@pytest.mark.asyncio
async def test_reset_keyword(tester: AppTester):
    tester.setup_state("state_no_responses")
    await tester.user_input("ask")
    tester.assert_state("state_question")


@pytest.mark.asyncio
async def test_display_response_choices(tester: AppTester, model_mock):
    tester.setup_state("state_question")
    await tester.user_input("Is the vaccine safe?")
    tester.assert_message(
        "\n".join(
            [
                "🔎 *Top Search Results*",
                "",
                "1. Are COVID-19 vaccines safe?",
                "2. Do vaccines work against COVID-19 variants?",
                "3. Do we know what's in the vaccines?",
                "",
                "[💡Tip: If you don't see what you're looking for, try typing your "
                "question again using different words or reply *FAQ* to browse topics]",
            ]
        )
    )
    tester.assert_state("state_display_response_choices")
    [req] = model_mock.tstate.requests
    req_data = req.json
    req_data["metadata"].pop("message_id")
    assert req_data == {
        "text_to_match": "Is the vaccine safe?",
        "metadata": {"whatsapp_id": "27820001001"},
    }


@pytest.mark.asyncio
async def test_display_response_choices_reask_question(tester: AppTester, model_mock):
    with open("vaccine/tests/aaq_model_response.json") as f:
        tester.setup_answer("model_response", f.read())
    tester.setup_state("state_display_response_choices")

    await tester.user_input("Does the vaccine contain covid?")
    tester.assert_state("state_display_response_choices")
    assert len(model_mock.tstate.requests) == 1
    tester.assert_answer("state_question", "Does the vaccine contain covid?")


@pytest.mark.asyncio
async def test_model_api_temporary_error(tester: AppTester, model_mock):
    model_mock.tstate.errormax = 1
    tester.setup_state("state_question")
    await tester.user_input("Is the vaccine safe?")
    tester.assert_state("state_display_response_choices")
    assert len(model_mock.tstate.requests) == 2


@pytest.mark.asyncio
async def test_model_api_permanent_error(tester: AppTester, model_mock):
    model_mock.tstate.errormax = 5
    tester.setup_state("state_question")
    await tester.user_input("Is the vaccine safe?")
    assert len(model_mock.tstate.requests) == 3
    tester.assert_message(
        "Something went wrong, your question was not able to be processed. "
        "Please try again later"
    )


@pytest.mark.asyncio
async def test_model_no_responses(tester: AppTester, model_mock):
    model_mock.tstate.no_response = True
    tester.setup_state("state_question")
    await tester.user_input("Is the vaccine safe?")
    tester.assert_message(
        "\n".join(
            [
                "*No Results Found*",
                "",
                "[💡Tip: Try typing your question again using different words or reply "
                "*FAQ* to browse topics]",
            ]
        )
    )
    tester.assert_state("state_no_responses")


@pytest.mark.asyncio
async def test_new_question_on_no_response(tester: AppTester, model_mock):
    tester.setup_state("state_no_responses")
    await tester.user_input("Is the vaccine safe?")
    tester.assert_state("state_display_response_choices")
    tester.assert_answer("state_question", "Is the vaccine safe?")


@pytest.mark.asyncio
async def test_display_selected_choice(tester: AppTester, model_mock):
    with open("vaccine/tests/aaq_model_response.json") as f:
        tester.setup_answer("model_response", f.read())

    tester.setup_state("state_display_response_choices")
    await tester.user_input("1")
    tester.assert_state("state_display_selected_choice")
    tester.assert_message(
        "\n".join(
            [
                "Yes, COVID-19 vaccines are safe. No step in the development, testing "
                "or regulation process has been skipped for these vaccines.\r",
                "\r",
                "When they are developed, all vaccines are thoroughly tested to make "
                "sure they are safe and work well.\r",
                "\r",
                "Every vaccine also needs to be approved by the medical regulators in "
                "each country to make sure that they are safe.\r",
                "\r",
                "Watch: youtu.be/AeSSyjhz8Hk",
            ]
        )
    )

    await tester.user_input("yes")
    [r1, r2] = model_mock.tstate.requests
    assert r1.json == {
        "feedback": {"choice": "Are COVID-19 vaccines safe?"},
        "feedback_secret_key": "testsecretkey",
        "inbound_id": 66,
    }
    assert r2.json == {
        "feedback": {"choice": "Are COVID-19 vaccines safe?", "feedback": "yes"},
        "feedback_secret_key": "testsecretkey",
        "inbound_id": 66,
    }


@pytest.mark.asyncio
async def test_display_selected_choice_no_feedback(tester: AppTester, model_mock):
    with open("vaccine/tests/aaq_model_response.json") as f:
        tester.setup_answer("model_response", f.read())

    tester.setup_state("state_display_response_choices")
    await tester.user_input("1")
    tester.assert_state("state_display_selected_choice")
    await tester.user_input("no")
    [r1, r2] = model_mock.tstate.requests
    assert r1.json == {
        "feedback": {"choice": "Are COVID-19 vaccines safe?"},
        "feedback_secret_key": "testsecretkey",
        "inbound_id": 66,
    }
    assert r2.json == {
        "feedback": {"choice": "Are COVID-19 vaccines safe?", "feedback": "no"},
        "feedback_secret_key": "testsecretkey",
        "inbound_id": 66,
    }
    tester.assert_state("state_another_result")
    tester.assert_message(
        "\n".join(
            [
                "Thank you for confirming.",
                "",
                "Try a different result?",
                "1. Are COVID-19 vaccines safe?",
                "2. Do vaccines work against COVID-19 variants?",
                "3. Do we know what's in the vaccines?",
                "",
                "-----",
                "Reply:",
                "❓ *ASK* to ask more vaccine questions",
                "📌 *0* for the main *MENU*",
            ]
        )
    )
    await tester.user_input("2")
    tester.assert_state("state_display_selected_choice")
    tester.assert_answer(
        "state_display_response_choices", "Do vaccines work against COVID-19 variants?"
    )


@pytest.mark.asyncio
async def test_display_selected_choice_temporary_error(tester: AppTester, model_mock):
    with open("vaccine/tests/aaq_model_response.json") as f:
        tester.setup_answer("model_response", f.read())

    tester.setup_answer("state_display_response_choices", "Is the vaccine safe?")
    model_mock.tstate.errormax = 1
    tester.setup_state("state_display_selected_choice")
    await tester.user_input("1")
    assert len(model_mock.tstate.requests) == 2


@pytest.mark.asyncio
async def test_display_selected_choice_permanent_error(tester: AppTester, model_mock):
    with open("vaccine/tests/aaq_model_response.json") as f:
        tester.setup_answer("model_response", f.read())

    tester.setup_answer("state_display_response_choices", "Is the vaccine safe?")
    model_mock.tstate.errormax = 5
    tester.setup_state("state_display_selected_choice")
    await tester.user_input("1")
    assert len(model_mock.tstate.requests) == 3
    tester.assert_message(
        "Something went wrong, your question was not able to be processed. "
        "Please try again later"
    )


@pytest.mark.asyncio
async def test_state_end(tester: AppTester, model_mock):
    with open("vaccine/tests/aaq_model_response.json") as f:
        tester.setup_answer("model_response", f.read())

    tester.setup_answer("state_display_response_choices", "Is the vaccine safe?")
    tester.setup_state("state_display_selected_choice")
    await tester.user_input("1")

    tester.assert_message(
        "\n".join(
            [
                "Thank you for confirming.",
                "",
                "-----",
                "Reply:",
                "❓ *ASK* to ask more vaccine questions",
                "📌 *0* for the main *MENU*",
            ]
        ),
        session=Message.SESSION_EVENT.CLOSE,
    )
