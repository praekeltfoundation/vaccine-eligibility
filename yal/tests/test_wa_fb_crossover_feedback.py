import json
from datetime import datetime, timedelta

import pytest
from sanic import Sanic, response

from vaccine.testing import AppTester, TState, run_sanic
from yal import config
from yal.utils import BACK_TO_MAIN, GET_HELP
from yal.wa_fb_crossover_feedback import Application


@pytest.fixture
def tester():
    return AppTester(Application)


def get_rapidpro_contact(urn):
    contact = {
        "uuid": "b733e997-b0b4-4d4d-a3ad-0546e1644aa9",
        "name": "Test Human",
        "language": "eng",
        "groups": [],
        "fields": {},
        "blocked": False,
        "stopped": False,
        "created_on": "2015-11-11T08:30:24.922024+00:00",
        "modified_on": "2015-11-11T08:30:25.525936+00:00",
        "urns": [urn],
    }
    if urn == "whatsapp:27820001001":
        contact["fields"] = {
            "last_mainmenu_time": f"{datetime.now()-timedelta(days=2)}"
        }
    return contact


@pytest.fixture
async def rapidpro_mock():
    Sanic.test_mode = True
    app = Sanic("mock_rapidpro")
    tstate = TState()

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
async def test_state_not_saw_recent_facebook(tester: AppTester, rapidpro_mock):
    tester.setup_state("state_wa_fb_crossover_feedback")
    await tester.user_input("No, I didn't")
    tester.assert_state(None)
    assert len(rapidpro_mock.tstate.requests) == 1
    assert [r.path for r in rapidpro_mock.tstate.requests] == ["/api/v2/contacts.json"]

    post_request = rapidpro_mock.tstate.requests[0]

    engaged_on_facebook = json.loads(post_request.body.decode("utf-8"))["fields"][
        "engaged_on_facebook"
    ]

    assert engaged_on_facebook is False


@pytest.mark.asyncio
async def test_state_saw_recent_facebook(tester: AppTester, rapidpro_mock):
    tester.setup_state("state_wa_fb_crossover_feedback")
    await tester.user_input("Yes, I did")
    tester.assert_state("state_saw_recent_facebook")
    tester.assert_message(
        f"""I thought it was so interesting 💡

What did you think?

_Click on the button below and choose an option_

1. It was helpful
2. Learnt something new
3. I enjoy the comments
4. Other

--

{BACK_TO_MAIN}
{GET_HELP}"""
    )
    assert len(rapidpro_mock.tstate.requests) == 1
    assert [r.path for r in rapidpro_mock.tstate.requests] == ["/api/v2/contacts.json"]

    post_request = rapidpro_mock.tstate.requests[0]

    engaged_on_facebook = json.loads(post_request.body.decode("utf-8"))["fields"][
        "engaged_on_facebook"
    ]

    assert engaged_on_facebook is True


@pytest.mark.asyncio
async def test_state_fb_hot_topic_helpful(tester: AppTester, rapidpro_mock):
    tester.setup_state("state_saw_recent_facebook")
    await tester.user_input("It was helpful")
    assert tester.application.answer_events[0].response == "helpful"
    tester.assert_state("state_fb_hot_topic_helpful")


@pytest.mark.asyncio
async def test_state_fb_hot_topic_helpful_learnt_new(tester: AppTester, rapidpro_mock):
    tester.setup_state("state_saw_recent_facebook")
    await tester.user_input("Learnt something new")
    assert tester.application.answer_events[0].response == "learnt new"
    tester.assert_state("state_fb_hot_topic_helpful")


@pytest.mark.asyncio
async def test_state_fb_hot_topic_enjoyed_comments(tester: AppTester, rapidpro_mock):
    tester.setup_state("state_saw_recent_facebook")
    await tester.user_input("I enjoy the comments")
    assert tester.application.answer_events[0].response == "enjoyed comments"
    tester.assert_state("state_fb_hot_topic_enjoyed_comments")


@pytest.mark.asyncio
async def test_state_fb_hot_topic_other(tester: AppTester, rapidpro_mock):
    tester.setup_state("state_saw_recent_facebook")
    await tester.user_input("Other")
    assert tester.application.answer_events[0].response == "other"
    tester.assert_state("state_fb_hot_topic_other")
    tester.assert_message(
        f"""I'd love to hear what you think of the topic. Please share your thoughts!

_Just type and send your reply_

--
*Or reply*
{BACK_TO_MAIN}
{GET_HELP}"""
    )


@pytest.mark.asyncio
async def test_state_fb_hot_topic_thanks_for_feedback(tester: AppTester, rapidpro_mock):
    tester.setup_state("state_fb_hot_topic_other")
    await tester.user_input("The article was boring")
    tester.assert_state("state_fb_hot_topic_thanks_for_feedback")
