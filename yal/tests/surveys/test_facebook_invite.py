import json
from unittest import mock

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
        if tstate.errormax and tstate.errors < tstate.errormax:
            tstate.errors += 1
            return response.json({}, status=500)

        return response.json(
            {
                "results": [{"fields": tstate.contact_fields}],
                "next": None,
            },
            status=200,
        )

    @app.route("/api/v2/globals.json", methods=["GET"])
    def get_global_value(request):
        tstate.requests.append(request)
        assert request.args.get("key") == "facebook_survey_status"

        return response.json(
            {
                "next": None,
                "previous": None,
                "results": [
                    {
                        "key": "Facebook Survey Status",
                        "name": "facebook_survey_status",
                        "value": tstate.globals["facebook_survey_status"],
                        "modified_on": "2023-05-30T07:34:06.216776Z",
                    }
                ],
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
async def test_facebook_invite_yes(tester: AppTester, rapidpro_mock):
    rapidpro_mock.tstate.contact_fields["onboarding_completed"] = True
    rapidpro_mock.tstate.contact_fields["terms_accepted"] = True
    rapidpro_mock.tstate.contact_fields["facebook_survey_invite_status"] = "sent"
    rapidpro_mock.tstate.globals["facebook_survey_status"] = "active"

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
async def test_facebook_invite_yes_study_inactive(tester: AppTester, rapidpro_mock):
    rapidpro_mock.tstate.contact_fields["onboarding_completed"] = True
    rapidpro_mock.tstate.contact_fields["terms_accepted"] = True
    rapidpro_mock.tstate.contact_fields["facebook_survey_invite_status"] = "sent"
    rapidpro_mock.tstate.globals["facebook_survey_status"] = "inactive"

    await tester.user_input("Yes, take part")
    tester.assert_state("state_facebook_study_not_active")

    tester.assert_message(
        "\n".join(
            [
                "Eish! It looks like you just missed the cut off for our survey. "
                "No worries, we get it, life happens!",
                "",
                "Stay tuned for more survey opportunities. We appreciate your "
                "enthusiasm and hope you can catch the next one.",
                "",
                "Go ahead and browse the menu or ask us a question.",
            ]
        )
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
async def test_state_facebook_member_yes_active(tester: AppTester, rapidpro_mock):
    tester.setup_state("state_facebook_member")
    rapidpro_mock.tstate.globals["facebook_survey_status"] = "active"

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
async def test_state_facebook_member_yes_survey_b_only(
    tester: AppTester, rapidpro_mock
):
    tester.setup_state("state_facebook_member")
    rapidpro_mock.tstate.globals["facebook_survey_status"] = "study_b_only"

    await tester.user_input("Yes")

    tester.assert_state("state_facebook_study_not_active")


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


@pytest.mark.asyncio
async def test_state_facebook_study_not_active_menu(
    tester: AppTester, contentrepo_api_mock
):
    tester.setup_state("state_facebook_study_not_active")

    await tester.user_input("Go to the menu")

    tester.assert_state("state_mainmenu")


@pytest.mark.asyncio
@mock.patch("yal.askaquestion.config")
async def test_state_facebook_study_not_active_aaq(mock_config, tester: AppTester):
    mock_config.AAQ_URL = "http://aaq-test.com"
    tester.setup_state("state_facebook_study_not_active")

    await tester.user_input("Ask a question")

    tester.assert_state("state_aaq_start")
