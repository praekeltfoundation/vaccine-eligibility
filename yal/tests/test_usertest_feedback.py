import json

import pytest
from sanic import Sanic, response

from vaccine.testing import AppTester
from yal import config
from yal.main import Application


@pytest.fixture
def tester():
    return AppTester(Application)


def get_rapidpro_contact(urn):
    print(urn)
    status = {
        "whatsapp:27820001001": "PENDING",
        "whatsapp:27820001002": "TRUE",
    }
    return {
        "uuid": "b733e997-b0b4-4d4d-a3ad-0546e1644aa9",
        "name": "",
        "language": "eng",
        "groups": [],
        "fields": {
            "usertesting_feedback_complete": status.get(urn),
        },
        "blocked": False,
        "stopped": False,
        "created_on": "2015-11-11T08:30:24.922024+00:00",
        "modified_on": "2015-11-11T08:30:25.525936+00:00",
        "urns": [urn],
    }


@pytest.fixture
async def rapidpro_mock(sanic_client):
    Sanic.test_mode = True
    app = Sanic("mock_rapidpro")
    app.requests = []
    app.errors = 0
    app.errormax = 0

    @app.route("/api/v2/contacts.json", methods=["GET"])
    def get_contact(request):
        app.requests.append(request)
        if app.errormax:
            if app.errors < app.errormax:
                app.errors += 1
                return response.json({}, status=500)

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
async def test_state_check_feedback_completed(tester: AppTester, rapidpro_mock):
    tester.setup_user_address("27820001002")
    await tester.user_input("feedback")

    tester.assert_state("state_start")

    tester.assert_message("Thanks, you have already completed this survey.")


@pytest.mark.asyncio
async def test_state_check_feedback_not_part(tester: AppTester, rapidpro_mock):
    tester.setup_user_address("27820001003")
    await tester.user_input("feedback")

    tester.assert_state("state_start")

    tester.assert_message(
        "\n".join(
            [
                "👩🏾 *Howzit! Welcome to B-Wise by Young Africa Live!*",
                "",
                "If you're looking for answers to questions about bodies, sex, "
                "relationships and health, please reply with the word *HI*.",
            ]
        )
    )


@pytest.mark.asyncio
async def test_state_feedback_pleasecallme(tester: AppTester, rapidpro_mock):
    await tester.user_input("feedback")

    tester.assert_state("state_feedback_pleasecallme")

    tester.assert_message(
        "\n".join(
            [
                "Now that you've gone though our service, how would your rate your "
                "experience using the *Please Call Me feature?*",
                "",
                "*1* - Excellent",
                "*2* - Good",
                "*3* - Ok",
                "*4* - Not so good",
                "*5* - Really bad",
                "",
                "*6* - Skip",
            ]
        )
    )


@pytest.mark.asyncio
async def test_state_feedback_servicefinder(tester: AppTester, rapidpro_mock):
    tester.setup_state("state_feedback_pleasecallme")
    await tester.user_input("1")

    tester.assert_state("state_feedback_servicefinder")

    tester.assert_message(
        "\n".join(
            [
                "How would your rate your experience using the *Service Finder?*",
                "",
                "*1* - Excellent",
                "*2* - Good",
                "*3* - Ok",
                "*4* - Not so good",
                "*5* - Really bad",
                "",
                "*6* - Skip",
            ]
        )
    )


@pytest.mark.asyncio
async def test_state_feedback_changepreferences(tester: AppTester, rapidpro_mock):
    tester.setup_state("state_feedback_servicefinder")
    await tester.user_input("1")

    tester.assert_state("state_feedback_changepreferences")

    tester.assert_message(
        "\n".join(
            [
                "How would your rate your experience using the *Settings (updating "
                "your profile etc)?*",
                "",
                "*1* - Excellent",
                "*2* - Good",
                "*3* - Ok",
                "*4* - Not so good",
                "*5* - Really bad",
                "",
                "*6* - Skip",
            ]
        )
    )


