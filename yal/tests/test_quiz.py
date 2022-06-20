import pytest
from sanic import Sanic, response

from vaccine.models import Message
from vaccine.testing import AppTester
from yal import config
from yal.main import Application


@pytest.fixture
def tester():
    return AppTester(Application)


@pytest.fixture
async def contentrepo_api_mock(sanic_client):
    Sanic.test_mode = True
    app = Sanic("contentrepo_api_mock")
    app.requests = []

    @app.route("/api/v2/pages", methods=["GET"])
    def get_pages(request):
        app.requests.append(request)
        tag = request.args.get("tag")

        pages = []
        if tag == "first_quiz_1":
            pages.append({"id": 1, "title": "Question 1"})
        if tag == "first_quiz_2":
            pages.append({"id": 4, "title": "Question 2"})
        if tag == "first_quiz_pass":
            pages.append({"id": 5, "title": "Quiz pass message"})

        child_of = request.args.get("child_of")
        if child_of in ["1"]:
            pages.append({"id": 2, "title": "Answer 1"})
            pages.append({"id": 3, "title": "Answer 2"})

        return response.json(
            {
                "count": len(pages),
                "results": pages,
            }
        )

    @app.route("/api/v2/pages/<page_id:int>", methods=["GET"])
    def get_page_detail(request, page_id):
        app.requests.append(request)

        title = "Question 1"
        body = "The body of question 1"
        tags = ["score_1"]
        if page_id == 2:
            body = "Answer 1"
        if page_id == 4:
            title = "Question 2"
            body = "The body of question 2"
            tags.extend(["quiz_end", "pass_percentage_90"])
        if page_id == 5:
            title = "Quiz pass message"
            body = "[SCORE] out of 2\nThe pass message for this quiz."

        return response.json(
            {
                "id": page_id,
                "title": title,
                "subtitle": "subtitle",
                "body": {
                    "message": page_id,
                    "total_messages": page_id,
                    "text": {
                        "type": "Whatsapp_Message",
                        "value": {"image": None, "message": body, "next_prompt": ""},
                        "id": "111b8f05-be1b-4461-ac85-562930747336",
                    },
                    "revision": page_id,
                },
                "tags": tags,
                "has_children": True,
                "meta": {"parent": {"id": 123, "title": "Parent Title"}},
            }
        )

    client = await sanic_client(app)
    url = config.CONTENTREPO_API_URL
    config.CONTENTREPO_API_URL = f"http://{client.host}:{client.port}"
    yield client
    config.CONTENTREPO_API_URL = url


@pytest.mark.asyncio
async def test_state_quiz_start(tester: AppTester, contentrepo_api_mock):
    tester.setup_state("state_quiz_start")

    tester.user.metadata["quiz_tag"] = "first_quiz"

    tester.user.session_id = 123

    await tester.user_input(session=Message.SESSION_EVENT.NEW)

    tester.assert_num_messages(1)
    tester.assert_message(
        "\n".join(
            [
                "*Question 1*",
                "subtitle",
                "-----",
                "",
                "The body of question 1",
                "",
                "1. Answer 1",
                "2. Answer 2",
                "",
                "-----",
                "*Or reply:*",
                "0. 🏠 Back to Main MENU",
                "# 🆘 Get HELP",
            ]
        )
    )

    await tester.user_input("1")

    [answer_msg, result_msg] = tester.fake_worker.outbound_messages
    assert answer_msg.content == "\n".join(
        [
            "Answer 1",
        ]
    )
    assert result_msg.content == "\n".join(
        [
            "1 out of 2\nThe pass message for this quiz.",
        ]
    )

    tester.assert_num_messages(1)
    tester.assert_message(
        "\n".join(
            [
                "*Question 2*",
                "subtitle",
                "-----",
                "",
                "The body of question 2",
                "",
                "1. Chat with a loveLife counsellor",
                "2. Not right now",
                "3. Redo Quiz",
                "",
                "-----",
                "*Or reply:*",
                "0. 🏠 Back to Main MENU",
                "# 🆘 Get HELP",
            ]
        )
    )
