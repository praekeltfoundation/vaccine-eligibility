from datetime import date
from unittest import mock

import pytest

from vaccine.healthcheck_ussd import Application as HealthCheckApp
from vaccine.healthcheck_vacreg_ussd import Application
from vaccine.models import Message, StateData, User
from vaccine.testing import AppTester
from vaccine.vaccine_reg_ussd import Application as VacRegApp


def test_no_state_name_clashes():
    hc_states = set(s for s in dir(HealthCheckApp) if s.startswith("state_"))
    vr_states = set(s for s in dir(VacRegApp) if s.startswith("state_"))
    intersection = (hc_states & vr_states) - {"state_name", "state_error"}
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
    assert u.state.name == "state_language"


@pytest.mark.asyncio
@mock.patch("vaccine.utils.get_today")
async def test_menu_with_id_number(get_today):
    get_today.return_value = date(2021, 1, 1)

    # English language choice
    u = User(addr="27820001001")
    app = Application(u)
    msg = Message(
        to_addr="*123*456*6001210001089#",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
        session_event=Message.SESSION_EVENT.NEW,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160

    app = Application(u)
    msg = Message(
        content="1",
        to_addr="*123*456*6001210001089#",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert u.state.name == "state_terms_and_conditions"
    assert u.answers["state_identification_type"] == "rsa_id"
    assert u.answers["state_identification_number"] == "6001210001089"
    assert u.answers["state_dob_year"] == "1960"
    assert u.answers["state_dob_month"] == "1"
    assert u.answers["state_dob_day"] == "21"
    assert u.answers["state_gender"] == "Female"

    # Accept All Terms Screens
    app = Application(u)
    msg = Message(
        content="1",
        to_addr="*123*456*6001210001089#",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert u.state.name == "state_terms_and_conditions_2"

    app = Application(u)
    msg = Message(
        content="1",
        to_addr="*123*456*6001210001089#",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert u.state.name == "state_terms_and_conditions_3"

    app = Application(u)
    msg = Message(
        content="1",
        to_addr="*123*456*6001210001089#",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert u.state.name == "state_first_name"


@pytest.mark.asyncio
@mock.patch("vaccine.utils.get_today")
async def test_menu_with_id_number_not_eligible(get_today):
    get_today.return_value = date(2021, 1, 1)

    # English language choice
    u = User(addr="27820001001")
    app = Application(u)
    msg = Message(
        to_addr="*123*456*9001010001088#",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
        session_event=Message.SESSION_EVENT.NEW,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160

    app = Application(u)
    msg = Message(
        content="1",
        to_addr="*123*456*9001010001088#",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert u.state.name == "state_under_age_notification"


@pytest.mark.asyncio
@mock.patch("vaccine.utils.get_today")
async def test_menu_with_id_number_invalid(get_today):
    get_today.return_value = date(2021, 1, 1)

    # English language choice
    u = User(addr="27820001001")
    app = Application(u)
    msg = Message(
        to_addr="*123*456*9001010001000#",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
        session_event=Message.SESSION_EVENT.NEW,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160

    app = Application(u)
    msg = Message(
        content="1",
        to_addr="*123*456*9001010001000#",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert u.state.name == "state_menu"


@pytest.mark.asyncio
@mock.patch("vaccine.utils.get_today")
async def test_menu_with_no_id_number(get_today):
    get_today.return_value = date(2021, 1, 1)

    # English language choice
    u = User(addr="27820001001")
    app = Application(u)
    msg = Message(
        to_addr="*123*456*7#",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
        session_event=Message.SESSION_EVENT.NEW,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160

    app = Application(u)
    msg = Message(
        content="1",
        to_addr="*123*456*7#",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert u.state.name == "state_menu"


@pytest.mark.asyncio
@mock.patch("vaccine.utils.get_today")
async def test_menu_with_id_number_ambigious_age_older(get_today):
    get_today.return_value = date(2021, 1, 1)

    # English language choice
    u = User(addr="27820001001")
    app = Application(u)
    msg = Message(
        to_addr="*123*456*0001010001087#",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
        session_event=Message.SESSION_EVENT.NEW,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160

    app = Application(u)
    msg = Message(
        content="1",
        to_addr="*123*456*0001010001087#",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert u.state.name == "state_terms_and_conditions"
    assert u.answers["state_identification_type"] == "rsa_id"
    assert u.answers["state_identification_number"] == "0001010001087"
    assert "state_dob_year" not in u.answers
    assert u.answers["state_dob_month"] == "1"
    assert u.answers["state_dob_day"] == "1"
    assert u.answers["state_gender"] == "Female"

    # Accept All Terms Screens
    app = Application(u)
    msg = Message(
        content="1",
        to_addr="*123*456*0001010001087#",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert u.state.name == "state_terms_and_conditions_2"

    app = Application(u)
    msg = Message(
        content="1",
        to_addr="*123*456*0001010001087#",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert u.state.name == "state_terms_and_conditions_3"

    app = Application(u)
    msg = Message(
        content="1",
        to_addr="*123*456*0001010001087#",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert u.state.name == "state_dob_year"

    app = Application(u)
    msg = Message(
        content="1900",
        to_addr="*123*456*0001010001087#",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert u.state.name == "state_first_name"


@pytest.mark.asyncio
@mock.patch("vaccine.utils.get_today")
async def test_menu_with_id_number_ambigious_age_younger(get_today):
    get_today.return_value = date(2021, 1, 1)

    # English language choice
    u = User(addr="27820001001")
    app = Application(u)
    msg = Message(
        to_addr="*123*456*0001010001087#",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
        session_event=Message.SESSION_EVENT.NEW,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160

    app = Application(u)
    msg = Message(
        content="1",
        to_addr="*123*456*0001010001087#",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert u.state.name == "state_terms_and_conditions"
    assert u.answers["state_identification_type"] == "rsa_id"
    assert u.answers["state_identification_number"] == "0001010001087"
    assert "state_dob_year" not in u.answers
    assert u.answers["state_dob_month"] == "1"
    assert u.answers["state_dob_day"] == "1"
    assert u.answers["state_gender"] == "Female"

    # Accept All Terms Screens
    app = Application(u)
    msg = Message(
        content="1",
        to_addr="*123*456*0001010001087#",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert u.state.name == "state_terms_and_conditions_2"

    app = Application(u)
    msg = Message(
        content="1",
        to_addr="*123*456*0001010001087#",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert u.state.name == "state_terms_and_conditions_3"

    app = Application(u)
    msg = Message(
        content="1",
        to_addr="*123*456*0001010001087#",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert u.state.name == "state_dob_year"

    app = Application(u)
    msg = Message(
        content="2000",
        to_addr="*123*456*0001010001087#",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert u.state.name == "state_under_age_notification"


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


async def test_state_timed_out_timed_out():
    tester = AppTester(Application)
    tester.setup_state("state_timed_out_vacreg")
    tester.setup_answer("resume_state", "state_vaccination_time")
    await tester.user_input(session=Message.SESSION_EVENT.NEW)
    tester.assert_state("state_timed_out_vacreg")
    tester.assert_answer("resume_state", "state_vaccination_time")


async def test_state_language():
    tester = AppTester(Application)
    tester.setup_state("state_menu")
    await tester.user_input("3")
    tester.assert_state("state_language")

    await tester.user_input("2")
    tester.assert_state("state_menu")
    assert tester.user.lang == "zul"
