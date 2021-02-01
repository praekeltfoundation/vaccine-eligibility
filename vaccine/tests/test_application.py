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
    assert reply.content == "\n".join(
        [
            "Welcome to the vaccine eligibility service.",
            "Please answer a few questions so that we can determine your eligibility.",
            "",
            "What is your current occupation?",
            "1. Unemployed",
            "2. Retired",
            "3. Healthcare",
            "4. Essential",
            "5. Software Engineer",
            "6. Other",
        ]
    )
    assert u.state.name == "state_occupation"
    assert u.in_session is True


@pytest.mark.asyncio
async def test_returning_user():
    """
    Returning user messages should be treated as responses to their current state
    """
    u = User(
        addr="27820001001", state=StateData(name="state_occupation"), in_session=True
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
    assert reply.content == "\n".join(
        [
            "Sorry we don't understand your response, please try again.",
            "",
            "What is your current occupation?",
            "1. Unemployed",
            "2. Retired",
            "3. Healthcare",
            "4. Essential",
            "5. Software Engineer",
            "6. Other",
        ]
    )
    assert u.state.name == "state_occupation"
    assert u.in_session is True


@pytest.mark.asyncio
async def test_occupation_number():
    """
    Replying with a number should select your occupation
    """
    u = User(
        addr="27820001001", state=StateData(name="state_occupation"), in_session=True
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
    assert u.answers["state_occupation"] == "retired"


@pytest.mark.asyncio
async def test_occupation_label():
    """
    Replying with a label should select your occupation
    """
    u = User(
        addr="27820001001", state=StateData(name="state_occupation"), in_session=True
    )
    app = Application(u)
    msg = Message(
        content="essential",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert reply.content == "What is your current age, in years?"
    assert u.answers["state_occupation"] == "essential"


@pytest.mark.asyncio
async def test_age_valid():
    """
    If the age is valid, should save the value for age
    """
    u = User(addr="27820001001", state=StateData(name="state_age"), in_session=True)
    app = Application(u)
    msg = Message(
        content="12",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert reply.content == "\n".join(
        [
            "Thank you for answering those questions.",
            "You are not currently eligible for a vaccine, but we will send you a "
            "message notifying you when you are eligible.",
            "",
            "Type *MENU* to go back to the main menu, or *VACCINE* for more "
            "information around vaccines",
        ]
    )
    assert u.answers["state_age"] == "12"


@pytest.mark.asyncio
async def test_age_invalid():
    """
    If the age is invalid, should display an error message
    """
    u = User(addr="27820001001", state=StateData(name="state_age"), in_session=True)
    app = Application(u)
    msg = Message(
        content="abc123",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert u.state.name == "state_age"
    assert (
        reply.content
        == "Sorry, we don't understand your response. Please type the number that "
        "represents your age in years"
    )
    assert "state_age" not in u.answers