@pytest.mark.asyncio
async def test_state_feedback_askaquestion(tester: AppTester, rapidpro_mock):
    tester.setup_state("state_feedback_changepreferences")
    await tester.user_input("1")

    tester.assert_state("state_feedback_askaquestion")

    tester.assert_message(
        "\n".join(
            [
                "How would your rate your experience using the *Ask a Question "
                "service?*",
                "",
                "*1* - Excellent",
                "*2* - Good",
                "*3* - Ok",
                "*4* - Not so good",
                "*5* - Really bad",
                "",
                "*6* - Skip",
            ]
        )
    )


@pytest.mark.asyncio
async def test_state_feedback_quickreply(tester: AppTester, rapidpro_mock):
    tester.setup_state("state_feedback_askaquestion")
    await tester.user_input("1")

    tester.assert_state("state_feedback_quickreply")

    tester.assert_message(
        "\n".join(
            [
                "How easy was it to get the information you were looking for using "
                "the *Quick Reply Button?*",
                "",
                "*1* - Excellent",
                "*2* - Good",
                "*3* - Ok",
                "*4* - Not so good",
                "*5* - Really bad",
                "",
                "*6* - Skip",
            ]
        )
    )


@pytest.mark.asyncio
async def test_state_feedback_numberskeywords(tester: AppTester, rapidpro_mock):
    tester.setup_state("state_feedback_quickreply")
    await tester.user_input("1")

    tester.assert_state("state_feedback_numberskeywords")

    tester.assert_message(
        "\n".join(
            [
                "How easy was it to get the information you were looking for *the "
                "numbers and keywords?*",
                "",
                "*1* - Excellent",
                "*2* - Good",
                "*3* - Ok",
                "*4* - Not so good",
                "*5* - Really bad",
                "",
                "*6* - Skip",
            ]
        )
    )


@pytest.mark.asyncio
async def test_state_feedback_usefulinformation(tester: AppTester, rapidpro_mock):
    tester.setup_state("state_feedback_numberskeywords")
    await tester.user_input("1")

    tester.assert_state("state_feedback_usefulinformation")

    tester.assert_message(
        "\n".join(
            [
                "How useful was the information you found?:",
                "",
                "*1* - Extremely useful",
                "*2* - Very useful",
                "*3* - Quite useful",
                "*4* - Not that useful",
                "*5* - Completely useless",
                "",
                "*6* - Skip",
            ]
        )
    )


@pytest.mark.asyncio
async def test_state_feedback_lookforinformation(tester: AppTester, rapidpro_mock):
    tester.setup_state("state_feedback_usefulinformation")
    await tester.user_input("1")

    tester.assert_state("state_feedback_lookforinformation")

    tester.assert_message(
        "\n".join(
            [
                "How likely are you to use this chatbot to look for information in "
                "the future?",
                "",
                "*1* - Extremely likely",
                "*2* - Very likely",
                "*3* - Quite likely",
                "*4* - Unlikely",
                "",
                "*5* - Skip",
            ]
        )
    )


@pytest.mark.asyncio
async def test_state_feedback_willreturn(tester: AppTester, rapidpro_mock):
    tester.setup_state("state_feedback_lookforinformation")
    await tester.user_input("1")

    tester.assert_state("state_feedback_willreturn")

    tester.assert_message(
        "\n".join(
            [
                "How often do you think you might use {Young Africa Live/BWise in "
                "the future?",
                "",
                "*1* - All the time",
                "*2* - Quite a lot",
                "*3* - Sometimes",
                "*4* - Not much",
                "*5* - Hardly ever",
                "",
                "*5* - Skip",
            ]
        )
    )


@pytest.mark.asyncio
async def test_state_submit_completed_feedback(tester: AppTester, rapidpro_mock):
    tester.setup_state("state_feedback_willreturn")
    await tester.user_input("1")

    tester.assert_state("state_start")

    tester.assert_message("Thank you for your feedback. Have a great day.")

    assert len(rapidpro_mock.app.requests) == 1
    request = rapidpro_mock.app.requests[0]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {"usertesting_feedback_complete": "TRUE"},
    }
