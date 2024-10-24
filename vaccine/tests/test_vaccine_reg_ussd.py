import gzip
from datetime import date
from unittest import mock

import pytest
from sanic import Sanic, response

from vaccine.models import Message, StateData, User
from vaccine.testing import AppTester, TState, run_sanic
from vaccine.vaccine_reg_ussd import Application, config


@pytest.fixture
def tester():
    return AppTester(Application)


@pytest.fixture
async def evds_mock():
    Sanic.test_mode = True
    app = Sanic("mock_turn")
    tstate = TState()

    @app.route("/api/private/evds-sa/person/8/record", methods=["POST"])
    def submit_record(request):
        tstate.requests.append(request)
        if tstate.errormax and tstate.errors < tstate.errormax:
            tstate.errors += 1
            return response.json({}, status=500)
        return response.json({}, status=200)

    @app.route("/api/private/evds-sa/person/8/lookup/location/1", methods=["GET"])
    def get_suburbs(request):
        with gzip.open("vaccine/data/suburbs.json.gz") as f:
            return response.raw(f.read(), content_type="application/json")

    async with run_sanic(app) as server:
        url = config.EVDS_URL
        username = config.EVDS_USERNAME
        password = config.EVDS_PASSWORD
        config.EVDS_URL = f"http://{server.host}:{server.port}"
        config.EVDS_USERNAME = "test"
        config.EVDS_PASSWORD = "test"  # noqa: S105 - Fake password/token for test purposes
        server.tstate = tstate
        yield server
        config.EVDS_URL = url
        config.EVDS_USERNAME = username
        config.EVDS_PASSWORD = password


@pytest.fixture
async def eventstore_mock():
    Sanic.test_mode = True
    app = Sanic("mock_eventstore")
    tstate = TState()

    @app.route("/v2/vaccineregistration/", methods=["POST"])
    def valid_registration(request):
        tstate.requests.append(request)
        return response.json({})

    async with run_sanic(app) as server:
        url = config.VACREG_EVENTSTORE_URL
        config.VACREG_EVENTSTORE_URL = f"http://{server.host}:{server.port}"
        server.tstate = tstate
        yield server
        config.VACREG_EVENTSTORE_URL = url


