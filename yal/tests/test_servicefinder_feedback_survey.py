from vaccine.testing import AppTester
from yal.servicefinder_feedback_survey import ServiceFinderFeedbackSurveyApplication
import pytest
from sanic import Sanic, response
from vaccine.testing import TState, run_sanic, MockServer
from vaccine.models import Message
from yal import config
from unittest import mock
from datetime import datetime


@pytest.fixture
def tester():
    return AppTester(ServiceFinderFeedbackSurveyApplication)

@pytest.fixture
async def rapidpro_mock():
    Sanic.test_mode = True
    app = Sanic("mock_rapidpro")
    tstate = TState()

    @app.route("/api/v2/contacts.json", methods=["GET"])
    def get_contact(request):
        tstate.requests.append(request)
        return response.json({"results": [{"fields": {"feedback_timestamp": "2022-03-04T05:06:07"}}]}, status=200)

    @app.route("/api/v2/contacts.json", methods=["POST"])
    def update_contact(request):
        tstate.requests.append(request)
        return response.json({}, status=200)

    async with run_sanic(app) as server:
        rapidpro_url = config.RAPIDPRO_URL
        config.RAPIDPRO_URL = f"http://{server.host}:{server.port}"
        server.tstate = tstate
        yield server
        config.RAPIDPRO_URL = rapidpro_url

@pytest.mark.asyncio
async def test_state_process_servicefinder_feedback_trigger(tester: AppTester, rapidpro_mock: MockServer):
    await tester.user_input(session=Message.SESSION_EVENT.NEW)
    tester.assert_state("state_process_servicefinder_feedback_trigger")
    [request] = rapidpro_mock.tstate.requests
    assert request.json["fields"] == {"feedback_survey_sent": ""}

@pytest.mark.asyncio
async def test_state_servicefinder_positive_feedback(tester: AppTester):
    tester.setup_state("state_process_servicefinder_feedback_trigger")
    await tester.user_input("yes, thanks")
    tester.assert_state("state_servicefinder_positive_feedback")

@pytest.mark.asyncio
async def test_state_servicefinder_negative_feedback(tester: AppTester):
    tester.setup_state("state_process_servicefinder_feedback_trigger")
    await tester.user_input("no, not helpful")
    tester.assert_state("state_servicefinder_negative_feedback")

@pytest.mark.asyncio
async def test_state_servicefinder_already_know_feedback(tester: AppTester):
    tester.setup_state("state_process_servicefinder_feedback_trigger")
    await tester.user_input("i knew this before")
    tester.assert_state("state_servicefinder_already_know_feedback")

@pytest.mark.asyncio
@mock.patch("yal.servicefinder_feedback_survey.utils.get_current_datetime")
async def test_state_servicefinder_feedback_confirmation(get_current_datetime: mock.MagicMock, tester: AppTester, rapidpro_mock: MockServer):
    get_current_datetime.return_value = datetime(2022, 1, 2, 3, 4, 5)
    tester.setup_state("state_servicefinder_positive_feedback")
    await tester.user_input("example feedback")
    tester.assert_state("state_servicefinder_feedback_confirmation")

    tester.setup_state("state_servicefinder_negative_feedback")
    await tester.user_input("example feedback")
    tester.assert_state("state_servicefinder_feedback_confirmation")

    # only positive feedback should trigger the second callback, so only one request
    [request] = rapidpro_mock.tstate.requests
    assert request.json["fields"] == {"feedback_timestamp": "2022-01-16T03:04:05", "feedback_type": "servicefinder_2"}

@pytest.mark.asyncio
async def test_state_went_to_service(tester: AppTester, rapidpro_mock: MockServer):
    tester.setup_state("state_servicefinder_feedback_survey_2_start")
    await tester.user_input("yes, i went")
    tester.assert_state("state_went_to_service")
    assert len(rapidpro_mock.tstate.requests) == 1

@pytest.mark.asyncio
async def test_state_did_not_go_to_service(tester: AppTester, rapidpro_mock: MockServer):
    tester.setup_state("state_servicefinder_feedback_survey_2_start")
    await tester.user_input("no, i didn't go")
    tester.assert_state("state_did_not_go_to_service")
    assert len(rapidpro_mock.tstate.requests) == 1

