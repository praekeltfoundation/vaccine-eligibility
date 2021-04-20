from datetime import date
from unittest import mock

import pytest
from sanic import Sanic, response

from vaccine.models import Message, StateData, User
from vaccine.vaccine_reg_ussd import Application, config


@pytest.fixture
async def evds_mock(sanic_client):
    Sanic.test_mode = True
    app = Sanic("mock_turn")
    app.requests = []
    app.errors = 0
    app.errormax = 0

    @app.route("/api/private/evds-sa/person/1/record", methods=["POST"])
    def submit_record(request):
        app.requests.append(request)
        if app.errormax:
            if app.errors < app.errormax:
                app.errors += 1
                return response.json({}, status=500)
        return response.json({}, status=200)

    client = await sanic_client(app)
    url = config.EVDS_URL
    username = config.EVDS_USERNAME
    password = config.EVDS_PASSWORD
    config.EVDS_URL = f"http://{client.host}:{client.port}"
    config.EVDS_USERNAME = "test"
    config.EVDS_PASSWORD = "test"
    yield client
    config.EVDS_URL = url
    config.EVDS_USERNAME = username
    config.EVDS_PASSWORD = password


@pytest.mark.asyncio
async def test_age_gate():
    """
    Should ask the user if they're over 60
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
    assert len(reply.content) < 140
    assert u.state.name == "state_age_gate"


@pytest.mark.asyncio
async def test_age_gate_error():
    """
    Should show the error message on incorrect input
    """
    u = User(addr="27820001001", state=StateData(name="state_age_gate"))
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
async def test_under_age_notification():
    """
    Should ask the user if they want a notification when it opens up
    """
    u = User(addr="27820001001", state=StateData(name="state_age_gate"), session_id=1)
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
    assert u.state.name == "state_under_age_notification"


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
    u = User(addr="27820001001", state=StateData(name="state_age_gate"), session_id=1)
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
    assert u.state.name == "state_terms_and_conditions"


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
        content="rsa id number",
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
        answers={"state_identification_type": Application.ID_TYPES.rsa_id.name},
        session_id=1,
    )
    app = Application(u)
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
async def test_passport_country():
    u = User(
        addr="27820001001",
        state=StateData(name="state_identification_number"),
        session_id=1,
        answers={"state_identification_type": Application.ID_TYPES.passport.name},
    )
    app = Application(u)
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
async def test_said_date_and_sex_extraction():
    u = User(
        addr="27820001001",
        state=StateData(name="state_identification_number"),
        answers={"state_identification_type": Application.ID_TYPES.rsa_id.name},
        session_id=1,
    )
    app = Application(u)
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
@mock.patch("vaccine.utils.get_today")
async def test_said_date_extraction_ambiguous(get_today):
    get_today.return_value = date(2020, 1, 1)
    u = User(
        addr="27820001001",
        state=StateData(name="state_identification_number"),
        answers={"state_identification_type": Application.ID_TYPES.rsa_id.name},
        session_id=1,
    )
    app = Application(u)
    msg = Message(
        content="0001010001087",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    await app.process_message(msg)
    assert "state_dob_year" not in u.answers
    assert u.answers["state_dob_month"] == "1"
    assert u.answers["state_dob_day"] == "1"


@pytest.mark.asyncio
async def test_gender():
    u = User(
        addr="27820001001",
        state=StateData(name="state_identification_number"),
        answers={"state_identification_type": Application.ID_TYPES.asylum_seeker.name},
        session_id=1,
    )
    app = Application(u)
    msg = Message(
        content="9001010001088",
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
        answers={"state_identification_type": Application.ID_TYPES.rsa_id.name},
    )
    app = Application(u)
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
        answers={"state_identification_type": Application.ID_TYPES.rsa_id.name},
    )
    app = Application(u)
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
async def test_dob_year_not_match_id():
    u = User(
        addr="27820001001",
        state=StateData(name="state_dob_year"),
        session_id=1,
        answers={
            "state_identification_type": Application.ID_TYPES.rsa_id.value,
            "state_identification_number": "9001010001088",
        },
    )
    app = Application(u)
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
    u = User(
        addr="27820001001",
        state=StateData(name="state_dob_year"),
        session_id=1,
        answers={"state_identification_type": Application.ID_TYPES.asylum_seeker.value},
    )
    app = Application(u)
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
            "state_identification_type": Application.ID_TYPES.refugee.name,
            "state_identification_number": "012345678901234567890123456789",
        },
    )
    app = Application(u)
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
            "state_identification_type": Application.ID_TYPES.refugee.name,
            "state_identification_number": "0123456789012345678901234567891234567890",
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
            "state_identification_type": Application.ID_TYPES.refugee.name,
            "state_identification_number": "012345678901234567890123456789",
        },
    )
    app = Application(u)
    msg = Message(
        content="wrong",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert u.state.name == "state_identification_type"


@pytest.mark.asyncio
async def test_province():
    u = User(
        addr="27820001001",
        state=StateData(name="state_confirm_profile"),
        session_id=1,
        answers={
            "state_first_name": "reallyreallylongfirstname1234567890",
            "state_surname": "reallyreallylongsurname124567890",
            "state_identification_type": Application.ID_TYPES.refugee.name,
            "state_identification_number": "012345678901234567890123456789",
        },
    )
    app = Application(u)
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
async def test_province_invalid():
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
async def test_suburb_search():
    u = User(
        addr="27820001001", state=StateData(name="state_province_id"), session_id=1
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
    assert u.answers["state_province_id"] == "e32298eb-17b4-471e-8d9b-ba093c6afc7c"


@pytest.mark.asyncio
async def test_suburb():
    u = User(
        addr="27820001001",
        state=StateData(name="state_suburb_search"),
        session_id=1,
        answers={"state_province_id": "e32298eb-17b4-471e-8d9b-ba093c6afc7c"},
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
            "1. Table View",
            "2. Bayview",
            "3. Ballotsview",
            "4. Other",
        ]
    )
    assert u.state.name == "state_suburb"


@pytest.mark.asyncio
async def test_suburb_error():
    u = User(
        addr="27820001001",
        state=StateData(name="state_suburb"),
        session_id=1,
        answers={
            "state_province_id": "e32298eb-17b4-471e-8d9b-ba093c6afc7c",
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
async def test_suburb_other():
    u = User(
        addr="27820001001",
        state=StateData(name="state_suburb"),
        session_id=1,
        answers={
            "state_province_id": "e32298eb-17b4-471e-8d9b-ba093c6afc7c",
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
async def test_self_registration():
    u = User(
        addr="27820001001",
        state=StateData(name="state_suburb"),
        session_id=1,
        answers={
            "state_province_id": "e32298eb-17b4-471e-8d9b-ba093c6afc7c",
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
        content="yes",
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
async def test_state_success(evds_mock):
    u = User(
        addr="27820001001",
        state=StateData(name="state_medical_aid"),
        session_id=1,
        answers={
            "state_dob_year": "1960",
            "state_dob_month": "1",
            "state_dob_day": "1",
            "state_vaccination_time": "weekday_morning",
            "state_suburb": "f4cba53d-a757-45a7-93ca-895b010e60c2",
            "state_province_id": "e32298eb-17b4-471e-8d9b-ba093c6afc7c",
            "state_gender": "Other",
            "state_surname": "test surname",
            "state_first_name": "test first name",
            "state_identification_type": "rsa_id",
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
        == ":) You have SUCCESSFULLY registered to get vaccinated. Additional "
        "information and appointment details will be sent via SMS."
    )
    assert reply.session_event == Message.SESSION_EVENT.CLOSE

    [requests] = evds_mock.app.requests
    assert requests.json == {
        "gender": "Other",
        "surname": "test surname",
        "firstName": "test first name",
        "dateOfBirth": "1960-01-01",
        "mobileNumber": "+27820001001",
        "preferredVaccineScheduleTimeOfDay": "morning",
        "preferredVaccineScheduleTimeOfWeek": "weekday",
        "preferredVaccineLocation": {
            "value": "f4cba53d-a757-45a7-93ca-895b010e60c2",
            "text": "Diep River",
        },
        "termsAndConditionsAccepted": True,
        "iDNumber": "6001010001081",
    }


@pytest.mark.asyncio
async def test_state_success_temporary_failure(evds_mock):
    evds_mock.app.errormax = 1
    u = User(
        addr="27820001001",
        state=StateData(name="state_medical_aid"),
        session_id=1,
        answers={
            "state_dob_year": "1960",
            "state_dob_month": "1",
            "state_dob_day": "1",
            "state_vaccination_time": "weekday_morning",
            "state_suburb": "f4cba53d-a757-45a7-93ca-895b010e60c2",
            "state_province_id": "e32298eb-17b4-471e-8d9b-ba093c6afc7c",
            "state_gender": "Other",
            "state_surname": "test surname",
            "state_first_name": "test first name",
            "state_identification_type": "passport",
            "state_identification_number": "A1234567890",
            "state_passport_country": "other",
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

    requests = evds_mock.app.requests
    assert len(requests) == 2
    assert requests[-1].json == {
        "gender": "Other",
        "surname": "test surname",
        "firstName": "test first name",
        "dateOfBirth": "1960-01-01",
        "mobileNumber": "+27820001001",
        "preferredVaccineScheduleTimeOfDay": "morning",
        "preferredVaccineScheduleTimeOfWeek": "weekday",
        "preferredVaccineLocation": {
            "value": "f4cba53d-a757-45a7-93ca-895b010e60c2",
            "text": "Diep River",
        },
        "termsAndConditionsAccepted": True,
        "passportNumber": "A1234567890",
        "passportCountry": "other",
    }


@pytest.mark.asyncio
async def test_state_error(evds_mock):
    evds_mock.app.errormax = 3
    u = User(
        addr="27820001001",
        state=StateData(name="state_medical_aid"),
        session_id=1,
        answers={
            "state_dob_year": "1960",
            "state_dob_month": "1",
            "state_dob_day": "1",
            "state_vaccination_time": "weekday_morning",
            "state_suburb": "f4cba53d-a757-45a7-93ca-895b010e60c2",
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

    requests = evds_mock.app.requests
    assert len(requests) == 3
    assert requests[-1].json == {
        "gender": "Other",
        "surname": "test surname",
        "firstName": "test first name",
        "dateOfBirth": "1960-01-01",
        "mobileNumber": "+27820001001",
        "preferredVaccineScheduleTimeOfDay": "morning",
        "preferredVaccineScheduleTimeOfWeek": "weekday",
        "preferredVaccineLocation": {
            "value": "f4cba53d-a757-45a7-93ca-895b010e60c2",
            "text": "Diep River",
        },
        "termsAndConditionsAccepted": True,
        "refugeeNumber": "6001010001081",
    }
