import pytest

from vaccine.models import Message, StateData, User
from vaccine.vaccine_reg_ussd import Application


@pytest.mark.asyncio
async def test_age_gate():
    """
    Should ask the user if they're over 40
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
async def test_under40_notification():
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
    assert u.state.name == "state_under40_notification"


@pytest.mark.asyncio
async def test_under40_notification_error():
    """
    Should show the error message on incorrect input
    """
    u = User(
        addr="27820001001",
        state=StateData(name="state_under40_notification"),
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
    assert u.state.name == "state_under40_notification"


@pytest.mark.asyncio
async def test_under40_notification_confirm():
    """
    Should confirm the selection and end the session
    """
    u = User(
        addr="27820001001",
        state=StateData(name="state_under40_notification"),
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
    assert u.answers["state_under40_notification"] == "yes"
    assert u.state.name == "state_age_gate"
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
async def test_gender():
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


@pytest.mark.asyncio
async def test_dob_month():
    u = User(addr="27820001001", state=StateData(name="state_dob_year"), session_id=1)
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
async def test_first_name():
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


@pytest.mark.asyncio
async def test_state_confirm_profile_invalid():
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
        content="no",
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
        content="yes",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert u.state.name == "state_province"


@pytest.mark.asyncio
async def test_province_invalid():
    u = User(addr="27820001001", state=StateData(name="state_province"), session_id=1)
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
    assert u.state.name == "state_province"
