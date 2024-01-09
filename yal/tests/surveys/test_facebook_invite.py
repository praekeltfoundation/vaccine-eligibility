import json

import pytest
from sanic import Sanic, response

from vaccine.testing import AppTester, TState, run_sanic
from yal import config
from yal.main import Application


@pytest.fixture
def tester():
    return AppTester(Application)


@pytest.fixture(autouse=True)
async def rapidpro_mock():
    Sanic.test_mode = True
    app = Sanic("mock_rapidpro")
    tstate = TState()

    @app.route("/api/v2/contacts.json", methods=["POST"])
    def update_contact(request):
        tstate.requests.append(request)
        return response.json({}, status=200)

    @app.route("/api/v2/contacts.json", methods=["GET"])
    def get_contact(request):
        tstate.requests.append(request)
        if tstate.errormax:
            if tstate.errors < tstate.errormax:
                tstate.errors += 1
                return response.json({}, status=500)

        return response.json(
            {
                "results": [{"fields": tstate.contact_fields}],
                "next": None,
            },
            status=200,
        )

    async with run_sanic(app) as server:
        url = config.RAPIDPRO_URL
        config.RAPIDPRO_URL = f"http://{server.host}:{server.port}"
        config.RAPIDPRO_TOKEN = "testtoken"
        server.tstate = tstate
        yield server
        config.RAPIDPRO_URL = url


@pytest.mark.asyncio
async def test_facebook_invite_yes(tester: AppTester, rapidpro_mock):
    rapidpro_mock.tstate.contact_fields["onboarding_completed"] = True
    rapidpro_mock.tstate.contact_fields["terms_accepted"] = True
    rapidpro_mock.tstate.contact_fields["facebook_survey_invite_status"] = "sent"

    await tester.user_input("Yes, take part")
    tester.assert_state("state_facebook_member")

    tester.assert_message(
        "Great! Before we get started, have you been a member of the B-Wise Facebook "
        "page since before June 2023?"
    )

    request = rapidpro_mock.tstate.requests[1]

    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {
            "facebook_survey_invite_status": "responded_yes",
        }
    }


@pytest.mark.asyncio
async def test_facebook_invite_no(tester: AppTester, rapidpro_mock):
    rapidpro_mock.tstate.contact_fields["onboarding_completed"] = True
    rapidpro_mock.tstate.contact_fields["terms_accepted"] = True
    rapidpro_mock.tstate.contact_fields["facebook_survey_invite_status"] = "sent"

    await tester.user_input("No, thanks")
    tester.assert_state("state_start")

    tester.assert_message(
        "\n".join(
            [
                "That's completely okay! This won’t affect your experience on "
                "the B-Wise chatbot.",
                "",
                "Please enjoy the B-Wise tool and stay safe.",
            ]
        )
    )

    request = rapidpro_mock.tstate.requests[1]

    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {
            "facebook_survey_invite_status": "responded_no",
        }
    }


@pytest.mark.asyncio
async def test_facebook_invite_not_invited(tester: AppTester, rapidpro_mock):
    rapidpro_mock.tstate.contact_fields["onboarding_completed"] = True
    rapidpro_mock.tstate.contact_fields["terms_accepted"] = True

    await tester.user_input("Yes, take part")
    tester.assert_state("state_start")

    tester.assert_message(
        "\n".join(
            [
                "🤖 *Hey there — Welcome to B-Wise!*",
                "",
                "If you're looking for answers to questions about bodies, sex, "
                "relationships and health, please reply with the word *HI*.",
            ]
        )
    )

    assert len(rapidpro_mock.tstate.requests) == 1


@pytest.mark.asyncio
async def test_state_facebook_member_yes(tester: AppTester):
    tester.setup_state("state_facebook_member")

    await tester.user_input("Yes")

    tester.assert_state("state_start")

    tester.assert_message(
        "\n".join(
            [
                "Excellent! Thank you for being a valuable member of our Facebook "
                "community.",
                "",
                "To do the survey, click on the link below, answer the questions and "
                "you’re all done!",
                "",
                "https://docs.google.com/forms/d/e/1FAIpQLScjbZEbIjQXMDdHbJTUCjxYnbRVP4D2p6kXQy74tXrIN6Qwww/viewform?usp=sf_link",  # noqa: E501
            ]
        )
    )


@pytest.mark.asyncio
async def test_state_facebook_member_no(tester: AppTester):
    tester.setup_state("state_facebook_member")

    await tester.user_input("No")

    tester.assert_state("state_not_a_member")

    tester.assert_message(
        "Have you seen a post by B-Wise on your Facebook feed?", buttons=["Yes", "No"]
    )


@pytest.mark.asyncio
async def test_state_not_a_member_yes(tester: AppTester):
    tester.setup_state("state_not_a_member")

    await tester.user_input("Yes")

    tester.assert_state("state_start")

    tester.assert_message(
        "\n".join(
            [
                "That’s great! The B-Wise Facebook community is a great place for "
                "cheeky memes and thought-provoking posts.",
                "",
                "Now on to the survey! Click on the link below, answer the questions "
                "and you’re all done!",
                "",
                "https://docs.google.com/forms/d/e/1FAIpQLSe_YlROLiezkGFbdcK7HBA99ABrWvUcvZ20azvAEpQKHwr6kw/viewform?usp=sf_link",  # noqa: E501
            ]
        )
    )


@pytest.mark.asyncio
async def test_state_not_a_member_no(tester: AppTester):
    tester.setup_state("state_not_a_member")

    await tester.user_input("No")

    tester.assert_state("state_start")

    tester.assert_message(
        "\n".join(
            [
                "No sweat! We won’t ask you to do the survey though, since we are only "
                "looking for people who are members of the B-Wise "
                "Facebook community or who have seen B-Wise posts on Facebook.",
                "",
                "Please enjoy the B-Wise tool and stay safe.",
            ]
        )
    )
