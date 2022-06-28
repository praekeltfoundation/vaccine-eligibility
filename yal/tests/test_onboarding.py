import json
from datetime import date
from unittest import mock

import pytest
from sanic import Sanic, response

from vaccine.testing import AppTester
from yal import config, turn
from yal.main import Application


@pytest.fixture
def tester():
    return AppTester(Application)


@pytest.fixture
async def turn_api_mock(sanic_client, tester):
    Sanic.test_mode = True
    app = Sanic("mock_turn_api")
    app.requests = []
    app.errors = 0
    app.errormax = 0

    @app.route("/v1/contacts/<msisdn:int>/profile", methods=["PATCH"])
    def callback(request, msisdn):
        app.requests.append(request)
        if app.errormax:
            if app.errors < app.errormax:
                app.errors += 1
                return response.json({}, status=500)
        return response.json({})

    client = await sanic_client(app)
    get_profile_url = turn.get_profile_url

    host = f"http://{client.host}:{client.port}"
    turn.get_profile_url = (
        lambda whatsapp_id: f"{host}/v1/contacts/{whatsapp_id}/profile"
    )

    yield client
    turn.get_profile_url = get_profile_url


@pytest.mark.asyncio
async def test_state_dob_full_valid(tester: AppTester):
    tester.setup_state("state_dob_full")

    await tester.user_input("1/1/2007")

    tester.assert_state("state_relationship_status")
    tester.assert_num_messages(1)

    tester.assert_answer("state_dob_year", "2007")
    tester.assert_answer("state_dob_month", "1")
    tester.assert_answer("state_dob_day", "1")
    tester.assert_answer("age", "15")


@pytest.mark.asyncio
async def test_state_dob_full_invalid(tester: AppTester):
    tester.setup_state("state_dob_full")

    await tester.user_input("1/1/20071")

    tester.assert_state("state_dob_year")
    tester.assert_num_messages(1)

    tester.assert_no_answer("state_dob_year")
    tester.assert_no_answer("state_dob_month")
    tester.assert_no_answer("state_dob_day")
    tester.assert_no_answer("age")


@pytest.mark.asyncio
async def test_state_dob_full_skip(tester: AppTester):
    tester.setup_state("state_dob_full")

    await tester.user_input("skip")

    tester.assert_state("state_relationship_status")
    tester.assert_num_messages(1)

    tester.assert_answer("state_dob_year", "skip")
    tester.assert_answer("state_dob_month", "skip")
    tester.assert_answer("state_dob_day", "skip")
    tester.assert_no_answer("age")


@pytest.mark.asyncio
async def test_state_dob_year_valid(tester: AppTester):
    tester.setup_state("state_dob_year")

    await tester.user_input("2007")

    tester.assert_state("state_dob_month")
    tester.assert_num_messages(1)

    tester.assert_answer("state_dob_year", "2007")


@pytest.mark.asyncio
async def test_state_dob_year_invalid(tester: AppTester):
    tester.setup_state("state_dob_year")

    await tester.user_input("12007")

    tester.assert_state("state_dob_year")
    tester.assert_num_messages(1)

    tester.assert_no_answer("state_dob_year")


@pytest.mark.asyncio
async def test_state_dob_month_valid(tester: AppTester):
    tester.setup_state("state_dob_month")
    tester.setup_answer("state_dob_year", "2022")

    await tester.user_input("2")

    tester.assert_state("state_dob_day")
    tester.assert_num_messages(1)

    tester.assert_answer("state_dob_month", "2")


@pytest.mark.asyncio
async def test_state_dob_month_invalid(tester: AppTester):
    tester.setup_state("state_dob_month")
    tester.setup_answer("state_dob_year", "2022")

    await tester.user_input("22")

    tester.assert_state("state_dob_month")
    tester.assert_num_messages(1)

    tester.assert_no_answer("state_dob_month")


@pytest.mark.asyncio
async def test_state_dob_month_skip(tester: AppTester):
    tester.setup_state("state_dob_month")
    tester.setup_answer("state_dob_year", "2022")

    await tester.user_input("skip")

    tester.assert_state("state_dob_day")
    tester.assert_num_messages(1)

    tester.assert_answer("state_dob_month", "skip")


