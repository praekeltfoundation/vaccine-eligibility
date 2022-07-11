import json
from datetime import date, datetime
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


@pytest.fixture
async def rapidpro_mock(sanic_client):
    Sanic.test_mode = True
    app = Sanic("mock_rapidpro")
    app.requests = []

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
@mock.patch("yal.onboarding.get_current_datetime")
async def test_state_dob_full_valid(
    get_current_datetime, tester: AppTester, rapidpro_mock
):
    get_current_datetime.return_value = datetime(2022, 6, 19, 17, 30)
    tester.setup_state("state_dob_full")

    await tester.user_input("1/1/2007")

    tester.assert_state("state_relationship_status")
    tester.assert_num_messages(1)

    tester.assert_answer("state_dob_year", "2007")
    tester.assert_answer("state_dob_month", "1")
    tester.assert_answer("state_dob_day", "1")
    tester.assert_answer("age", "15")

    assert len(rapidpro_mock.app.requests) == 2
    request = rapidpro_mock.app.requests[0]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {
            "last_onboarding_time": "2022-06-19T17:30:00",
        },
    }


@pytest.mark.asyncio
@mock.patch("yal.onboarding.get_current_datetime")
async def test_state_dob_full_invalid(
    get_current_datetime, tester: AppTester, rapidpro_mock
):
    get_current_datetime.return_value = datetime(2022, 6, 19, 17, 30)
    tester.setup_state("state_dob_full")

    await tester.user_input("1/1/20071")

    tester.assert_state("state_dob_year")
    tester.assert_num_messages(1)

    tester.assert_no_answer("state_dob_year")
    tester.assert_no_answer("state_dob_month")
    tester.assert_no_answer("state_dob_day")
    tester.assert_no_answer("age")

    assert len(rapidpro_mock.app.requests) == 2
    request = rapidpro_mock.app.requests[0]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {
            "last_onboarding_time": "2022-06-19T17:30:00",
        },
    }


@pytest.mark.asyncio
@mock.patch("yal.onboarding.get_current_datetime")
async def test_state_dob_full_skip(
    get_current_datetime, tester: AppTester, rapidpro_mock
):
    get_current_datetime.return_value = datetime(2022, 6, 19, 17, 30)
    tester.setup_state("state_dob_full")

    await tester.user_input("skip")

    tester.assert_state("state_relationship_status")
    tester.assert_num_messages(1)

    tester.assert_answer("state_dob_year", "skip")
    tester.assert_answer("state_dob_month", "skip")
    tester.assert_answer("state_dob_day", "skip")
    tester.assert_no_answer("age")

    assert len(rapidpro_mock.app.requests) == 2
    request = rapidpro_mock.app.requests[0]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {
            "last_onboarding_time": "2022-06-19T17:30:00",
        },
    }


@pytest.mark.asyncio
@mock.patch("yal.onboarding.get_current_datetime")
async def test_state_dob_year_valid(
    get_current_datetime, tester: AppTester, rapidpro_mock
):
    get_current_datetime.return_value = datetime(2022, 6, 19, 17, 30)
    tester.setup_state("state_dob_year")

    await tester.user_input("2007")

    tester.assert_state("state_dob_month")
    tester.assert_num_messages(1)

    tester.assert_answer("state_dob_year", "2007")

    assert len(rapidpro_mock.app.requests) == 2
    request = rapidpro_mock.app.requests[0]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {
            "last_onboarding_time": "2022-06-19T17:30:00",
        },
    }


@pytest.mark.asyncio
@mock.patch("yal.onboarding.get_current_datetime")
async def test_state_dob_year_invalid(
    get_current_datetime, tester: AppTester, rapidpro_mock
):
    get_current_datetime.return_value = datetime(2022, 6, 19, 17, 30)
    tester.setup_state("state_dob_year")

    await tester.user_input("12007")

    tester.assert_state("state_dob_year")
    tester.assert_num_messages(1)

    tester.assert_no_answer("state_dob_year")

    assert len(rapidpro_mock.app.requests) == 1
    request = rapidpro_mock.app.requests[0]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {
            "last_onboarding_time": "2022-06-19T17:30:00",
        },
    }


@pytest.mark.asyncio
@mock.patch("yal.onboarding.get_current_datetime")
async def test_state_dob_month_valid(
    get_current_datetime, tester: AppTester, rapidpro_mock
):
    get_current_datetime.return_value = datetime(2022, 6, 19, 17, 30)
    tester.setup_state("state_dob_month")
    tester.setup_answer("state_dob_year", "2022")

    await tester.user_input("2")

    tester.assert_state("state_dob_day")
    tester.assert_num_messages(1)

    tester.assert_answer("state_dob_month", "2")

    assert len(rapidpro_mock.app.requests) == 2
    request = rapidpro_mock.app.requests[0]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {
            "last_onboarding_time": "2022-06-19T17:30:00",
        },
    }


