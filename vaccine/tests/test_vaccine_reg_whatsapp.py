import gzip
from datetime import date
from unittest import mock

import pytest
from sanic import Sanic, response

from vaccine.data.medscheme import config as m_config
from vaccine.data.suburbs import config as s_config
from vaccine.models import Message, StateData, User
from vaccine.vaccine_reg_whatsapp import Application, config


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

    @app.route("/api/private/evds-sa/person/1/lookup/medscheme/1", methods=["GET"])
    def get_medschemes(request):
        with gzip.open("vaccine/data/medscheme.json.gz") as f:
            return response.raw(f.read(), content_type="application/json")

    @app.route("/api/private/evds-sa/person/1/lookup/location/1", methods=["GET"])
    def get_suburbs(request):
        with gzip.open("vaccine/data/suburbs.json.gz") as f:
            return response.raw(f.read(), content_type="application/json")

    client = await sanic_client(app)
    url = config.EVDS_URL
    username = config.EVDS_USERNAME
    password = config.EVDS_PASSWORD
    s_config.EVDS_URL = (
        m_config.EVDS_URL
    ) = config.EVDS_URL = f"http://{client.host}:{client.port}"
    s_config.EVDS_USERNAME = m_config.EVDS_USERNAME = config.EVDS_USERNAME = "test"
    s_config.EVDS_PASSWORD = m_config.EVDS_PASSWORD = config.EVDS_PASSWORD = "test"
    yield client
    s_config.EVDS_URL = m_config.EVDS_URL = config.EVDS_URL = url
    s_config.EVDS_USERNAME = m_config.EVDS_USERNAME = config.EVDS_USERNAME = username
    s_config.EVDS_PASSWORD = m_config.EVDS_PASSWORD = config.EVDS_PASSWORD = password


@pytest.fixture
async def eventstore_mock(sanic_client):
    Sanic.test_mode = True
    app = Sanic("mock_eventstore")
    app.requests = []
    app.registration_errormax = 0
    app.registration_errors = 0

    @app.route("/v2/vaccineregistration/", methods=["POST"])
    def valid_registration(request):
        app.requests.append(request)
        if app.registration_errormax:
            if app.registration_errors < app.registration_errormax:
                app.registration_errors += 1
                return response.json({}, status=500)
        return response.json({})

    client = await sanic_client(app)
    url = config.VACREG_EVENTSTORE_URL
    config.VACREG_EVENTSTORE_URL = f"http://{client.host}:{client.port}"
    yield client
    config.VACREG_EVENTSTORE_URL = url


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
    assert reply.content == "Thank you for confirming"
    assert reply.session_event == Message.SESSION_EVENT.CLOSE


