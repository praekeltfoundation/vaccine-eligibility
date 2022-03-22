import pytest

from mqr.baseline_survey_wa import Application
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

    assert (
        reply.content == "1/13 \n"
        "\n"
        "Do you plan to breastfeed your baby after birth?\n"
        "1. Yes\n"
        "2. No\n"
        "3. Skip this question"
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

    assert user.state.name == "breast_feeding_term"
    assert reply.content == "\n".join(
        [
            "Please use numbers from list.\n"
            "\n"
            "*How long do you plan to give your baby only"
            " breastmilk before giving other foods and water?*"
            "\n"
            "1. Between 0 and 3 months\n"
            "2. Between 4 and 5 months\n"
            "3. For 6 months\n"
            "4. Longer than 6 months\n"
            "5. I don't want to only breastfeed\n"
            "6. I don't know\n"
            "7. Skip this question"
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

    assert user.state.name == "breast_feeding_term"
    assert reply.content == "\n".join(
        [
            "2/13 \n"
            "\n"
            "*How long do you plan to give your baby only"
            " breastmilk before giving other foods and water?*"
            "\n"
            "1. Between 0 and 3 months\n"
            "2. Between 4 and 5 months\n"
            "3. For 6 months\n"
            "4. Longer than 6 months\n"
            "5. I don't want to only breastfeed\n"
            "6. I don't know\n"
            "7. Skip this question"
        ]
    )


@pytest.mark.asyncio
async def test_eating_vegetables():
    user = User(addr="27820001003", state=StateData("eating_vegetables"))
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

    assert (
        reply.content == "6/13 \n"
        "\n"
        "Since becoming pregnant, do you eat vegetables at least once a week?\n"
        "1. Yes\n"
        "2. No\n"
        "3. Skip this question"
    )


@pytest.mark.asyncio
async def test_eating_fruits():
    user = User(addr="27820001003", state=StateData("eating_fruits"))
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

    assert (
        reply.content == "7/13 \n"
        "\n"
        "Since becoming pregnant, do you eat fruit at least once a week?\n"
        "1. Yes\n"
        "2. No\n"
        "3. Skip this question"
    )


@pytest.mark.asyncio
async def test_eating_dairy_products():
    user = User(addr="27820001003", state=StateData("eating_dairy_products"))
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

    assert (
        reply.content == "8/13 \n"
        "\n"
        "Since becoming pregnant, do you have milk, maas, hard cheese or yoghurt at "
        "least once a week?\n"
        "1. Yes\n"
        "2. No\n"
        "3. Skip this question"
    )


@pytest.mark.asyncio
async def test_eating_liver_frequency():
    user = User(addr="27820001003", state=StateData("eating_liver_frequency"))
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

    assert (
        reply.content == "9/13 \n"
        "\n"
        "How often do you eat liver?\n"
        "1. 2-3 times a week\n"
        "2. Once a week\n"
        "3. Once a month\n"
        "4. Less than once a month\n"
        "5. Never\n"
        "6. Skip this question"
    )


@pytest.mark.asyncio
async def test_pregnancy_danger_signs():
    user = User(addr="27820001003", state=StateData("pregnancy_danger_signs"))
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

    assert (
        reply.content == "10/13 \n"
        "\n"
        "In your opinion, what is the biggest danger sign in pregnancy "
        "from this list?\n"
        "1. Weight gain of 4-5 kilograms\n"
        "2. Vaginal bleeding\n"
        "3. Nose bleeds\n"
        "4. Skip this question"
    )


@pytest.mark.asyncio
async def test_second_pregnancy_danger_signs():
    user = User(addr="27820001003", state=StateData("second_pregnancy_danger_signs"))
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

    assert (
        reply.content == "11/13 \n"
        "\n"
        "In your view, what is the biggest pregnancy danger sign on this list?\n"
        "1. Swollen feet and legs even after sleep\n"
        "2. Bloating\n"
        "3. Gas\n"
        "4. Skip this question"
    )


@pytest.mark.asyncio
async def test_marital_status():
    user = User(addr="27820001003", state=StateData("marital_status"))
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

    assert (
        reply.content == "12/13 \n"
        "\n"
        "What is your marital status?\n"
        "1. Never married\n"
        "2. Married\n"
        "3. Separated or divorced\n"
        "4. Widowed\n"
        "5. Have a partner or boyfriend\n"
        "6. Skip this question"
    )


@pytest.mark.asyncio
async def test_vaccination_diseases_statement():
    user = User(
        addr="278201234567",
        state=StateData(name="vaccination_diseases_statement"),
        session_id=1,
        answers={},
    )
    app = Application(user)
    msg = Message(
        content="valid",
        to_addr="278201234567",
        from_addr="27820001003",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.USSD,
        session_event=Message.SESSION_EVENT.NEW,
    )
    [reply] = await app.process_message(msg)

    assert user.state.name == "vaccination_diseases_statement"
    assert reply.content == "\n".join(
        [
            "3/13 \n"
            "\n"
            "What do you think about this statement\n"
            "I think it is important to vaccinate my baby against severe diseases like "
            "measles, polio and tetanus\n"
            "1. I strongly agree\n"
            "2. I agree\n"
            "3. I don't agree or disagree\n"
            "4. I disagree\n"
            "5. I strongly disagree\n"
            "6. Skip this question"
        ]
    )


@pytest.mark.asyncio
async def test_vaccination_risks_statement():
    user = User(
        addr="278201234567",
        state=StateData(name="vaccination_risks_statement"),
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

    assert user.state.name == "vaccination_risks_statement"
    assert reply.content == "\n".join(
        [
            "4/13 \n"
            "\n"
            "What do you think about this statement\n"
            "The benefits of vaccines protecting my child against diseases like "
            "measles, tetanus, and polio outweigh the risks of my child developing "
            "a serious side effect from the vaccine.\n"
            "1. I strongly agree\n"
            "2. I agree\n"
            "3. I don't agree or disagree\n"
            "4. I disagree\n"
            "5. I strongly disagree\n"
            "6. Skip this question"
        ]
    )


@pytest.mark.asyncio
async def test_pregnancy_checkup():
    user = User(
        addr="278201234567",
        state=StateData(name="pregnancy_checkup"),
        session_id=1,
        answers={},
    )
    app = Application(user)
    msg = Message(
        content="valid",
        to_addr="278201234567",
        from_addr="27820001003",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.USSD,
        session_event=Message.SESSION_EVENT.NEW,
    )
    [reply] = await app.process_message(msg)

    assert user.state.name == "pregnancy_checkup"
    assert reply.content == "\n".join(
        [
            "5/13 \n"
            "\n"
            "How often do you plan to go to the clinic for a a check-up "
            "during this pregnancy?\n"
            "1. More than once a month\n"
            "2. Once a month\n"
            "3. Once every  2 to 3 months\n"
            "4. Once every  4 to 5 months\n"
            "5. Once every 6 to 9 months\n"
            "6. Never\n"
            "7. Skip this question"
        ]
    )


@pytest.mark.asyncio
async def test_education_highest_level():
    user = User(
        addr="278201234567",
        state=StateData(name="education_highest_level"),
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

    assert user.state.name == "education_highest_level"
    assert reply.content == "\n".join(
        [
            "13/13 \n"
            "\n"
            "Which answer best describes your highest level of education?\n"
            "1. Less than Grade 7\n"
            "2. Between Grades 7-12\n"
            "3. Matric\n"
            "4. Diploma\n"
            "5. University degree or higher\n"
            "6. Skip this question"
        ]
    )