@pytest.mark.asyncio
@mock.patch("yal.onboarding.get_current_datetime")
async def test_state_dob_month_invalid(
    get_current_datetime, tester: AppTester, rapidpro_mock
):
    get_current_datetime.return_value = datetime(2022, 6, 19, 17, 30)
    tester.setup_state("state_dob_month")
    tester.setup_answer("state_dob_year", "2022")

    await tester.user_input("22")

    tester.assert_state("state_dob_month")
    tester.assert_num_messages(1)

    tester.assert_no_answer("state_dob_month")

    assert len(rapidpro_mock.app.requests) == 1
    request = rapidpro_mock.app.requests[0]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {
            "last_onboarding_time": "2022-06-19T17:30:00",
        },
    }


@pytest.mark.asyncio
@mock.patch("yal.onboarding.get_current_datetime")
async def test_state_dob_month_skip(
    get_current_datetime, tester: AppTester, rapidpro_mock
):
    get_current_datetime.return_value = datetime(2022, 6, 19, 17, 30)
    tester.setup_state("state_dob_month")
    tester.setup_answer("state_dob_year", "2022")

    await tester.user_input("skip")

    tester.assert_state("state_dob_day")
    tester.assert_num_messages(1)

    tester.assert_answer("state_dob_month", "skip")

    assert len(rapidpro_mock.app.requests) == 2
    request = rapidpro_mock.app.requests[0]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {
            "last_onboarding_time": "2022-06-19T17:30:00",
        },
    }


@pytest.mark.asyncio
@mock.patch("yal.onboarding.get_current_datetime")
async def test_state_dob_day_valid(
    get_current_datetime, tester: AppTester, rapidpro_mock
):
    get_current_datetime.return_value = datetime(2022, 6, 19, 17, 30)
    tester.setup_state("state_dob_day")

    tester.setup_answer("state_dob_year", "2022")
    tester.setup_answer("state_dob_month", "2")

    await tester.user_input("2")

    tester.assert_state("state_relationship_status")
    tester.assert_num_messages(1)

    tester.assert_answer("state_dob_day", "2")

    assert len(rapidpro_mock.app.requests) == 2
    request = rapidpro_mock.app.requests[0]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {
            "last_onboarding_time": "2022-06-19T17:30:00",
        },
    }


@pytest.mark.asyncio
@mock.patch("yal.onboarding.get_current_datetime")
async def test_state_dob_day_valid_no_year(
    get_current_datetime, tester: AppTester, rapidpro_mock
):
    get_current_datetime.return_value = datetime(2022, 6, 19, 17, 30)
    tester.setup_state("state_dob_day")

    tester.setup_answer("state_dob_year", "skip")
    tester.setup_answer("state_dob_month", "2")

    await tester.user_input("2")

    tester.assert_state("state_relationship_status")
    tester.assert_num_messages(1)

    tester.assert_answer("state_dob_day", "2")

    assert len(rapidpro_mock.app.requests) == 2
    request = rapidpro_mock.app.requests[0]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {
            "last_onboarding_time": "2022-06-19T17:30:00",
        },
    }


@pytest.mark.asyncio
@mock.patch("yal.onboarding.get_current_datetime")
async def test_state_dob_day_invalid(
    get_current_datetime, tester: AppTester, rapidpro_mock
):
    get_current_datetime.return_value = datetime(2022, 6, 19, 17, 30)
    tester.setup_state("state_dob_day")

    tester.setup_answer("state_dob_year", "skip")
    tester.setup_answer("state_dob_month", "2")

    await tester.user_input("200")

    tester.assert_state("state_dob_day")
    tester.assert_num_messages(1)

    tester.assert_no_answer("state_dob_day")

    assert len(rapidpro_mock.app.requests) == 1
    request = rapidpro_mock.app.requests[0]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {
            "last_onboarding_time": "2022-06-19T17:30:00",
        },
    }


@pytest.mark.asyncio
@mock.patch("yal.onboarding.get_current_datetime")
async def test_state_dob_day_invalid_date(
    get_current_datetime, tester: AppTester, rapidpro_mock
):
    get_current_datetime.return_value = datetime(2022, 6, 19, 17, 30)
    tester.setup_state("state_dob_day")

    tester.setup_answer("state_dob_year", "2022")
    tester.setup_answer("state_dob_month", "9")

    await tester.user_input("31")

    tester.assert_state("state_dob_day")
    tester.assert_num_messages(1)

    tester.assert_no_answer("state_dob_day")

    assert len(rapidpro_mock.app.requests) == 1
    request = rapidpro_mock.app.requests[0]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {
            "last_onboarding_time": "2022-06-19T17:30:00",
        },
    }