@pytest.mark.asyncio
async def test_age_gate():
    """
    Should notify the user of minimum age
    """
    u = User(addr="27820001001", state=StateData())
    app = Application(u)
    msg = Message(
        content=None,
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
        session_event=Message.SESSION_EVENT.NEW,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert u.state.name == "state_age_gate"


@pytest.mark.asyncio
async def test_age_gate_error():
    """
    Should show the error message on incorrect input
    """
    u = User(addr="27820001001", state=StateData(name="state_age_gate"), session_id=1)
    app = Application(u)
    msg = Message(
        content="invalid",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 140
    assert u.state.name == "state_age_gate"


@pytest.mark.asyncio
async def test_under_age_notification_error():
    """
    Should show the error message on incorrect input
    """
    u = User(
        addr="27820001001",
        state=StateData(name="state_under_age_notification"),
        session_id=1,
    )
    app = Application(u)
    msg = Message(
        content="invalid",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert u.state.name == "state_under_age_notification"


@pytest.mark.asyncio
async def test_under_age_notification_confirm():
    """
    Should confirm the selection and end the session
    """
    u = User(
        addr="27820001001",
        state=StateData(name="state_under_age_notification"),
        session_id=1,
    )
    app = Application(u)
    msg = Message(
        content="yes",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert reply.content == "Thank you for confirming"
    assert reply.session_event == Message.SESSION_EVENT.CLOSE


@pytest.mark.asyncio
async def test_identification_type():
    u = User(
        addr="27820001001",
        state=StateData(name="state_terms_and_conditions_3"),
        session_id=1,
    )
    app = Application(u)
    msg = Message(
        content="accept",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert u.state.name == "state_identification_type"


@pytest.mark.asyncio
async def test_identification_type_invalid():
    u = User(
        addr="27820001001",
        state=StateData(name="state_identification_type"),
        session_id=1,
    )
    app = Application(u)
    msg = Message(
        content="invalid",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert u.state.name == "state_identification_type"


@pytest.mark.asyncio
async def test_identification_number():
    u = User(
        addr="27820001001",
        state=StateData(name="state_identification_type"),
        session_id=1,
    )
    app = Application(u)
    msg = Message(
        content="rsa id number / birth certificate number",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert u.state.name == "state_identification_number"


@pytest.mark.asyncio
async def test_identification_number_invalid():
    u = User(
        addr="27820001001",
        state=StateData(name="state_identification_number"),
        session_id=1,
    )
    app = Application(u)
    u.answers["state_identification_type"] = app.ID_TYPES.rsa_id.name
    msg = Message(
        content="9001010001089",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert u.state.name == "state_identification_number"


@pytest.mark.asyncio
async def test_identification_number_said_on_passport(tester: AppTester):
    tester.setup_state("state_identification_number")
    tester.setup_answer("state_identification_type", "passport")
    await tester.user_input("9001010001088")
    tester.assert_state("state_check_id_number")
    tester.assert_num_messages(1)


@pytest.mark.asyncio
@mock.patch("vaccine.utils.get_today")
async def test_check_id_number(get_today, tester: AppTester):
    get_today.return_value = date(2100, 1, 1)
    tester.setup_state("state_identification_number")
    tester.setup_answer("state_identification_type", "passport")
    await tester.user_input("9001010001088")
    tester.assert_state("state_check_id_number")
    tester.assert_num_messages(1)
    await tester.user_input("yes")
    tester.assert_answer("state_identification_type", "rsa_id")
    tester.assert_answer("state_dob_year", "1990")
    tester.assert_answer("state_dob_month", "1")
    tester.assert_answer("state_dob_day", "1")
    tester.assert_answer("state_gender", "Female")
    tester.assert_state("state_first_name")


@pytest.mark.asyncio
async def test_check_id_number_restart(tester: AppTester):
    tester.setup_state("state_identification_number")
    tester.setup_answer("state_identification_type", "passport")
    await tester.user_input("9001010001088")
    tester.assert_num_messages(1)
    tester.assert_state("state_check_id_number")
    await tester.user_input("no")
    tester.assert_num_messages(1)
    tester.assert_state("state_identification_type")


@pytest.mark.asyncio
async def test_passport_country():
    u = User(
        addr="27820001001",
        state=StateData(name="state_identification_number"),
        session_id=1,
    )
    app = Application(u)
    u.answers["state_identification_type"] = app.ID_TYPES.passport.name
    msg = Message(
        content="A1234567890",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert u.state.name == "state_passport_country"


@pytest.mark.asyncio
async def test_passport_country_by_choosing():
    u = User(
        addr="27820001001", state=StateData(name="state_passport_country"), session_id=1
    )
    app = Application(u)
    u.answers["state_identification_type"] = app.ID_TYPES.passport.name
    msg = Message(
        content="2",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert u.state.name == "state_gender"
    assert u.answers["state_passport_country"] == "MZ"


@pytest.mark.asyncio
async def test_passport_country_invalid():
    u = User(
        addr="27820001001", state=StateData(name="state_passport_country"), session_id=1
    )
    app = Application(u)
    msg = Message(
        content="invalid",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert u.state.name == "state_passport_country"


@pytest.mark.asyncio
async def test_passport_country_search():
    u = User(
        addr="27820001001", state=StateData(name="state_passport_country"), session_id=1
    )
    app = Application(u)
    u.answers["state_identification_type"] = app.ID_TYPES.passport.name
    msg = Message(
        content="other",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert u.state.name == "state_passport_country_search"
    assert reply.content == "Please TYPE in your passport's COUNTRY of origin."
    assert len(reply.content) < 160

    app.messages = []
    msg = Message(
        content="cote d'ivory",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert u.state.name == "state_passport_country_list"
    assert u.answers["state_passport_country_search"] == "cote d'ivory"

    assert reply.content == "\n".join(
        [
            "Please choose the best match for your COUNTRY of origin:",
            "1. Republic of Côte d'Ivoire",
            "2. British Indian Ocean Territ",
            "3. Plurinational State of Boli",
            "4. Other",
        ]
    )
    assert len(reply.content) < 160

    msg = Message(
        content="1",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    await app.process_message(msg)
    assert u.answers["state_passport_country_list"] == "CI"


@pytest.mark.asyncio
async def test_passport_country_search_other():
    u = User(
        addr="27820001001",
        state=StateData(name="state_passport_country_list"),
        session_id=1,
        answers={
            "state_passport_country": "other",
            "state_passport_country_search": "cote d'ivoire",
        },
    )
    app = Application(u)
    msg = Message(
        content="other",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert u.state.name == "state_passport_country_search"


@pytest.mark.asyncio
async def test_passport_country_search_list_invalid():
    u = User(
        addr="27820001001",
        state=StateData(name="state_passport_country_list"),
        session_id=1,
        answers={
            "state_passport_country": "other",
            "state_passport_country_search": "Côte d'Ivoire",
        },
    )
    app = Application(u)
    msg = Message(
        content="invalid",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert u.state.name == "state_passport_country_list"


@pytest.mark.asyncio
async def test_said_date_and_sex_extraction():
    u = User(
        addr="27820001001",
        state=StateData(name="state_identification_number"),
        session_id=1,
    )
    app = Application(u)
    u.answers["state_identification_type"] = app.ID_TYPES.rsa_id.name
    msg = Message(
        content="9001010001088",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    await app.process_message(msg)
    assert u.answers["state_dob_year"] == "1990"
    assert u.answers["state_dob_month"] == "1"
    assert u.answers["state_dob_day"] == "1"
    assert u.answers["state_gender"] == "Female"


@pytest.mark.asyncio
@mock.patch("vaccine.vaccine_reg_ussd.get_today")
@mock.patch("vaccine.utils.get_today")
async def test_said_date_extraction_ambiguous(
    get_today1, get_today2, tester: AppTester
):
    get_today1.return_value = date(2020, 1, 1)
    get_today2.return_value = date(2020, 1, 1)
    tester.setup_state("state_identification_number")
    tester.setup_answer("state_identification_type", "rsa_id")
    await tester.user_input("0001010001087")
    tester.assert_state("state_dob_year")
    tester.assert_no_answer("state_dob_year")

    await tester.user_input("1900")
    tester.assert_answer("state_dob_month", "1")
    tester.assert_answer("state_dob_day", "1")


@pytest.mark.asyncio
async def test_gender():
    u = User(
        addr="27820001001",
        state=StateData(name="state_identification_number"),
        session_id=1,
    )
    app = Application(u)
    u.answers["state_identification_type"] = app.ID_TYPES.asylum_seeker.name
    msg = Message(
        content="ABC123",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert u.state.name == "state_gender"


@pytest.mark.asyncio
async def test_gender_invalid():
    u = User(addr="27820001001", state=StateData(name="state_gender"), session_id=1)
    app = Application(u)
    u.answers["state_identification_type"] = app.ID_TYPES.passport.name
    msg = Message(
        content="invalid",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert u.state.name == "state_gender"


@pytest.mark.asyncio
@mock.patch("vaccine.utils.get_today")
async def test_dob_and_gender_skipped(get_today):
    get_today.return_value = date(2100, 1, 1)
    u = User(
        addr="27820001001",
        state=StateData(name="state_identification_number"),
        session_id=1,
    )
    app = Application(u)
    u.answers["state_identification_type"] = app.ID_TYPES.rsa_id.name
    msg = Message(
        content="9001010001088",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert u.state.name == "state_first_name"


@pytest.mark.asyncio
@mock.patch("vaccine.utils.get_today")
async def test_too_young(get_today):
    get_today.return_value = date(2020, 1, 1)
    u = User(
        addr="27820001001",
        state=StateData(name="state_identification_number"),
        session_id=1,
    )
    app = Application(u)
    u.answers["state_identification_type"] = app.ID_TYPES.rsa_id.name
    msg = Message(
        content="9001010001088",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert u.state.name == "state_under_age_notification"


@pytest.mark.asyncio
async def test_dob_year():
    u = User(addr="27820001001", state=StateData(name="state_gender"), session_id=1)
    app = Application(u)
    u.answers["state_identification_type"] = app.ID_TYPES.passport.name
    msg = Message(
        content="male",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert u.state.name == "state_dob_year"


@pytest.mark.asyncio
async def test_dob_year_invalid():
    u = User(addr="27820001001", state=StateData(name="state_dob_year"), session_id=1)
    app = Application(u)
    u.answers["state_identification_type"] = app.ID_TYPES.passport.name
    msg = Message(
        content="invalid",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert u.state.name == "state_dob_year"
    assert (
        reply.content
        == "REQUIRED: Please TYPE the 4 digits of the YEAR you were born (Example: "
        "1980)"
    )


@pytest.mark.asyncio
@mock.patch("vaccine.utils.get_today")
async def test_dob_year_not_match_id(get_today):
    get_today.return_value = date(2010, 1, 1)
    u = User(
        addr="27820001001",
        state=StateData(name="state_dob_year"),
        session_id=1,
        answers={"state_identification_number": "9001010001088"},
    )
    app = Application(u)
    u.answers["state_identification_type"] = app.ID_TYPES.rsa_id.name
    msg = Message(
        content="1991",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert u.state.name == "state_dob_year"
    assert (
        reply.content
        == "The YEAR you have given does not match the YEAR of your ID number. Please "
        "try again"
    )


@pytest.mark.asyncio
async def test_dob_month():
    u = User(addr="27820001001", state=StateData(name="state_dob_year"), session_id=1)
    app = Application(u)
    u.answers["state_identification_type"] = app.ID_TYPES.asylum_seeker.name
    msg = Message(
        content="1990",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert u.state.name == "state_dob_month"


@pytest.mark.asyncio
async def test_dob_month_error():
    u = User(addr="27820001001", state=StateData(name="state_dob_month"), session_id=1)
    app = Application(u)
    u.answers["state_identification_type"] = app.ID_TYPES.passport.name
    msg = Message(
        content="invalid",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert u.state.name == "state_dob_month"


@pytest.mark.asyncio
async def test_dob_day():
    u = User(addr="27820001001", state=StateData(name="state_dob_month"), session_id=1)
    app = Application(u)
    u.answers["state_identification_type"] = app.ID_TYPES.passport.name
    msg = Message(
        content="jan",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert u.state.name == "state_dob_day"


@pytest.mark.asyncio
async def test_dob_day_invalid():
    u = User(
        addr="27820001001",
        state=StateData(name="state_dob_day"),
        session_id=1,
        answers={"state_dob_year": "1990", "state_dob_month": "2"},
    )
    app = Application(u)
    u.answers["state_identification_type"] = app.ID_TYPES.passport.name
    msg = Message(
        content="29",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert u.state.name == "state_dob_day"


@pytest.mark.asyncio
@mock.patch("vaccine.utils.get_today")
async def test_first_name(get_today):
    get_today.return_value = date(2100, 1, 1)
    u = User(
        addr="27820001001",
        state=StateData(name="state_dob_day"),
        session_id=1,
        answers={"state_dob_year": "1990", "state_dob_month": "2"},
    )
    app = Application(u)
    u.answers["state_identification_type"] = app.ID_TYPES.passport.name
    msg = Message(
        content="2",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert u.state.name == "state_first_name"


@pytest.mark.asyncio
@mock.patch("vaccine.utils.get_today")
async def test_surname(get_today):
    get_today.return_value = date(2100, 1, 1)
    u = User(
        addr="27820001001",
        state=StateData(name="state_first_name"),
        session_id=1,
        answers={
            "state_dob_year": "1990",
            "state_dob_month": "1",
            "state_dob_day": "1",
        },
    )
    app = Application(u)
    msg = Message(
        content="firstname",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert u.state.name == "state_surname"
    assert u.answers["state_first_name"] == "firstname"


@pytest.mark.asyncio
async def test_state_confirm_profile():
    u = User(
        addr="27820001001",
        state=StateData(name="state_surname"),
        session_id=1,
        answers={
            "state_first_name": "reallyreallylongfirstname",
            "state_identification_number": "012345678901234567890123456789",
        },
    )
    app = Application(u)
    u.answers["state_identification_type"] = app.ID_TYPES.refugee.name
    msg = Message(
        content="reallyreallylongsurname",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert u.state.name == "state_confirm_profile"
    assert u.answers["state_surname"] == "reallyreallylongsurname"
    assert reply.content == "\n".join(
        [
            "Confirm the following:",
            "",
            "reallyreallylongfirstname reallyreallylongsurname",
            "0123456789012345678901234",
            "",
            "1. Correct",
            "2. Wrong",
        ]
    )


@pytest.mark.asyncio
async def test_state_confirm_profile_invalid():
    u = User(
        addr="27820001001",
        state=StateData(name="state_confirm_profile"),
        session_id=1,
        answers={
            "state_first_name": "reallyreallylongfirstname12345678901234567890",
            "state_surname": "reallyreallylongsurname1245678901234567890",
            "state_identification_number": "0123456789012345678901234567891234567890",
        },
    )
    app = Application(u)
    u.answers["state_identification_type"] = app.ID_TYPES.refugee.name
    msg = Message(
        content="invalid",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert u.state.name == "state_confirm_profile"


@pytest.mark.asyncio
async def test_state_confirm_profile_no():
    u = User(
        addr="27820001001",
        state=StateData(name="state_confirm_profile"),
        session_id=1,
        answers={
            "state_first_name": "reallyreallylongfirstname1234567890",
            "state_surname": "reallyreallylongsurname124567890",
            "state_identification_number": "012345678901234567890123456789",
        },
    )
    app = Application(u)
    u.answers["state_identification_type"] = app.ID_TYPES.refugee.name
    msg = Message(
        content="wrong",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert u.state.name == "state_gender"


@pytest.mark.asyncio
async def test_province(evds_mock):
    u = User(
        addr="27820001001",
        state=StateData(name="state_confirm_profile"),
        session_id=1,
        answers={
            "state_first_name": "reallyreallylongfirstname1234567890",
            "state_surname": "reallyreallylongsurname124567890",
            "state_identification_number": "012345678901234567890123456789",
        },
    )
    app = Application(u)
    u.answers["state_identification_type"] = app.ID_TYPES.refugee.name
    msg = Message(
        content="correct",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert u.state.name == "state_province_id"


@pytest.mark.asyncio
async def test_province_invalid(evds_mock):
    u = User(
        addr="27820001001", state=StateData(name="state_province_id"), session_id=1
    )
    app = Application(u)
    msg = Message(
        content="invalid",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert u.state.name == "state_province_id"


@pytest.mark.asyncio
async def test_suburb_search(evds_mock):
    u = User(
        addr="27820001001", state=StateData(name="state_province_id"), session_id=1
    )
    app = Application(u)
    msg = Message(
        content="9",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert u.state.name == "state_suburb_search"
    assert u.answers["state_province_id"] == "western cape"


@pytest.mark.asyncio
async def test_municipality(evds_mock):
    u = User(
        addr="27820001001",
        state=StateData(name="state_suburb_search"),
        session_id=1,
        answers={"state_province_id": "eastern cape"},
    )
    app = Application(u)
    msg = Message(
        content="mandela",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert reply.content == "\n".join(
        [
            "Please select your municipality",
            "1. Buffalo City",
            "2. Enoch Mgijima",
            "3. Great Kei",
            "4. King Sabata Dalindyebo",
            "5. Nelson Mandela Bay",
            "6. Raymond Mhlaba",
            "7. Other",
        ]
    )
    assert u.state.name == "state_municipality"


@pytest.mark.asyncio
async def test_suburb_with_municipality(evds_mock):
    u = User(
        addr="27820001001",
        state=StateData(name="state_municipality"),
        session_id=1,
        answers={"state_province_id": "eastern cape", "state_suburb_search": "mandela"},
    )
    app = Application(u)
    msg = Message(
        content="Raymond Mhlaba",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert reply.content == "\n".join(
        [
            "Please choose the best match for your location:",
            "1. Mandela Park, Balfour",
            "2. Other",
        ]
    )
    assert u.state.name == "state_suburb"


@pytest.mark.asyncio
async def test_suburb_with_municipality_other(evds_mock):
    u = User(
        addr="27820001001",
        state=StateData(name="state_municipality"),
        session_id=1,
        answers={"state_province_id": "eastern cape", "state_suburb_search": "mandela"},
    )
    app = Application(u)
    msg = Message(
        content="other",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert u.state.name == "state_suburb_search"


@pytest.mark.asyncio
async def test_suburb(evds_mock):
    u = User(
        addr="27820001001",
        state=StateData(name="state_suburb_search"),
        session_id=1,
        answers={"state_province_id": "western cape"},
    )
    app = Application(u)
    msg = Message(
        content="tableview",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert reply.content == "\n".join(
        [
            "Please choose the best match for your location:",
            "1. Table View, Blouberg",
            "2. Other",
        ]
    )
    assert u.state.name == "state_suburb"


@pytest.mark.asyncio
async def test_province_no_results(evds_mock):
    u = User(
        addr="27820001001",
        state=StateData(name="state_suburb_search"),
        session_id=1,
        answers={"state_province_id": "western cape"},
    )
    app = Application(u)
    msg = Message(
        content="invalid",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert reply.content == "\n".join(
        [
            "Suburb not found. Try again",
            "1. Eastern Cape",
            "2. Free State",
            "3. Gauteng",
            "4. Kwazulu-natal",
            "5. Limpopo",
            "6. Mpumalanga",
            "7. North West",
            "8. Northern Cape",
            "9. Western Cape",
        ]
    )
    assert u.state.name == "state_province_no_results"


@pytest.mark.asyncio
async def test_suburb_no_results(evds_mock):
    u = User(
        addr="27820001001",
        state=StateData(name="state_province_no_results"),
        session_id=1,
    )
    app = Application(u)
    msg = Message(
        content="western cape",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert u.state.name == "state_suburb_search"
    assert u.answers["state_province_id"] == "western cape"


@pytest.mark.asyncio
async def test_suburb_error(evds_mock):
    u = User(
        addr="27820001001",
        state=StateData(name="state_suburb"),
        session_id=1,
        answers={
            "state_province_id": "western cape",
            "state_suburb_search": "tableview",
        },
    )
    app = Application(u)
    msg = Message(
        content="invalid",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert u.state.name == "state_suburb"


@pytest.mark.asyncio
async def test_suburb_other(evds_mock):
    u = User(
        addr="27820001001",
        state=StateData(name="state_suburb"),
        session_id=1,
        answers={
            "state_province_id": "western cape",
            "state_suburb_search": "tableview",
        },
    )
    app = Application(u)
    msg = Message(
        content="other",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert u.state.name == "state_province_id"


@pytest.mark.asyncio
async def test_self_registration(evds_mock):
    u = User(
        addr="27820001001",
        state=StateData(name="state_suburb"),
        session_id=1,
        answers={
            "state_province_id": "western cape",
            "state_suburb_search": "tableview",
        },
    )
    app = Application(u)
    msg = Message(
        content="1",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert reply.content == "\n".join(
        [
            "Can we use this number: 082 000 1001 to send you SMS appointment "
            "information?",
            "1. Yes",
            "2. No",
        ]
    )
    assert u.state.name == "state_self_registration"


@pytest.mark.asyncio
async def test_self_registration_invalid():
    u = User(
        addr="27820001001",
        state=StateData(name="state_self_registration"),
        session_id=1,
    )
    app = Application(u)
    msg = Message(
        content="invalid",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert u.state.name == "state_self_registration"


@pytest.mark.asyncio
async def test_phone_number():
    u = User(
        addr="27820001001",
        state=StateData(name="state_self_registration"),
        session_id=1,
    )
    app = Application(u)
    msg = Message(
        content="no",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert u.state.name == "state_phone_number"


@pytest.mark.asyncio
async def test_phone_number_invalid():
    u = User(
        addr="27820001001", state=StateData(name="state_phone_number"), session_id=1
    )
    app = Application(u)
    msg = Message(
        content="invalid",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert u.state.name == "state_phone_number"


@pytest.mark.asyncio
async def test_phone_number_confirm():
    u = User(
        addr="27820001001", state=StateData(name="state_phone_number"), session_id=1
    )
    app = Application(u)
    msg = Message(
        content="0820001001",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert u.state.name == "state_confirm_phone_number"


@pytest.mark.asyncio
async def test_phone_number_confirm_invalid():
    u = User(
        addr="27820001001",
        state=StateData(name="state_confirm_phone_number"),
        session_id=1,
        answers={"state_phone_number": "0820001001"},
    )
    app = Application(u)
    msg = Message(
        content="invalid",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert u.state.name == "state_confirm_phone_number"


@pytest.mark.asyncio
async def test_vaccination_time():
    u = User(
        addr="27820001001",
        state=StateData(name="state_self_registration"),
        session_id=1,
    )
    app = Application(u)
    msg = Message(
        content="yes",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert u.state.name == "state_vaccination_time"


@pytest.mark.asyncio
async def test_vaccination_time_invalid():
    u = User(
        addr="27820001001", state=StateData(name="state_vaccination_time"), session_id=1
    )
    app = Application(u)
    msg = Message(
        content="invalid",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert u.state.name == "state_vaccination_time"


@pytest.mark.asyncio
async def test_medical_aid():
    u = User(
        addr="27820001001", state=StateData(name="state_vaccination_time"), session_id=1
    )
    app = Application(u)
    msg = Message(
        content="weekday morning",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert u.state.name == "state_medical_aid"


@pytest.mark.asyncio
async def test_medical_aid_invalid():
    u = User(
        addr="27820001001", state=StateData(name="state_medical_aid"), session_id=1
    )
    app = Application(u)
    msg = Message(
        content="invalid",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert u.state.name == "state_medical_aid"


@pytest.mark.asyncio
async def test_terms_and_conditions():
    u = User(addr="27820001001", state=StateData(name="state_age_gate"), session_id=1)
    app = Application(u)
    msg = Message(
        content="continue",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert u.state.name == "state_terms_and_conditions"


@pytest.mark.asyncio
async def test_terms_and_conditions_invalid():
    u = User(
        addr="27820001001",
        state=StateData(name="state_terms_and_conditions"),
        session_id=1,
    )
    app = Application(u)
    msg = Message(
        content="invalid",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert u.state.name == "state_terms_and_conditions"


@pytest.mark.asyncio
async def test_terms_and_conditions_2():
    u = User(
        addr="27820001001",
        state=StateData(name="state_terms_and_conditions"),
        session_id=1,
    )
    app = Application(u)
    msg = Message(
        content="next",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert u.state.name == "state_terms_and_conditions_2"


@pytest.mark.asyncio
async def test_terms_and_conditions_2_invalid():
    u = User(
        addr="27820001001",
        state=StateData(name="state_terms_and_conditions_2"),
        session_id=1,
    )
    app = Application(u)
    msg = Message(
        content="invalid",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert u.state.name == "state_terms_and_conditions_2"


@pytest.mark.asyncio
async def test_terms_and_conditions_3():
    u = User(
        addr="27820001001",
        state=StateData(name="state_terms_and_conditions_2"),
        session_id=1,
    )
    app = Application(u)
    msg = Message(
        content="next",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert u.state.name == "state_terms_and_conditions_3"


@pytest.mark.asyncio
async def test_terms_and_conditions_3_invalid():
    u = User(
        addr="27820001001",
        state=StateData(name="state_terms_and_conditions_3"),
        session_id=1,
    )
    app = Application(u)
    msg = Message(
        content="invalid",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert u.state.name == "state_terms_and_conditions_3"


@pytest.mark.asyncio
async def test_state_success(evds_mock, eventstore_mock):
    u = User(
        addr="27820001001",
        state=StateData(name="state_medical_aid"),
        session_id=1,
        answers={
            "state_dob_year": "1960",
            "state_dob_month": "1",
            "state_dob_day": "1",
            "state_vaccination_time": "weekday_morning",
            "state_suburb": "d114778e-c590-4a08-894e-0ddaefc5759e",
            "state_province_id": "e32298eb-17b4-471e-8d9b-ba093c6afc7c",
            "state_gender": "Other",
            "state_surname": " test $\nsurname",
            "state_first_name": " test f%irst name ",
            "state_identification_type": "rsa_id",
            "state_identification_number": " 6001 010001081  ",
        },
    )
    app = Application(u)
    msg = Message(
        content="yes",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert (
        reply.content
        == ":) You have SUCCESSFULLY registered to get vaccinated. Additional "
        "information and appointment details will be sent via SMS."
    )
    assert reply.session_event == Message.SESSION_EVENT.CLOSE

    [requests] = evds_mock.tstate.requests
    assert requests.json == {
        "gender": "Other",
        "surname": "test surname",
        "firstName": "test first name",
        "dateOfBirth": "1960-01-01",
        "mobileNumber": "27820001001",
        "preferredVaccineScheduleTimeOfDay": "morning",
        "preferredVaccineScheduleTimeOfWeek": "weekday",
        "preferredVaccineLocation": {
            "value": "d114778e-c590-4a08-894e-0ddaefc5759e",
            "text": "Diep River",
        },
        "termsAndConditionsAccepted": True,
        "iDNumber": "6001010001081",
        "sourceId": "008c0f09-db09-4d60-83c5-63505c7f05ba",
        "medicalAidMember": True,
    }

    [requests] = eventstore_mock.tstate.requests
    assert requests.json == {
        "msisdn": "+27820001001",
        "source": "USSD 27820001002",
        "gender": "Other",
        "first_name": "test first name",
        "last_name": "test surname",
        "date_of_birth": "1960-01-01",
        "preferred_time": "morning",
        "preferred_date": "weekday",
        "preferred_location_id": "d114778e-c590-4a08-894e-0ddaefc5759e",
        "preferred_location_name": "Diep River",
        "id_number": "6001010001081",
        "data": {},
    }


@pytest.mark.asyncio
async def test_state_success_passport(evds_mock, eventstore_mock):
    u = User(
        addr="27820001001",
        state=StateData(name="state_medical_aid"),
        session_id=1,
        answers={
            "state_dob_year": "1960",
            "state_dob_month": "1",
            "state_dob_day": "1",
            "state_vaccination_time": "weekday_morning",
            "state_suburb": "d114778e-c590-4a08-894e-0ddaefc5759e",
            "state_province_id": "e32298eb-17b4-471e-8d9b-ba093c6afc7c",
            "state_gender": "Other",
            "state_surname": "test surname",
            "state_first_name": "test first name",
            "state_identification_type": "passport",
            "state_identification_number": "A1234567890",
            "state_passport_country": "other",
            "state_passport_country_list": "ZA",
        },
    )
    app = Application(u)
    msg = Message(
        content="yes",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert (
        reply.content
        == ":) You have SUCCESSFULLY registered to get vaccinated. Additional "
        "information and appointment details will be sent via SMS."
    )
    assert reply.session_event == Message.SESSION_EVENT.CLOSE

    [requests] = evds_mock.tstate.requests
    assert requests.json == {
        "gender": "Other",
        "surname": "test surname",
        "firstName": "test first name",
        "dateOfBirth": "1960-01-01",
        "mobileNumber": "27820001001",
        "preferredVaccineScheduleTimeOfDay": "morning",
        "preferredVaccineScheduleTimeOfWeek": "weekday",
        "preferredVaccineLocation": {
            "value": "d114778e-c590-4a08-894e-0ddaefc5759e",
            "text": "Diep River",
        },
        "termsAndConditionsAccepted": True,
        "passportNumber": "A1234567890",
        "passportCountry": "ZA",
        "sourceId": "008c0f09-db09-4d60-83c5-63505c7f05ba",
        "medicalAidMember": True,
    }
    [requests] = eventstore_mock.tstate.requests
    assert requests.json == {
        "msisdn": "+27820001001",
        "source": "USSD 27820001002",
        "gender": "Other",
        "first_name": "test first name",
        "last_name": "test surname",
        "date_of_birth": "1960-01-01",
        "preferred_time": "morning",
        "preferred_date": "weekday",
        "preferred_location_id": "d114778e-c590-4a08-894e-0ddaefc5759e",
        "preferred_location_name": "Diep River",
        "passport_number": "A1234567890",
        "passport_country": "ZA",
        "data": {},
    }


@pytest.mark.asyncio
async def test_state_success_passport_from_choosing(evds_mock, eventstore_mock):
    u = User(
        addr="27820001001",
        state=StateData(name="state_medical_aid"),
        session_id=1,
        answers={
            "state_dob_year": "1960",
            "state_dob_month": "1",
            "state_dob_day": "1",
            "state_vaccination_time": "weekday_morning",
            "state_suburb": "d114778e-c590-4a08-894e-0ddaefc5759e",
            "state_province_id": "e32298eb-17b4-471e-8d9b-ba093c6afc7c",
            "state_gender": "Other",
            "state_surname": "test surname",
            "state_first_name": "test first name",
            "state_identification_type": "passport",
            "state_identification_number": "A1234567890",
            "state_passport_country": "ZW",
        },
    )
    app = Application(u)
    msg = Message(
        content="yes",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert (
        reply.content
        == ":) You have SUCCESSFULLY registered to get vaccinated. Additional "
        "information and appointment details will be sent via SMS."
    )
    assert reply.session_event == Message.SESSION_EVENT.CLOSE

    [requests] = evds_mock.tstate.requests
    assert requests.json == {
        "gender": "Other",
        "surname": "test surname",
        "firstName": "test first name",
        "dateOfBirth": "1960-01-01",
        "mobileNumber": "27820001001",
        "preferredVaccineScheduleTimeOfDay": "morning",
        "preferredVaccineScheduleTimeOfWeek": "weekday",
        "preferredVaccineLocation": {
            "value": "d114778e-c590-4a08-894e-0ddaefc5759e",
            "text": "Diep River",
        },
        "termsAndConditionsAccepted": True,
        "passportNumber": "A1234567890",
        "passportCountry": "ZW",
        "sourceId": "008c0f09-db09-4d60-83c5-63505c7f05ba",
        "medicalAidMember": True,
    }
    [requests] = eventstore_mock.tstate.requests
    assert requests.json == {
        "msisdn": "+27820001001",
        "source": "USSD 27820001002",
        "gender": "Other",
        "first_name": "test first name",
        "last_name": "test surname",
        "date_of_birth": "1960-01-01",
        "preferred_time": "morning",
        "preferred_date": "weekday",
        "preferred_location_id": "d114778e-c590-4a08-894e-0ddaefc5759e",
        "preferred_location_name": "Diep River",
        "passport_number": "A1234567890",
        "passport_country": "ZW",
        "data": {},
    }


@pytest.mark.asyncio
async def test_state_success_asylum_seeker(evds_mock, eventstore_mock):
    u = User(
        addr="27820001001",
        state=StateData(name="state_medical_aid"),
        session_id=1,
        answers={
            "state_dob_year": "1960",
            "state_dob_month": "1",
            "state_dob_day": "1",
            "state_vaccination_time": "weekday_morning",
            "state_suburb": "d114778e-c590-4a08-894e-0ddaefc5759e",
            "state_province_id": "e32298eb-17b4-471e-8d9b-ba093c6afc7c",
            "state_gender": "Other",
            "state_surname": "test surname",
            "state_first_name": "test first name",
            "state_identification_type": "asylum_seeker",
            "state_identification_number": "A1234567890",
        },
    )
    app = Application(u)
    msg = Message(
        content="yes",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert (
        reply.content
        == ":) You have SUCCESSFULLY registered to get vaccinated. Additional "
        "information and appointment details will be sent via SMS."
    )
    assert reply.session_event == Message.SESSION_EVENT.CLOSE

    [requests] = evds_mock.tstate.requests
    assert requests.json == {
        "gender": "Other",
        "surname": "test surname",
        "firstName": "test first name",
        "dateOfBirth": "1960-01-01",
        "mobileNumber": "27820001001",
        "preferredVaccineScheduleTimeOfDay": "morning",
        "preferredVaccineScheduleTimeOfWeek": "weekday",
        "preferredVaccineLocation": {
            "value": "d114778e-c590-4a08-894e-0ddaefc5759e",
            "text": "Diep River",
        },
        "termsAndConditionsAccepted": True,
        "refugeeNumber": "A1234567890",
        "sourceId": "008c0f09-db09-4d60-83c5-63505c7f05ba",
        "medicalAidMember": True,
    }

    [requests] = eventstore_mock.tstate.requests
    assert requests.json == {
        "msisdn": "+27820001001",
        "source": "USSD 27820001002",
        "gender": "Other",
        "first_name": "test first name",
        "last_name": "test surname",
        "date_of_birth": "1960-01-01",
        "preferred_time": "morning",
        "preferred_date": "weekday",
        "preferred_location_id": "d114778e-c590-4a08-894e-0ddaefc5759e",
        "preferred_location_name": "Diep River",
        "asylum_seeker_number": "A1234567890",
        "data": {},
    }


@pytest.mark.asyncio
async def test_state_success_refugee(evds_mock, eventstore_mock):
    u = User(
        addr="27820001001",
        state=StateData(name="state_medical_aid"),
        session_id=1,
        answers={
            "state_dob_year": "1960",
            "state_dob_month": "1",
            "state_dob_day": "1",
            "state_vaccination_time": "weekday_morning",
            "state_suburb": "d114778e-c590-4a08-894e-0ddaefc5759e",
            "state_province_id": "e32298eb-17b4-471e-8d9b-ba093c6afc7c",
            "state_gender": "Other",
            "state_surname": "test surname",
            "state_first_name": "test first name",
            "state_identification_type": "refugee",
            "state_identification_number": "A1234567890",
        },
    )
    app = Application(u)
    msg = Message(
        content="yes",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert (
        reply.content
        == ":) You have SUCCESSFULLY registered to get vaccinated. Additional "
        "information and appointment details will be sent via SMS."
    )
    assert reply.session_event == Message.SESSION_EVENT.CLOSE

    [requests] = evds_mock.tstate.requests
    assert requests.json == {
        "gender": "Other",
        "surname": "test surname",
        "firstName": "test first name",
        "dateOfBirth": "1960-01-01",
        "mobileNumber": "27820001001",
        "preferredVaccineScheduleTimeOfDay": "morning",
        "preferredVaccineScheduleTimeOfWeek": "weekday",
        "preferredVaccineLocation": {
            "value": "d114778e-c590-4a08-894e-0ddaefc5759e",
            "text": "Diep River",
        },
        "termsAndConditionsAccepted": True,
        "refugeeNumber": "A1234567890",
        "sourceId": "008c0f09-db09-4d60-83c5-63505c7f05ba",
        "medicalAidMember": True,
    }

    [requests] = eventstore_mock.tstate.requests
    assert requests.json == {
        "msisdn": "+27820001001",
        "source": "USSD 27820001002",
        "gender": "Other",
        "first_name": "test first name",
        "last_name": "test surname",
        "date_of_birth": "1960-01-01",
        "preferred_time": "morning",
        "preferred_date": "weekday",
        "preferred_location_id": "d114778e-c590-4a08-894e-0ddaefc5759e",
        "preferred_location_name": "Diep River",
        "refugee_number": "A1234567890",
        "data": {},
    }


@pytest.mark.asyncio
async def test_state_success_temporary_failure(evds_mock):
    evds_mock.tstate.errormax = 1
    u = User(
        addr="27820001001",
        state=StateData(name="state_medical_aid"),
        session_id=1,
        answers={
            "state_dob_year": "1960",
            "state_dob_month": "1",
            "state_dob_day": "1",
            "state_vaccination_time": "weekday_morning",
            "state_suburb": "d114778e-c590-4a08-894e-0ddaefc5759e",
            "state_province_id": "e32298eb-17b4-471e-8d9b-ba093c6afc7c",
            "state_gender": "Other",
            "state_surname": "test surname",
            "state_first_name": "test first name",
            "state_identification_type": "passport",
            "state_identification_number": "A1234567890",
            "state_passport_country": "other",
            "state_passport_country_list": "ZA",
        },
    )
    app = Application(u)
    msg = Message(
        content="yes",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert (
        reply.content
        == ":) You have SUCCESSFULLY registered to get vaccinated. Additional "
        "information and appointment details will be sent via SMS."
    )
    assert reply.session_event == Message.SESSION_EVENT.CLOSE

    requests = evds_mock.tstate.requests
    assert len(requests) == 2
    assert requests[-1].json == {
        "gender": "Other",
        "surname": "test surname",
        "firstName": "test first name",
        "dateOfBirth": "1960-01-01",
        "mobileNumber": "27820001001",
        "preferredVaccineScheduleTimeOfDay": "morning",
        "preferredVaccineScheduleTimeOfWeek": "weekday",
        "preferredVaccineLocation": {
            "value": "d114778e-c590-4a08-894e-0ddaefc5759e",
            "text": "Diep River",
        },
        "termsAndConditionsAccepted": True,
        "passportNumber": "A1234567890",
        "passportCountry": "ZA",
        "sourceId": "008c0f09-db09-4d60-83c5-63505c7f05ba",
        "medicalAidMember": True,
    }


@pytest.mark.asyncio
async def test_state_error(evds_mock):
    evds_mock.tstate.errormax = 3
    u = User(
        addr="27820001001",
        state=StateData(name="state_medical_aid"),
        session_id=1,
        answers={
            "state_dob_year": "1960",
            "state_dob_month": "1",
            "state_dob_day": "1",
            "state_vaccination_time": "weekday_morning",
            "state_suburb": "d114778e-c590-4a08-894e-0ddaefc5759e",
            "state_province_id": "e32298eb-17b4-471e-8d9b-ba093c6afc7c",
            "state_gender": "Other",
            "state_surname": "test surname",
            "state_first_name": "test first name",
            "state_identification_type": "refugee",
            "state_identification_number": "6001010001081",
        },
    )
    app = Application(u)
    msg = Message(
        content="yes",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert (
        reply.content
        == "Something went wrong with your registration session. Your registration was "
        "not able to be processed. Please try again later"
    )
    assert reply.session_event == Message.SESSION_EVENT.CLOSE

    requests = evds_mock.tstate.requests
    assert len(requests) == 3
    assert requests[-1].json == {
        "gender": "Other",
        "surname": "test surname",
        "firstName": "test first name",
        "dateOfBirth": "1960-01-01",
        "mobileNumber": "27820001001",
        "preferredVaccineScheduleTimeOfDay": "morning",
        "preferredVaccineScheduleTimeOfWeek": "weekday",
        "preferredVaccineLocation": {
            "value": "d114778e-c590-4a08-894e-0ddaefc5759e",
            "text": "Diep River",
        },
        "termsAndConditionsAccepted": True,
        "refugeeNumber": "6001010001081",
        "sourceId": "008c0f09-db09-4d60-83c5-63505c7f05ba",
        "medicalAidMember": True,
    }


@pytest.mark.asyncio
async def test_throttle():
    throttle = config.THROTTLE_PERCENTAGE
    config.THROTTLE_PERCENTAGE = 100.0

    u = User(addr="27820001001")
    app = Application(u)
    msg = Message(
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert reply.content == "\n".join(
        [
            "We are currently experiencing high volumes of registrations.",
            "",
            "Your registration is important! Please try again in 15 minutes",
        ]
    )

    config.THROTTLE_PERCENTAGE = throttle
