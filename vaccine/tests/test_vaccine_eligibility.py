import pytest

from vaccine.models import Message, StateData, User
from vaccine.vaccine_eligibility import Application


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
    await app.process_message(msg)
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
async def test_congregate_valid():
    """
    A valid response should save the answer and go to the next stage
    """
    u = User(
        addr="27820001001", state=StateData(name="state_congregate"), session_id="1"
    )
    app = Application(u)
    msg = Message(
        content="yes",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    await app.process_message(msg)
    assert u.state.name == "state_age"
    assert u.answers["state_congregate"] == "yes"


@pytest.mark.asyncio
async def test_congregate_invalid():
    """
    No answer saved, reply with error text
    """
    u = User(
        addr="27820001001", state=StateData(name="state_congregate"), session_id="1"
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
    assert reply.content == "\n".join(
        [
            "⚠️ This service works best when you use the numbered options available",
            "",
            "1. Yes",
            "2. No",
            "3. Not Sure",
        ]
    )
    assert u.state.name == "state_congregate"
    assert "state_congregate" not in u.answers


@pytest.mark.asyncio
async def test_congregate_not_sure():
    """
    Selecting not sure should give a description, then ask the question again
    """
    u = User(
        addr="27820001001", state=StateData(name="state_congregate"), session_id="1"
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
    assert (
        info.content
        == "Examples of places where you may be exposed to large numbers of people "
        "include care homes, detention centers, shelters, prisons, hospitality "
        "settings, tourism settings and educational institutions"
    )
    assert reply.content == "\n".join(
        [
            "◼️◼️◻️◻️◻️",
            "",
            "Are you often in contact with lots of people or are you often in a closed "
            "space with lots of people?",
            "",
            "1. Yes",
            "2. No",
            "3. Not Sure",
        ]
    )
    assert u.state.name == "state_congregate"


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
    await app.process_message(msg)
    assert u.answers["state_age"] == "12"
    [answer] = app.answer_events
    assert answer.question == "state_age"
    assert answer.response == "12"
    assert answer.address == "27820001001"
    assert answer.session_id == "1"
    assert u.state.name == "state_location"


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
    assert reply.content == "⚠️  Reply using numbers only. Example *27*"
    assert "state_age" not in u.answers


@pytest.mark.asyncio
async def test_location():
    """
    Value in response to location should be saved
    """
    u = User(addr="27820001001", state=StateData(name="state_location"), session_id="1")
    app = Application(u)
    msg = Message(
        content="test location",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    await app.process_message(msg)
    assert u.answers["state_location"] == "test location"
    assert u.state.name == "state_comorbidities"


@pytest.mark.asyncio
async def test_location_pin():
    """
    Location pins should also be accepted, their coordinates should be stored
    Value in response to location should be saved
    """
    u = User(addr="27820001001", state=StateData(name="state_location"), session_id="1")
    app = Application(u)
    msg = Message(
        content="test location",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
        transport_metadata={
            "msg": {"location": {"longitude": 12.34, "latitude": 56.78}}
        },
    )
    await app.process_message(msg)
    assert u.answers["state_location"] == "test location"
    assert u.answers["location_geopoint"] == [56.78, 12.34]
    assert u.state.name == "state_comorbidities"


@pytest.mark.asyncio
async def test_comorbidities_valid():
    """
    A valid response should save the answer and go to the next stage
    """
    u = User(
        addr="27820001001",
        state=StateData(name="state_comorbidities"),
        session_id="1",
        answers={"state_age": "12"},
    )
    app = Application(u)
    msg = Message(
        content="yes",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    await app.process_message(msg)
    assert u.state.name == "state_start"
    assert u.session_id is None
    assert u.answers["state_comorbidities"] == "yes"


@pytest.mark.asyncio
async def test_comorbidities_invalid():
    """
    No answer saved, reply with error text
    """
    u = User(
        addr="27820001001", state=StateData(name="state_comorbidities"), session_id="1"
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
    assert reply.content == "\n".join(
        [
            "⚠️ This service works best when you use the numbered options available",
            "",
            "1. Yes",
            "2. No",
            "3. Not Sure",
        ]
    )
    assert u.state.name == "state_comorbidities"
    assert "state_comorbidities" not in u.answers


@pytest.mark.asyncio
async def test_comorbidities_not_sure():
    """
    Selecting not sure should give a description, then ask the question again
    """
    u = User(
        addr="27820001001", state=StateData(name="state_comorbidities"), session_id="1"
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
            "Having one or more specific chronic conditions could impact which phase "
            "you are in. These conditions include:",
            "Chronic Lung Disease (such as Emphysema or Chronic Bronchitis)",
            "Cardiovascular disease / Heart Disease",
            "Renal Disease / Chronic Kidney Disease",
            "HIV",
            "TB (Turboculosis)",
            "Obesity (diagnosed overweight)",
        ]
    )
    assert reply.content == "\n".join(
        [
            "◼️◼️◼️◼️◼️",
            "",
            "Has a doctor ever diagnosed you with diabetes, chronic lung disease, "
            "cardiovascular(heart) disease, renal disease, HIV, TB, or Obesity?",
            "",
            "1. Yes",
            "2. No",
            "3. Not Sure",
        ]
    )
    assert u.state.name == "state_comorbidities"


@pytest.mark.asyncio
async def test_result_ineligible():
    """
    Under 18 years old should be ineligible
    """
    u = User(
        addr="27820001001",
        state=StateData(name="state_comorbidities"),
        session_id="1",
        answers={"state_age": "16"},
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
            "Based on your age you are currently NOT able to get the vaccine. "
            "This may change when more vaccine trials are completed.",
            "",
            "----",
            "Reply:",
            "💉 *VACCINE* for info and updates",
            "📌 *0* to go to the main *MENU*",
        ]
    )
    assert u.session_id is None
    assert u.state.name == "state_start"


@pytest.mark.asyncio
async def test_result_1():
    """
    Health Care Workers should be in phase 1
    """
    u = User(
        addr="27820001001",
        state=StateData(name="state_comorbidities"),
        session_id="1",
        answers={"state_age": "27", "state_occupation": "hcw"},
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
            "✅ *PHASE 1*",
            "🟥 *PHASE 2*",
            "🟥 *PHASE 3*",
            "",
            "*Congratulations!* Based on your responses you could be in *PHASE 1* and "
            "possibly get vaccinated now.",
            "",
            "*What to do next:*",
            "To confirm this and get an appointment, you need to register online at "
            "https://vaccine.enroll.health.gov.za",
            "",
            "Registration does not guarentee that you will get the vaccine "
            "immediately. It helps us check that you fall into this phase and plan for "
            "your vaccine appointment.",
            "",
            "*To register, you will need:* ",
            "👉🏽 Access to the internet on any device ",
            "👉🏽 Your ID number or Passport (non-RSA)",
            "👉🏽 General contact information (your cellphone number will be used as the "
            "primary mode of communication).",
            "👉🏽 Employment information (who you work for and where)",
            "👉🏽 Where relevant, your professional registration details, and medical "
            "aid are also requested.",
            "",
            "If you have all this information available, the 3-step registration "
            "should take 2-3 minutes.",
            "",
            "----",
            "Reply:",
            "💉 *VACCINE* for info and updates",
            "📌 *0* to go to the main *MENU*",
        ]
    )
    assert u.state.name == "state_start"


@pytest.mark.asyncio
async def test_result_2():
    """
    Essential Workers, congregate, age >= 60, or comorbidities should be in phase 2
    """
    u = User(
        addr="27820001001",
        state=StateData(name="state_comorbidities"),
        session_id="1",
        answers={"state_age": "27", "state_occupation": "essential"},
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
            "🟥 *PHASE 1*",
            "✅ *PHASE 2*",
            "🟥 *PHASE 3*",
            "",
            "Your answers show that you could be part of *PHASE 2*.",
            "",
            "Would you like to be notified when registration for *PHASE 2* is "
            "available?",
            "",
            "1. Yes",
            "2. No",
        ]
    )
    assert u.state.name == "state_result_2"


@pytest.mark.asyncio
async def test_result_3():
    """
    Everyone else should be in phase 3
    """
    u = User(
        addr="27820001001",
        state=StateData(name="state_comorbidities"),
        session_id="1",
        answers={
            "state_age": "27",
            "state_occupation": "other",
            "state_congregate": "no",
            "state_comorbidities": "no",
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
    assert reply.content == "\n".join(
        [
            "🟥 *PHASE 1*",
            "🟥 *PHASE 2*",
            "✅ *PHASE 3*",
            "",
            "Your answers show that you could be part of *PHASE 3*.",
            "",
            "Would you like to be notified when registration for *PHASE 3* is "
            "available?",
            "",
            "1. Yes",
            "2. No",
        ]
    )
    assert u.state.name == "state_result_3"


@pytest.mark.asyncio
async def test_confirm_notification_yes():
    """
    If the user selects to get a notification, should save and display result to user
    """
    u = User(addr="27820001001", state=StateData(name="state_result_2"), session_id="1")
    app = Application(u)
    msg = Message(
        content="yes",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert reply.content == "\n".join(
        [
            "Thank you for confirming. We will contact you.",
            "",
            "----",
            "Reply:",
            "💉 *VACCINE* for info and updates",
            "📌 *0* to go to the main *MENU*",
        ]
    )
    assert u.state.name == "state_start"
    assert u.session_id is None
    assert u.answers["state_result_2"] == "yes"


@pytest.mark.asyncio
async def test_confirm_notification_no():
    """
    If the user selects to not get a notification, should save and display result
    """
    u = User(addr="27820001001", state=StateData(name="state_result_3"), session_id="1")
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
            "Thank you for confirming. We won't contact you.",
            "",
            "----",
            "Reply:",
            "💉 *VACCINE* for info and updates",
            "📌 *0* to go to the main *MENU*",
        ]
    )
    assert u.state.name == "state_start"
    assert u.session_id is None
    assert u.answers["state_result_3"] == "no"


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


@pytest.mark.asyncio
async def test_reset_keyword():
    """
    The reset keyword should reset all state and start the user from the beginning
    """
    u = User(
        addr="27820001001",
        state=StateData(name="state_occupation"),
        session_id="1",
        answers={"test": "answers"},
    )
    app = Application(u)
    msg = Message(
        content="!reset",
        to_addr="27820001002",
        from_addr="27820001002",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    await app.process_message(msg)
    assert u.session_id != "1"
    assert u.answers == {}
    assert u.state.name == "state_occupation"