@pytest.mark.asyncio
@mock.patch("yal.onboarding.get_current_datetime")
async def test_state_dob_day_skip(
    get_current_datetime, tester: AppTester, rapidpro_mock
):
    get_current_datetime.return_value = datetime(2022, 6, 19, 17, 30)
    tester.setup_state("state_dob_day")

    tester.setup_answer("state_dob_year", "2022")
    tester.setup_answer("state_dob_month", "2")

    await tester.user_input("skip")

    tester.assert_state("state_relationship_status")
    tester.assert_num_messages(1)

    tester.assert_answer("state_dob_day", "skip")

    assert len(rapidpro_mock.app.requests) == 2
    request = rapidpro_mock.app.requests[0]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {
            "last_onboarding_time": "2022-06-19T17:30:00",
        },
    }


@pytest.mark.asyncio
@mock.patch("yal.onboarding.get_current_datetime")
@mock.patch("yal.onboarding.get_today")
async def test_state_check_birthday(
    get_today, get_current_datetime, tester: AppTester, rapidpro_mock
):
    get_current_datetime.return_value = datetime(2022, 6, 19, 17, 30)
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

    assert len(rapidpro_mock.app.requests) == 2
    request = rapidpro_mock.app.requests[0]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {
            "last_onboarding_time": "2022-06-19T17:30:00",
        },
    }


@pytest.mark.asyncio
@mock.patch("yal.onboarding.get_current_datetime")
@mock.patch("yal.onboarding.get_today")
async def test_state_check_birthday_skip_day(
    get_today, get_current_datetime, tester: AppTester, rapidpro_mock
):
    get_current_datetime.return_value = datetime(2022, 6, 19, 17, 30)
    get_today.return_value = date(2022, 2, 22)
    tester.setup_state("state_dob_day")

    tester.setup_answer("state_dob_month", "2")
    tester.setup_answer("state_dob_year", "2007")

    await tester.user_input("skip")
    tester.assert_no_answer("age")

    tester.assert_state("state_relationship_status")
    tester.assert_num_messages(1)
    assert tester.fake_worker.outbound_messages == []

    assert len(rapidpro_mock.app.requests) == 2
    request = rapidpro_mock.app.requests[0]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {
            "last_onboarding_time": "2022-06-19T17:30:00",
        },
    }


@pytest.mark.asyncio
@mock.patch("yal.onboarding.get_current_datetime")
@mock.patch("yal.onboarding.get_today")
async def test_state_check_birthday_skip_month(
    get_today, get_current_datetime, tester: AppTester, rapidpro_mock
):
    get_current_datetime.return_value = datetime(2022, 6, 19, 17, 30)
    get_today.return_value = date(2022, 2, 22)
    tester.setup_state("state_dob_day")

    tester.setup_answer("state_dob_month", "skip")
    tester.setup_answer("state_dob_year", "2007")

    await tester.user_input("22")
    tester.assert_no_answer("age")

    tester.assert_state("state_relationship_status")
    tester.assert_num_messages(1)
    assert tester.fake_worker.outbound_messages == []

    assert len(rapidpro_mock.app.requests) == 2
    request = rapidpro_mock.app.requests[0]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {
            "last_onboarding_time": "2022-06-19T17:30:00",
        },
    }


@pytest.mark.asyncio
@mock.patch("yal.onboarding.get_current_datetime")
@mock.patch("yal.onboarding.get_today")
async def test_state_check_birthday_skip_year(
    get_today, get_current_datetime, tester: AppTester, rapidpro_mock
):
    get_current_datetime.return_value = datetime(2022, 6, 19, 17, 30)
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

    assert len(rapidpro_mock.app.requests) == 2
    request = rapidpro_mock.app.requests[0]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {
            "last_onboarding_time": "2022-06-19T17:30:00",
        },
    }


@pytest.mark.asyncio
@mock.patch("yal.onboarding.get_current_datetime")
async def test_state_relationship_status_valid(
    get_current_datetime, tester: AppTester, rapidpro_mock
):
    get_current_datetime.return_value = datetime(2022, 6, 19, 17, 30)
    tester.setup_state("state_relationship_status")

    await tester.user_input("2")

    tester.assert_state("state_province")
    tester.assert_num_messages(1)

    tester.assert_answer("state_relationship_status", "complicated")

    assert len(rapidpro_mock.app.requests) == 2
    request = rapidpro_mock.app.requests[0]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {
            "last_onboarding_time": "2022-06-19T17:30:00",
        },
    }