@pytest.mark.asyncio
async def test_identification_type():
    u = User(addr="27820001001", state=StateData(name="state_age_gate"), session_id=1)
    app = Application(u)
    msg = Message(
        content="1",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [pdf, reply] = await app.process_message(msg)
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
    assert u.state.name == "state_passport_country"


@pytest.mark.asyncio
async def test_passport_country_search():
    u = User(
        addr="27820001001", state=StateData(name="state_passport_country"), session_id=1
    )
    app = Application(u)
    msg = Message(
        content="cote d'ivory",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert u.state.name == "state_passport_country_list"
    assert u.answers["state_passport_country"] == "cote d'ivory"

    assert reply.content == "\n".join(
        [
            "*VACCINE REGISTRATION SECURE CHAT* 🔐",
            "",
            "Please confirm your passport's COUNTRY of origin. REPLY with a "
            "NUMBER from the list below:",
            "1. Republic of Côte d'Ivoire",
            "2. Plurinational State of Bolivia",
            "3. Swiss Confederation",
            "4. Other",
        ]
    )


@pytest.mark.asyncio
async def test_passport_country_search_other():
    u = User(
        addr="27820001001",
        state=StateData(name="state_passport_country_list"),
        session_id=1,
        answers={"state_passport_country": "CI"},
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
    assert u.state.name == "state_passport_country"


@pytest.mark.asyncio
async def test_passport_country_search_list_invalid():
    u = User(
        addr="27820001001",
        state=StateData(name="state_passport_country_list"),
        session_id=1,
        answers={"state_passport_country": "Côte d'Ivoire"},
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
@mock.patch("vaccine.utils.get_today")
async def test_gender(get_today):
    get_today.return_value = date(2120, 1, 1)
    u = User(
        addr="27820001001",
        state=StateData(name="state_dob_day"),
        answers={"state_dob_year": "1990", "state_dob_month": "1"},
        session_id=1,
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
    assert u.state.name == "state_gender"


@pytest.mark.asyncio
@mock.patch("vaccine.utils.get_today")
async def test_gender_invalid(get_today):
    get_today.return_value = date(2120, 1, 1)
    u = User(
        addr="27820001001",
        state=StateData(name="state_gender"),
        session_id=1,
        answers={
            "state_dob_year": "1990",
            "state_dob_month": "1",
            "state_dob_day": "1",
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
    assert u.state.name == "state_gender"


@pytest.mark.asyncio
@mock.patch("vaccine.utils.get_today")
async def test_too_young(get_today):
    get_today.return_value = date(2020, 1, 1)
    u = User(
        addr="27820001001",
        state=StateData(name="state_dob_year"),
        session_id=1,
        answers={
            "state_dob_month": "1",
            "state_dob_day": "1",
            "state_identification_type": "passport",
        },
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
    assert u.state.name == "state_under_age_notification"


@pytest.mark.asyncio
async def test_dob_year():
    u = User(addr="27820001001", state=StateData(name="state_surname"), session_id=1)
    app = Application(u)
    msg = Message(
        content="test surname",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
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
    assert u.state.name == "state_dob_year"
    assert reply.content == "\n".join(
        ["⚠️  Please TYPE in only the YEAR you were born.", "Example _1980_"]
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
    assert u.state.name == "state_dob_month"


@pytest.mark.asyncio
async def test_dob_day():
    u = User(addr="27820001001", state=StateData(name="state_dob_month"), session_id=1)
    app = Application(u)
    msg = Message(
        content="january",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
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
    assert u.state.name == "state_dob_day"


@pytest.mark.asyncio
async def test_first_name():
    u = User(
        addr="27820001001",
        state=StateData(name="state_passport_country_list"),
        session_id=1,
        answers={"state_passport_country": "south africa"},
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
    assert u.state.name == "state_first_name"


@pytest.mark.asyncio
async def test_surname():
    u = User(addr="27820001001", state=StateData(name="state_first_name"), session_id=1)
    app = Application(u)
    msg = Message(
        content="firstname",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert u.state.name == "state_surname"
    assert u.answers["state_first_name"] == "firstname"


@pytest.mark.asyncio
@mock.patch("vaccine.utils.get_today")
async def test_skip_dob_and_gender(get_today, evds_mock):
    get_today.return_value = date(2120, 1, 1)
    u = User(
        addr="27820001001",
        state=StateData(name="state_surname"),
        session_id=1,
        answers={
            "state_dob_day": "1",
            "state_dob_month": "1",
            "state_dob_year": "1990",
            "state_gender": "male",
        },
    )
    app = Application(u)
    msg = Message(
        content="test surname",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert u.state.name == "state_province_id"


@pytest.mark.asyncio
async def test_province(evds_mock):
    u = User(
        addr="27820001001",
        state=StateData(name="state_terms_and_conditions"),
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
    assert u.state.name == "state_suburb_search"
    assert u.answers["state_province_id"] == "western cape"


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
    assert reply.content == "\n".join(
        [
            "*VACCINE REGISTRATION SECURE CHAT* 🔐",
            "Please REPLY with a NUMBER to confirm your location:",
            "1. Table View, Milnerton, City Of Cape Town",
            "2. Mountainview, Cape Town, City Of Cape Town",
            "3. Mountainview, Strand, City Of Cape Town",
            "4. Other",
        ]
    )
    assert u.state.name == "state_suburb"


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
    assert u.state.name == "state_province_id"


@pytest.mark.asyncio
async def test_suburb_value(evds_mock):
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
    assert u.state.name == "state_self_registration"


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
    assert reply.content == "\n".join(
        [
            "*VACCINE REGISTRATION SECURE CHAT* 🔐",
            "",
            "We will use your cell phone number to send you notifications and updates "
            "via WhatsApp and/or SMS about getting vaccinated.",
            "Can we use 082 000 1001?",
            "1. Yes",
            "2. No",
        ]
    )
    assert u.state.name == "state_self_registration"


@pytest.mark.asyncio
@mock.patch("vaccine.utils.get_today")
async def test_self_registration_invalid(get_today):
    get_today.return_value = date(2100, 1, 1)
    u = User(
        addr="27820001001",
        state=StateData(name="state_self_registration"),
        session_id=1,
        answers={
            "state_dob_year": "1990",
            "state_dob_month": "1",
            "state_dob_day": "1",
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
    assert u.state.name == "state_self_registration"


@pytest.mark.asyncio
@mock.patch("vaccine.utils.get_today")
async def test_phone_number(get_today):
    get_today.return_value = date(2100, 1, 1)
    u = User(
        addr="27820001001",
        state=StateData(name="state_self_registration"),
        session_id=1,
        answers={
            "state_dob_year": "1990",
            "state_dob_month": "1",
            "state_dob_day": "1",
        },
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
    assert u.state.name == "state_phone_number"


@pytest.mark.asyncio
@mock.patch("vaccine.utils.get_today")
async def test_phone_number_invalid(get_today):
    get_today.return_value = date(2100, 1, 1)
    u = User(
        addr="27820001001",
        state=StateData(name="state_phone_number"),
        session_id=1,
        answers={
            "state_dob_year": "1990",
            "state_dob_month": "1",
            "state_dob_day": "1",
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
    assert u.state.name == "state_phone_number"


@pytest.mark.asyncio
async def test_vaccination_time():
    u = User(
        addr="27820001001",
        state=StateData(name="state_medical_aid_number"),
        session_id=1,
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
    assert u.state.name == "state_vaccination_time"


@pytest.mark.asyncio
async def test_medical_aid_search():
    u = User(
        addr="27820001001", state=StateData(name="state_medical_aid"), session_id=1
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
    assert u.state.name == "state_medical_aid_search"


@pytest.mark.asyncio
async def test_medical_aid_list_1(evds_mock):
    u = User(
        addr="27820001001",
        state=StateData(name="state_medical_aid_search"),
        session_id=1,
    )
    app = Application(u)
    msg = Message(
        content="discovery",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert u.state.name == "state_medical_aid_list"
    assert reply.content == "\n".join(
        [
            "*VACCINE REGISTRATION SECURE CHAT* 🔐",
            "",
            "Please confirm your Medical Aid Provider. REPLY with a NUMBER from the "
            "list below:",
            "1. Discovery Health Medical Scheme",
            "2. Aeci Medical Aid Society",
            "3. BMW Employees Medical Aid Society",
            "4. None of these",
        ]
    )


@pytest.mark.asyncio
async def test_medical_aid_list_2(evds_mock):
    u = User(
        addr="27820001001",
        state=StateData(name="state_medical_aid_search"),
        session_id=1,
    )
    app = Application(u)
    msg = Message(
        content="tsogo sun",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert u.state.name == "state_medical_aid_list"
    assert reply.content == "\n".join(
        [
            "*VACCINE REGISTRATION SECURE CHAT* 🔐",
            "",
            "Please confirm your Medical Aid Provider. REPLY with a NUMBER from the "
            "list below:",
            "1. Tsogo Sun Group Medical Scheme",
            "2. Golden Arrows Employees Medical Benefit Fund",
            "3. Government Employees Medical Scheme (GEMS)",
            "4. None of these",
        ]
    )


@pytest.mark.asyncio
async def test_medical_aid_list_3(evds_mock):
    u = User(
        addr="27820001001",
        state=StateData(name="state_medical_aid_search"),
        session_id=1,
    )
    app = Application(u)
    msg = Message(
        content="de beers",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert u.state.name == "state_medical_aid_list"
    assert reply.content == "\n".join(
        [
            "*VACCINE REGISTRATION SECURE CHAT* 🔐",
            "",
            "Please confirm your Medical Aid Provider. REPLY with a NUMBER from the "
            "list below:",
            "1. De Beers Benefit Society",
            "2. South African Breweries Medical Aid Scheme (SABMAS)",
            "3. BMW Employees Medical Aid Society",
            "4. None of these",
        ]
    )


@pytest.mark.asyncio
async def test_medical_aid_list_other(evds_mock):
    u = User(
        addr="27820001001",
        state=StateData(name="state_medical_aid_list"),
        session_id=1,
        answers={"state_medical_aid_search": "discovery"},
    )
    app = Application(u)
    msg = Message(
        content="4",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert u.state.name == "state_medical_aid_search"


@pytest.mark.asyncio
async def test_medical_aid_number(evds_mock):
    u = User(
        addr="27820001001",
        state=StateData(name="state_medical_aid_list"),
        session_id=1,
        answers={"state_medical_aid_search": "discovery"},
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
    assert u.state.name == "state_medical_aid_number"


@pytest.mark.asyncio
async def test_medical_aid():
    u = User(
        addr="27820001001", state=StateData(name="state_email_address"), session_id=1
    )
    app = Application(u)
    msg = Message(
        content="test@example.org",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
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
    assert u.state.name == "state_medical_aid"


@pytest.mark.asyncio
async def test_email_address():
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
    assert u.state.name == "state_email_address"


@pytest.mark.asyncio
async def test_email_skip():
    u = User(
        addr="27820001001", state=StateData(name="state_email_address"), session_id=1
    )
    app = Application(u)
    msg = Message(
        content="skip",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert u.state.name == "state_medical_aid"


@pytest.mark.asyncio
async def test_email_invalid():
    u = User(
        addr="27820001001", state=StateData(name="state_email_address"), session_id=1
    )
    app = Application(u)
    msg = Message(
        content="invalid@",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert u.state.name == "state_email_address"


@pytest.mark.asyncio
async def test_email_invalid_2():
    u = User(
        addr="27820001001", state=StateData(name="state_email_address"), session_id=1
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
    assert u.state.name == "state_email_address"


@pytest.mark.asyncio
async def test_terms_and_conditions():
    u = User(addr="27820001001", state=StateData(name="state_age_gate"), session_id=1)
    app = Application(u)
    msg = Message(
        content="1",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [pdf, reply] = await app.process_message(msg)
    assert "document" in pdf.helper_metadata
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
    assert u.state.name == "state_terms_and_conditions"


@pytest.mark.asyncio
async def test_terms_and_conditions_summary():
    u = User(
        addr="27820001001",
        state=StateData(name="state_terms_and_conditions"),
        session_id=1,
    )
    app = Application(u)
    msg = Message(
        content="read summary",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert u.state.name == "state_terms_and_conditions_summary"


@pytest.mark.asyncio
async def test_no_terms():
    u = User(
        addr="27820001001",
        state=StateData(name="state_terms_and_conditions_summary"),
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
    assert reply.content == "\n".join(
        [
            "*VACCINE REGISTRATION SECURE CHAT* 🔐",
            "",
            "Thank you. If you change your mind, type *REGISTER* to restart your "
            "registration session",
        ]
    )
    assert reply.session_event == Message.SESSION_EVENT.CLOSE


@pytest.mark.asyncio
async def test_state_success(evds_mock, eventstore_mock):
    u = User(
        addr="27820001001",
        state=StateData(name="state_vaccination_time"),
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
            "state_medical_aid": "state_vaccination_time",
            "state_email_address": "SKIP",
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
    assert reply.content == "\n".join(
        [
            "*VACCINE REGISTRATION SECURE CHAT* 🔐",
            "",
            "Congratulations! You successfully registered with the National Department "
            "of Health to get a COVID-19 vaccine.",
            "",
            "Look out for messages from this number (060 012 3456) on WhatsApp OR on "
            "SMS/email. We will update you with important information about your "
            "appointment and what to expect.",
        ]
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
        "residentialLocation": {
            "value": "f4cba53d-a757-45a7-93ca-895b010e60c2",
            "text": "Diep River",
        },
        "termsAndConditionsAccepted": True,
        "iDNumber": "6001010001081",
        "medicalAidMember": False,
        "sourceId": "aeb8444d-cfa4-4c52-bfaf-eed1495124b7",
    }

    [requests] = eventstore_mock.app.requests
    assert requests.json == {
        "msisdn": "+27820001001",
        "source": "WhatsApp 27820001002",
        "gender": "Other",
        "first_name": "test first name",
        "last_name": "test surname",
        "date_of_birth": "1960-01-01",
        "preferred_time": "morning",
        "preferred_date": "weekday",
        "preferred_location_id": "f4cba53d-a757-45a7-93ca-895b010e60c2",
        "preferred_location_name": "Diep River",
        "id_number": "6001010001081",
        "data": {},
    }


@pytest.mark.asyncio
async def test_state_success_passport(evds_mock):
    u = User(
        addr="27820001001",
        state=StateData(name="state_vaccination_time"),
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
            "state_passport_country": "south africa",
            "state_passport_country_list": "ZA",
            "state_medical_aid": "state_vaccination_time",
            "state_email_address": "SKIP",
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
    assert reply.content == "\n".join(
        [
            "*VACCINE REGISTRATION SECURE CHAT* 🔐",
            "",
            "Congratulations! You successfully registered with the National Department "
            "of Health to get a COVID-19 vaccine.",
            "",
            "Look out for messages from this number (060 012 3456) on WhatsApp OR on "
            "SMS/email. We will update you with important information about your "
            "appointment and what to expect.",
        ]
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
        "residentialLocation": {
            "value": "f4cba53d-a757-45a7-93ca-895b010e60c2",
            "text": "Diep River",
        },
        "termsAndConditionsAccepted": True,
        "passportNumber": "A1234567890",
        "passportCountry": "ZA",
        "medicalAidMember": False,
        "sourceId": "aeb8444d-cfa4-4c52-bfaf-eed1495124b7",
    }


@pytest.mark.asyncio
async def test_state_success_temporary_failure(evds_mock):
    evds_mock.app.errormax = 1
    u = User(
        addr="27820001001",
        state=StateData(name="state_vaccination_time"),
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
            "state_passport_country": "south africa",
            "state_passport_country_list": "ZA",
            "state_medical_aid": "state_vaccination_time",
            "state_email_address": "test@example.org",
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
    assert reply.content == "\n".join(
        [
            "*VACCINE REGISTRATION SECURE CHAT* 🔐",
            "",
            "Congratulations! You successfully registered with the National Department "
            "of Health to get a COVID-19 vaccine.",
            "",
            "Look out for messages from this number (060 012 3456) on WhatsApp OR on "
            "SMS/email. We will update you with important information about your "
            "appointment and what to expect.",
        ]
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
        "residentialLocation": {
            "value": "f4cba53d-a757-45a7-93ca-895b010e60c2",
            "text": "Diep River",
        },
        "termsAndConditionsAccepted": True,
        "passportNumber": "A1234567890",
        "passportCountry": "ZA",
        "emailAddress": "test@example.org",
        "medicalAidMember": False,
        "sourceId": "aeb8444d-cfa4-4c52-bfaf-eed1495124b7",
    }


@pytest.mark.asyncio
async def test_state_error(evds_mock):
    evds_mock.app.errormax = 3
    u = User(
        addr="27820001001",
        state=StateData(name="state_vaccination_time"),
        session_id=1,
        answers={
            "state_dob_year": "1960",
            "state_dob_month": "1",
            "state_dob_day": "1",
            "state_gender": "Other",
            "state_suburb": "f4cba53d-a757-45a7-93ca-895b010e60c2",
            "state_province_id": "e32298eb-17b4-471e-8d9b-ba093c6afc7c",
            "state_gender": "Other",
            "state_surname": "test surname",
            "state_first_name": "test first name",
            "state_identification_type": "refugee",
            "state_identification_number": "6001010001081",
            "state_medical_aid": "state_medical_aid_search",
            "state_medical_aid_search": "discovery",
            "state_medical_aid_list": "971672ba-bb31-4fca-945a-7c530b8b5558",
            "state_medical_aid_number": "M1234567890",
            "state_vaccination_time": "weekday_morning",
            "state_email_address": "SKIP",
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
        "residentialLocation": {
            "value": "f4cba53d-a757-45a7-93ca-895b010e60c2",
            "text": "Diep River",
        },
        "termsAndConditionsAccepted": True,
        "refugeeNumber": "6001010001081",
        "medicalAidMember": True,
        "medicalAidScheme": {
            "text": "Discovery Health Medical Scheme",
            "value": "971672ba-bb31-4fca-945a-7c530b8b5558",
        },
        "medicalAidSchemeNumber": "M1234567890",
        "sourceId": "aeb8444d-cfa4-4c52-bfaf-eed1495124b7",
    }


@pytest.mark.asyncio
async def test_timeout():
    u = User(
        addr="27820001001", state=StateData(name="state_passport_country"), session_id=1
    )
    app = Application(u)
    msg = Message(
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
        session_event=Message.SESSION_EVENT.CLOSE,
    )
    [reply] = await app.process_message(msg)
    assert reply.content == "\n".join(
        [
            "*VACCINE REGISTRATION SECURE CHAT* 🔐",
            "",
            "We haven’t heard from you in a while!",
            "",
            "The registration session has timed out due to inactivity. You will need "
            "to start again. Just TYPE the word REGISTER.",
            "",
            "-----",
            "📌 Reply *0* to return to the main *MENU*",
        ]
    )
    assert reply.session_event == Message.SESSION_EVENT.CLOSE
