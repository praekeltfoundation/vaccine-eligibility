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
    assert u.session_id is None
    app = Application(u)
    msg = Message(
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [welcome, reply] = await app.process_message(msg)
    assert (
        welcome.content
        == "Thank you for your interest in the getting the COVID-19 vaccine. The South "
        "African national vaccine rollout is being done over 3 phases. Answer these "
        "questions to find out which phase you are in:"
    )
    assert reply.content == "\n".join(
        [
            "◼️◻️◻️◻️◻️",
            "",
            "Which of these positions or job titles describes your current "
            "employment:",
            "",
            "1. Health Care Worker",
            "2. Essential Worker",
            "3. Other",
            "4. Not Sure",
        ]
    )
    assert u.state.name == "state_occupation"
    assert u.session_id is not None


@pytest.mark.asyncio
async def test_returning_user():
    """
    Returning user messages should be treated as responses to their current state
    """
    u = User(
        addr="27820001001", state=StateData(name="state_occupation"), session_id="1"
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
            "⚠️ This service works best when you use the numbered options available",
            "",
            "1. Health Care Worker",
            "2. Essential Worker",
            "3. Other",
            "4. Not Sure",
        ]
    )
    assert u.state.name == "state_occupation"
    assert u.session_id == "1"


@pytest.mark.asyncio
async def test_occupation_number():
    """
    Replying with a number should select your occupation, and save the result
    """
    u = User(
        addr="27820001001", state=StateData(name="state_occupation"), session_id="1"
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
    assert u.answers["state_occupation"] == "essential"
    [answer] = app.answer_events
    assert answer.question == "state_occupation"
    assert answer.response == "essential"
    assert answer.address == "27820001001"
    assert answer.session_id == "1"


@pytest.mark.asyncio
async def test_occupation_label():
    """
    Replying with a label should select your occupation
    """
    u = User(
        addr="27820001001", state=StateData(name="state_occupation"), session_id="1"
    )
    app = Application(u)
    msg = Message(
        content="essential worker",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert reply.content == "What is your current age, in years?"
    assert u.answers["state_occupation"] == "essential"


@pytest.mark.asyncio
async def test_occupation_not_sure():
    """
    Selecting not sure should give a description, then ask the question again
    """
    u = User(
        addr="27820001001", state=StateData(name="state_occupation"), session_id="1"
    )
    app = Application(u)
    msg = Message(
        content="not sure",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [info, reply] = await app.process_message(msg)
    assert info.content == "\n".join(
        [
            "*Health Care Workers* include doctors, nurses, dentists, pharmacists, "
            "medical specialists and all people involved in providing health "
            "services such as cleaning, security, medical waste disposal and "
            "administrative work.",
            "",
            "*Essential Workers* include police officers, miners, teachers, people "
            "working in security, retail, food, funeral, banking and essential "
            "muncipal and home affairs, border control and port health services.",
        ]
    )
    assert reply.content == "\n".join(
        [
            "◼️◻️◻️◻️◻️",
            "",
            "Which of these positions or job titles describes your current "
            "employment:",
            "",
            "1. Health Care Worker",
            "2. Essential Worker",
            "3. Other",
            "4. Not Sure",
        ]
    )
    assert u.state.name == "state_occupation"
    assert u.session_id == "1"


@pytest.mark.asyncio
async def test_age_valid():
    """
    If the age is valid, should save the value for age
    """
    u = User(addr="27820001001", state=StateData(name="state_age"), session_id="1")
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
    [answer] = app.answer_events
    assert answer.question == "state_age"
    assert answer.response == "12"
    assert answer.address == "27820001001"
    assert answer.session_id == "1"


@pytest.mark.asyncio
async def test_age_invalid():
    """
    If the age is invalid, should display an error message
    """
    u = User(addr="27820001001", state=StateData(name="state_age"), session_id="1")
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


@pytest.mark.asyncio
async def test_user_end_sesssion():
    """
    If the user has ended the session, then we should send them the session end message
    """
    u = User(
        addr="27820001001", state=StateData(name="state_occupation"), session_id="1"
    )
    app = Application(u)
    msg = Message(
        to_addr="27820001002",
        from_addr="27820001002",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
        session_event=Message.SESSION_EVENT.CLOSE,
    )
    [reply] = await app.process_message(msg)
    assert u.session_id is None
    assert reply.content == "\n".join(
        [
            "We're sorry, but you've taken too long to reply and your session has "
            "expired.",
            "If you would like to continue, you can at anytime by typing the word "
            "*VACCINE*.",
            "",
            "Reply *MENU* to return to the main menu",
        ]
    )
