import pytest

from vaccine.application import Application
from vaccine.models import Message, StateData, User


@pytest.mark.asyncio
async def test_new_user():
    """
    New users should be put in the start state
    """
    u = User.get_or_create("27820001001", "")
    assert u.state.name is None
    assert u.in_session is False
    app = Application(u)
    msg = Message(
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert reply.content == "Welcome to the vaccine eligibility service."
    assert u.state.name == "state_start"
    assert u.in_session is True


@pytest.mark.asyncio
async def test_returning_user():
    u = User(addr="27820001001", state=StateData(name="state_start"), in_session=True)
    app = Application(u)
    msg = Message(
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert reply.content == "Welcome to the vaccine eligibility service."
    assert u.state.name == "state_start"
    assert u.in_session is False