@pytest.mark.asyncio
async def test_state_service_helped(tester: AppTester):
    tester.setup_state("state_went_to_service")
    await tester.user_input("they helped me")
    tester.assert_state("state_service_helped")

@pytest.mark.asyncio
async def test_state_service_no_help_needed(tester: AppTester):
    tester.setup_state("state_went_to_service")
    await tester.user_input("i didn't need help")
    tester.assert_state("state_service_no_help_needed")

@pytest.mark.asyncio
async def test_state_service_no_help(tester: AppTester):
    tester.setup_state("state_went_to_service")
    await tester.user_input("they didn't help me")
    tester.assert_state("state_service_no_help")

@pytest.mark.asyncio
async def test_state_have_information_needed(tester: AppTester):
    tester.setup_state("state_did_not_go_to_service")
    await tester.user_input("i still plan to go")
    tester.assert_state("state_have_information_needed")

@pytest.mark.asyncio
async def test_state_service_finder_offer_aaq(tester: AppTester):
    tester.setup_state("state_did_not_go_to_service")
    await tester.user_input("i got help somewhere else")
    tester.assert_state("state_service_finder_offer_aaq")

@pytest.mark.asyncio
async def test_state_service_finder_survey_complete(tester: AppTester):
    tester.setup_state("state_service_helped")
    await tester.user_input("yes, i have all the info i need")
    tester.assert_state("state_service_finder_survey_complete")

@pytest.mark.asyncio
async def test_state_service_finder_offer_aaq(tester: AppTester):
    tester.setup_state("state_service_helped")
    await tester.user_input("no, i don't know what to do")
    tester.assert_state("state_service_finder_offer_aaq")

@pytest.mark.asyncio
async def test_state_offer_appointment_tips(tester: AppTester):
    tester.setup_state("state_service_no_help_needed")
    await tester.user_input("good")
    tester.assert_state("state_offer_appointment_tips")

@pytest.mark.asyncio
async def test_state_offer_appointment_tips_bad_experience(tester: AppTester):
    tester.setup_state("state_service_no_help_needed")
    await tester.user_input("just ok")
    tester.assert_state("state_offer_appointment_tips_bad_experience")

@pytest.mark.asyncio
async def test_state_offer_clinic_finder(tester: AppTester):
    tester.setup_state("state_service_no_help")
    await tester.user_input("queue was too long")
    tester.assert_state("state_offer_clinic_finder")

@pytest.mark.asyncio
async def test_state_got_other_help(tester: AppTester):
    tester.setup_state("state_service_no_help")
    await tester.user_input("got other help")
    tester.assert_state("state_got_other_help")

@pytest.mark.asyncio
async def test_state_other_reason_for_no_service(tester: AppTester):
    tester.setup_state("state_service_no_help")
    await tester.user_input("another reason")
    tester.assert_state("state_other_reason_for_no_service")

@pytest.mark.asyncio
async def test_state_service_finder_survey_complete_2(tester: AppTester):
    tester.setup_state("state_have_information_needed")
    await tester.user_input("yes")
    tester.assert_state("state_service_finder_survey_complete_2")

@pytest.mark.asyncio
async def test_state_offer_aaq(tester: AppTester):
    tester.setup_state("state_have_information_needed")
    await tester.user_input("no")
    tester.assert_state("state_offer_aaq")

@pytest.mark.asyncio
async def test_state_service_finder_survey_complete_3(tester: AppTester):
    tester.setup_state("state_service_finder_offer_aaq")
    await tester.user_input("maybe later")
    tester.assert_state("state_service_finder_survey_complete_3")

@pytest.mark.asyncio
async def test_state_service_finder_survey_complete_4(tester: AppTester):
    tester.setup_state("state_offer_appointment_tips")
    await tester.user_input("no, thanks")
    tester.assert_state("state_service_finder_survey_complete_4")

@pytest.mark.asyncio
async def test_state_service_finder_survey_complete_5(tester: AppTester):
    tester.setup_state("state_got_other_help")
    await tester.user_input("yes, thanks")
    tester.assert_state("state_service_finder_survey_complete_5")
