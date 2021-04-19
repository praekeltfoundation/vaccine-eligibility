import pytest

from vaccine.healthcheck_ussd import Application as HealthCheckApp
from vaccine.healthcheck_vacreg_ussd import Application
from vaccine.models import Message, StateData, User
from vaccine.vaccine_reg_ussd import Application as VacRegApp


def test_no_state_name_clashes():
    hc_states = set(s for s in dir(HealthCheckApp) if s.startswith("state_"))
    vr_states = set(s for s in dir(VacRegApp) if s.startswith("state_"))
    intersection = (hc_states & vr_states) - {"state_name"}
    assert len(intersection) == 0, f"Common states to both apps: {intersection}"


@pytest.mark.asyncio
async def test_menu():
    u = User(addr="27820001001")
    app = Application(u)
    msg = Message(
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
        session_event=Message.SESSION_EVENT.NEW,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert u.state.name == "state_menu"


@pytest.mark.asyncio
async def test_session_timeout_healthcheck():
    u = User(
        addr="27820001001", state=StateData(name="state_sore_throat"), session_id=1
    )
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
    assert u.state.name == "state_timed_out_healthcheck"
    assert len(reply.content) < 140
    assert u.answers["resume_state"] == "state_sore_throat"
    assert u.session_id != 1


async def test_state_timed_out_vaccinereg():
    u = User(
        addr="27820001001", state=StateData(name="state_vaccination_time"), session_id=1
    )
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
    assert u.state.name == "state_timed_out_vacreg"
    assert len(reply.content) < 140
    assert u.answers["resume_state"] == "state_vaccination_time"
    assert u.session_id != 1
