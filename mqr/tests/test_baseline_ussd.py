import pytest

from mqr.baseline_ussd import Application
from vaccine.models import Message, StateData, User


@pytest.mark.asyncio
async def test_breast_feeding():
    user = User(
        addr="278201234567",
        state=StateData(name="breast_feeding"),
        session_id=1,
        answers={"returning_user": "yes"},
    )
    app = Application(user)
    msg = Message(
        content="start",
        to_addr="27820001002",
        from_addr="27820001003",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)

    assert len(reply.content) < 160
    assert user.state.name == "breast_feeding"


@pytest.mark.asyncio
async def test_breast_feeding_valid():
    user = User(addr="27820001003", state=StateData("breast_feeding"))
    app = Application(user)
    msg = Message(
        content=None,
        to_addr="27820001002",
        from_addr="27820001003",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
        session_event=Message.SESSION_EVENT.NEW,
    )
    [reply] = await app.process_message(msg)

    assert len(reply.content) < 160
    assert (
        reply.content == "1/13 \n"
        "\n"
        "Do you plan to breastfeed your baby after birth?\n"
        "1. Yes\n"
        "2. No\n"
        "3. Skip"
    )


@pytest.mark.asyncio
async def test_breast_feeding_term_invalid():
    user = User(
        addr="278201234567",
        state=StateData(name="breast_feeding_term"),
        session_id=1,
        answers={},
    )
    app = Application(user)
    msg = Message(
        content="invalid",
        to_addr="278201234567",
        from_addr="27820001003",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.USSD,
    )
    [reply] = await app.process_message(msg)

    assert len(reply.content) < 160
    assert user.state.name == "breast_feeding_term"
    assert reply.content == "\n".join(
        [
            "Please use numbers from list.\n"
            "\n"
            "*How long do you plan to give your baby only"
            " breastmilk before giving other foods and water?*"
            "\n"
            "1. Next"
        ]
    )


@pytest.mark.asyncio
async def test_breast_feeding_term_valid():
    user = User(
        addr="278201234567",
        state=StateData(name="breast_feeding_term"),
        session_id=1,
        answers={},
    )
    app = Application(user)
    msg = Message(
        content="invalid",
        to_addr="278201234567",
        from_addr="27820001003",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.USSD,
        session_event=Message.SESSION_EVENT.NEW,
    )
    [reply] = await app.process_message(msg)

    assert len(reply.content) < 160
    assert user.state.name == "breast_feeding_term"
    assert reply.content == "\n".join(
        [
            "2/13 \n"
            "\n"
            "*How long do you plan to give your baby only"
            " breastmilk before giving other foods and water?*"
            "\n"
            "1. Next"
        ]
    )