@pytest.mark.asyncio
async def test_state_dob_day_valid(tester: AppTester):
    tester.setup_state("state_dob_day")

    tester.setup_answer("state_dob_year", "2022")
    tester.setup_answer("state_dob_month", "2")

    await tester.user_input("2")

    tester.assert_state("state_relationship_status")
    tester.assert_num_messages(1)

    tester.assert_answer("state_dob_day", "2")


@pytest.mark.asyncio
async def test_state_dob_day_valid_no_year(tester: AppTester):
    tester.setup_state("state_dob_day")

    tester.setup_answer("state_dob_year", "skip")
    tester.setup_answer("state_dob_month", "2")

    await tester.user_input("2")

    tester.assert_state("state_relationship_status")
    tester.assert_num_messages(1)

    tester.assert_answer("state_dob_day", "2")


@pytest.mark.asyncio
async def test_state_dob_day_invalid(tester: AppTester):
    tester.setup_state("state_dob_day")

    tester.setup_answer("state_dob_year", "skip")
    tester.setup_answer("state_dob_month", "2")

    await tester.user_input("200")

    tester.assert_state("state_dob_day")
    tester.assert_num_messages(1)

    tester.assert_no_answer("state_dob_day")


@pytest.mark.asyncio
async def test_state_dob_day_invalid_date(tester: AppTester):
    tester.setup_state("state_dob_day")

    tester.setup_answer("state_dob_year", "2022")
    tester.setup_answer("state_dob_month", "9")

    await tester.user_input("31")

    tester.assert_state("state_dob_day")
    tester.assert_num_messages(1)

    tester.assert_no_answer("state_dob_day")


@pytest.mark.asyncio
async def test_state_dob_day_skip(tester: AppTester):
    tester.setup_state("state_dob_day")

    tester.setup_answer("state_dob_year", "2022")
    tester.setup_answer("state_dob_month", "2")

    await tester.user_input("skip")

    tester.assert_state("state_relationship_status")
    tester.assert_num_messages(1)

    tester.assert_answer("state_dob_day", "skip")


@pytest.mark.asyncio
@mock.patch("yal.onboarding.get_today")
async def test_state_check_birthday(get_today, tester: AppTester):
    get_today.return_value = date(2022, 2, 22)
    config.CONTENTREPO_API_URL = "https://contenrepo/"
    tester.setup_state("state_dob_day")

    tester.setup_answer("state_dob_month", "2")
    tester.setup_answer("state_dob_year", "2005")

    await tester.user_input("22")

    tester.assert_state("state_relationship_status")
    tester.assert_num_messages(1)

    tester.assert_answer("state_dob_day", "22")
    tester.assert_answer("age", "17")

    [msg] = tester.fake_worker.outbound_messages
    assert msg.content == "\n".join(
        [
            "*Yoh! 17 today? HAPPY BIRTHDAY!* 🎂 🎉 ",
            "",
            "Hope you're having a great one so far! Remember—age is "
            "just a number. Here's to always having  wisdom that goes"
            " beyond your years 😉 🥂",
        ]
    )
    assert msg.helper_metadata == {
        "image": "https://contenrepo/media/original_images/hbd.png"
    }


@pytest.mark.asyncio
@mock.patch("yal.onboarding.get_today")
async def test_state_check_birthday_skip_day(get_today, tester: AppTester):
    get_today.return_value = date(2022, 2, 22)
    tester.setup_state("state_dob_day")

    tester.setup_answer("state_dob_month", "2")
    tester.setup_answer("state_dob_year", "2007")

    await tester.user_input("skip")
    tester.assert_no_answer("age")

    tester.assert_state("state_relationship_status")
    tester.assert_num_messages(1)
    assert tester.fake_worker.outbound_messages == []


@pytest.mark.asyncio
@mock.patch("yal.onboarding.get_today")
async def test_state_check_birthday_skip_month(get_today, tester: AppTester):
    get_today.return_value = date(2022, 2, 22)
    tester.setup_state("state_dob_day")

    tester.setup_answer("state_dob_month", "skip")
    tester.setup_answer("state_dob_year", "2007")

    await tester.user_input("22")
    tester.assert_no_answer("age")

    tester.assert_state("state_relationship_status")
    tester.assert_num_messages(1)
    assert tester.fake_worker.outbound_messages == []