@pytest.mark.asyncio
@mock.patch("yal.onboarding.get_current_datetime")
async def test_state_full_address_invalid(
    get_current_datetime, tester: AppTester, rapidpro_mock
):
    get_current_datetime.return_value = datetime(2022, 6, 19, 17, 30)
    tester.setup_answer("age", "22")
    tester.setup_state("state_full_address")

    await tester.user_input("2 test street \n test suburb")

    tester.assert_state("state_suburb")

    assert len(rapidpro_mock.app.requests) == 2
    request = rapidpro_mock.app.requests[0]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {
            "last_onboarding_time": "2022-06-19T17:30:00",
        },
    }


@pytest.mark.asyncio
@mock.patch("yal.onboarding.get_current_datetime")
async def test_state_full_address_valid(
    get_current_datetime, tester: AppTester, rapidpro_mock
):
    get_current_datetime.return_value = datetime(2022, 6, 19, 17, 30)
    tester.setup_answer("age", "22")
    tester.setup_state("state_full_address")

    await tester.user_input("2\ntest street\n test suburb")

    tester.assert_state("state_gender")

    assert len(rapidpro_mock.app.requests) == 2
    request = rapidpro_mock.app.requests[0]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {
            "last_onboarding_time": "2022-06-19T17:30:00",
        },
    }


@pytest.mark.asyncio
@mock.patch("yal.onboarding.get_current_datetime")
async def test_state_full_address_minor(
    get_current_datetime, tester: AppTester, rapidpro_mock
):
    get_current_datetime.return_value = datetime(2022, 6, 19, 17, 30)
    tester.setup_answer("age", "17")
    tester.setup_state("state_province")

    await tester.user_input("2")

    tester.assert_state("state_gender")

    assert len(rapidpro_mock.app.requests) == 3
    request = rapidpro_mock.app.requests[0]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {
            "last_onboarding_time": "2022-06-19T17:30:00",
        },
    }


@pytest.mark.asyncio
@mock.patch("yal.onboarding.get_current_datetime")
async def test_state_gender(get_current_datetime, tester: AppTester, rapidpro_mock):
    get_current_datetime.return_value = datetime(2022, 6, 19, 17, 30)
    tester.setup_state("state_gender")

    await tester.user_input(session=Message.SESSION_EVENT.NEW)

    tester.assert_message(
        "\n".join(
            [
                "*ABOUT YOU*",
                "🌈 How you identify",
                "-----",
                "",
                "*You're almost done!*🙌🏾",
                "",
                "✅ Birthday",
                "✅ Relationship Status",
                "✅ Location",
                "◻️ Gender",
                "-----",
                "",
                "*What's your gender?*",
                "",
                "Please select the option you think best describes you:",
                "",
                "*1* - Girl/Woman",
                "*2* - Cisgender",
                "*3* - Boy/Man",
                "*4* - Genderfluid",
                "*5* - Intersex",
                "*6* - Non-binary",
                "*7* - Questioning",
                "*8* - Transgender",
                "*9* - Something else",
                "*10* - Skip",
            ]
        )
    )

    assert len(rapidpro_mock.app.requests) == 1
    request = rapidpro_mock.app.requests[0]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {
            "last_onboarding_time": "2022-06-19T17:30:00",
        },
    }


@pytest.mark.asyncio
@mock.patch("yal.onboarding.get_current_datetime")
async def test_state_gender_valid(
    get_current_datetime, tester: AppTester, rapidpro_mock
):
    get_current_datetime.return_value = datetime(2022, 6, 19, 17, 30)
    tester.setup_state("state_gender")

    await tester.user_input("9")

    tester.assert_state("state_name_gender")
    tester.assert_num_messages(1)

    tester.assert_answer("state_gender", "other")

    assert len(rapidpro_mock.app.requests) == 2
    request = rapidpro_mock.app.requests[0]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {
            "last_onboarding_time": "2022-06-19T17:30:00",
        },
    }


@pytest.mark.asyncio
async def test_submit_onboarding(tester: AppTester, rapidpro_mock):
    tester.setup_state("state_name_gender")

    tester.setup_answer("state_dob_month", "2")
    tester.setup_answer("state_dob_day", "22")
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

    assert len(rapidpro_mock.app.requests) == 2
    request = rapidpro_mock.app.requests[1]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {
            "onboarding_completed": "True",
            "dob_month": "2",
            "dob_day": "22",
            "relationship_status": "yes",
            "gender": "other",
            "gender_other": "new gender",
            "province": "FS",
            "suburb": "SomeSuburb",
            "street_name": "Good street",
            "street_number": "12",
        },
    }

    tester.assert_metadata("province", "FS")
    tester.assert_metadata("suburb", "SomeSuburb")
    tester.assert_metadata("street_name", "Good street")
    tester.assert_metadata("street_number", "12")