@pytest.mark.asyncio
@mock.patch("yal.onboarding.get_today")
async def test_state_check_birthday_skip_year(get_today, tester: AppTester):
    get_today.return_value = date(2022, 2, 22)
    config.CONTENTREPO_API_URL = "https://contenrepo/"
    tester.setup_state("state_dob_day")

    tester.setup_answer("state_dob_month", "2")
    tester.setup_answer("state_dob_year", "skip")

    await tester.user_input("22")

    tester.assert_state("state_relationship_status")
    tester.assert_num_messages(1)

    tester.assert_no_answer("age")

    [msg] = tester.fake_worker.outbound_messages
    assert msg.content == "\n".join(
        [
            "*Yoh! HAPPY BIRTHDAY!* 🎂 🎉 ",
            "",
            "Hope you're having a great one so far! Remember—age is "
            "just a number. Here's to always having  wisdom that goes"
            " beyond your years 😉 🥂",
        ]
    )
    assert msg.helper_metadata == {
        "image": "https://contenrepo/media/original_images/hbd.png"
    }


@pytest.mark.asyncio
async def test_state_relationship_status_valid(tester: AppTester):
    tester.setup_state("state_relationship_status")

    await tester.user_input("2")

    tester.assert_state("state_province")
    tester.assert_num_messages(1)

    tester.assert_answer("state_relationship_status", "complicated")


@pytest.mark.asyncio
async def test_state_full_address_invalid(tester: AppTester):
    tester.setup_answer("age", "22")
    tester.setup_state("state_full_address")

    await tester.user_input("2 test street \n test suburb")

    tester.assert_state("state_suburb")


@pytest.mark.asyncio
async def test_state_full_address_valid(tester: AppTester):
    tester.setup_answer("age", "22")
    tester.setup_state("state_full_address")

    await tester.user_input("2\ntest street\n test suburb")

    tester.assert_state("state_gender")


@pytest.mark.asyncio
async def test_state_full_address_minor(tester: AppTester):
    tester.setup_answer("age", "17")
    tester.setup_state("state_province")

    await tester.user_input("2")

    tester.assert_state("state_gender")


@pytest.mark.asyncio
async def test_state_gender_valid(tester: AppTester):
    tester.setup_state("state_gender")

    await tester.user_input("9")

    tester.assert_state("state_name_gender")
    tester.assert_num_messages(1)

    tester.assert_answer("state_gender", "other")


@pytest.mark.asyncio
async def test_submit_onboarding(tester: AppTester, turn_api_mock):
    tester.setup_state("state_name_gender")

    tester.setup_answer("state_dob_month", "2")
    tester.setup_answer("state_dob_day", "22")
    tester.setup_answer("state_dob_year", "2007")
    tester.setup_answer("state_relationship_status", "yes")
    tester.setup_answer("state_gender", "other")
    tester.setup_answer("state_name_gender", "new gender")
    tester.setup_answer("state_province", "FS")
    tester.setup_answer("state_suburb", "SomeSuburb")
    tester.setup_answer("state_street_name", "Good street")
    tester.setup_answer("state_street_number", "12")

    await tester.user_input("new gender")

    tester.assert_state("state_onboarding_complete")
    tester.assert_num_messages(1)

    assert len(turn_api_mock.app.requests) == 1
    request = turn_api_mock.app.requests[0]
    assert json.loads(request.body.decode("utf-8")) == {
        "onboarding_completed": True,
        "dob_month": "2",
        "dob_day": "22",
        "dob_year": "2007",
        "relationship_status": "yes",
        "gender": "other",
        "gender_other": "new gender",
        "province": "FS",
        "suburb": "SomeSuburb",
        "street_name": "Good street",
        "street_number": "12",
    }

    tester.assert_metadata("province", "FS")
    tester.assert_metadata("suburb", "SomeSuburb")
    tester.assert_metadata("street_name", "Good street")
    tester.assert_metadata("street_number", "12")
