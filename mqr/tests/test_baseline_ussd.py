import pytest
from sanic import Sanic, response

from mqr.baseline_ussd import Application
from vaccine.models import Message, StateData, User
import vaccine.healthcheck_config as config


def get_rapidpro_contact(urn, mqr_consent="Accepted", mqr_arm="RCM_SMS"):
    return {
        "uuid": "b733e997-b0b4-4d4d-a3ad-0546e1644aa9",
        "name": "",
        "language": "zul",
        "groups": [],
        "fields": {"mqr_consent": mqr_consent, "mqr_arm": mqr_arm},
        "blocked": False,
        "stopped": False,
        "created_on": "2015-11-11T08:30:24.922024+00:00",
        "modified_on": "2015-11-11T08:30:25.525936+00:00",
        "urns": [urn],
    }


@pytest.fixture
async def rapidpro_mock(sanic_client):
    Sanic.test_mode = True
    app = Sanic("mock_rapidpro")
    app.requests = []
    app.errors = 0
    app.errormax = 0

    @app.route("/api/v2/contacts.json", methods=["GET"])
    def get_contact(request):
        app.requests.append(request)
        if app.errormax:
            if app.errors < app.errormax:
                app.errors += 1
                return response.json({}, status=500)

        contacts = []
        urn = request.args.get("urn")
        if urn == "whatsapp:27820001003":
            contacts = [get_rapidpro_contact(urn)]

        if urn == "whatsapp:27820001004":
            contacts = [get_rapidpro_contact(urn, "Declined", "BCM")]

        return response.json(
            {
                "results": contacts,
                "next": None,
            },
            status=200,
        )

    client = await sanic_client(app)
    url = config.RAPIDPRO_URL
    config.RAPIDPRO_URL = f"http://{client.host}:{client.port}"
    config.RAPIDPRO_TOKEN = "testtoken"
    yield client
    config.RAPIDPRO_URL = url


@pytest.mark.asyncio
async def test_state_survey_start(rapidpro_mock):
    u = User(addr="27820001003", state=StateData())
    app = Application(u)
    msg = Message(
        content=None,
        to_addr="27820001002",
        from_addr="27820001003",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
        session_event=Message.SESSION_EVENT.NEW,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 140
    assert reply.content == "\n".join(
        [
            "1/13",
            "",
            "Do you plan to breastfeed your baby after birth?",
            "1. Yes",
            "2. No",
            "3. Skip",
        ]
    )

    assert [r.path for r in rapidpro_mock.app.requests] == ["/api/v2/contacts.json"]


@pytest.mark.asyncio
async def test_state_survey_start_not_mqr_contact(rapidpro_mock):
    u = User(addr="27820001004", state=StateData())
    app = Application(u)
    msg = Message(
        content=None,
        to_addr="27820001002",
        from_addr="27820001004",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
        session_event=Message.SESSION_EVENT.NEW,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 140
    assert reply.content == "TODO COPY"

    assert [r.path for r in rapidpro_mock.app.requests] == ["/api/v2/contacts.json"]


@pytest.mark.asyncio
async def test_state_survey_start_not_found(rapidpro_mock):
    u = User(addr="27820001005", state=StateData())
    app = Application(u)
    msg = Message(
        content=None,
        to_addr="27820001002",
        from_addr="27820001005",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
        session_event=Message.SESSION_EVENT.NEW,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 140
    assert reply.content == "TODO COPY"

    assert [r.path for r in rapidpro_mock.app.requests] == ["/api/v2/contacts.json"]


@pytest.mark.asyncio
async def test_state_start_temporary_errors(rapidpro_mock):
    rapidpro_mock.app.errormax = 3
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

    assert len(rapidpro_mock.app.requests) == 3


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
        reply.content == "1/13\n"
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

    assert len(reply.content) < 160
    assert (
        reply.content == "6/13 \n"
        "\n"
        "Since becoming pregnant, do you eat vegetables at least once a week?\n"
        "1. Yes\n"
        "2. No\n"
        "3. Skip"
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

    assert len(reply.content) < 160
    assert (
        reply.content == "7/13 \n"
        "\n"
        "Since becoming pregnant, do you eat fruit at least once a week?\n"
        "1. Yes\n"
        "2. No\n"
        "3. Skip"
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

    assert len(reply.content) < 160
    assert (
        reply.content == "8/13 \n"
        "\n"
        "Since becoming pregnant, do you have milk, maas, hard cheese or yoghurt at "
        "least once a week?\n"
        "1. Yes\n"
        "2. No\n"
        "3. Skip"
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

    assert len(reply.content) < 160
    assert (
        reply.content == "9/13 \n"
        "\n"
        "How often do you eat liver?\n"
        "1. 2-3 times a week\n"
        "2. Once a week\n"
        "3. Once a month\n"
        "4. Less than once a month\n"
        "5. Never\n"
        "6. Skip"
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

    assert len(reply.content) < 160
    assert (
        reply.content == "10/13 \n"
        "\n"
        "In your view, what is the biggest pregnancy danger sign on this list?\n"
        "1. Yes\n"
        "2. Weight gain of 4-5 kilograms\n"
        "3. Nose bleeds\n"
        "4. Skip"
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

    assert len(reply.content) < 160
    assert (
        reply.content == "11/13 \n"
        "\n"
        "In your view, what is the biggest pregnancy danger sign on this list?\n"
        "1. Swollen feet and legs even after sleep\n"
        "2. Bloating\n"
        "3. Gas\n"
        "4. Skip"
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

    assert len(reply.content) < 160
    assert (
        reply.content == "12/13 \n"
        "\n"
        "What is your marital status?\n"
        "1. Never married\n"
        "2. Married\n"
        "3. Separated or divorced\n"
        "4. Widowed\n"
        "5. Have a partner or boyfriend\n"
        "6. Skip"
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

    assert len(reply.content) < 160
    assert user.state.name == "vaccination_diseases_statement"
    assert reply.content == "\n".join(
        [
            "3/13 \n"
            "\n"
            "What do you think about this statement\n"
            "I think it is important to vaccinate my baby against severe diseases like "
            "measles, polio and tetanus\n"
            "1. Next"
        ]
    )


@pytest.mark.asyncio
async def test_vaccination_diseases_statement_answer():
    user = User(
        addr="278201234567",
        state=StateData(name="vaccination_diseases_statement_answers"),
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

    assert len(reply.content) < 160
    assert user.state.name == "vaccination_diseases_statement_answers"
    assert reply.content == "\n".join(
        [
            "\n"
            "1. I strongly agree\n"
            "2. I agree\n"
            "3. I don't agree or disagree\n"
            "4. I disagree\n"
            "5. I strongly disagree\n"
            "6. Skip"
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

    assert len(reply.content) < 160
    assert user.state.name == "vaccination_risks_statement"
    assert reply.content == "\n".join(
        [
            "4/13 \n"
            "\n"
            "What do you think about this statement\n"
            "The benefits of vaccinating my child outweighs the risks my child will "
            "develop side effects from them\n"
            "1. Next"
        ]
    )


@pytest.mark.asyncio
async def test_vaccination_risks_statement_answers():
    user = User(
        addr="278201234567",
        state=StateData(name="vaccination_risks_statement_answers"),
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
    assert user.state.name == "vaccination_risks_statement_answers"
    assert reply.content == "\n".join(
        [
            "\n"
            "1. I strongly agree\n"
            "2. I agree\n"
            "3. I don't agree or disagree\n"
            "4. I disagree\n"
            "5. I strongly disagree\n"
            "6. Skip"
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

    assert len(reply.content) < 160
    assert user.state.name == "pregnancy_checkup"
    assert reply.content == "\n".join(
        [
            "5/13 \n"
            "\n"
            "How often do you plan to go to the clinic for a a check-up "
            "during this pregnancy?\n"
            "1. Next"
        ]
    )


@pytest.mark.asyncio
async def test_pregnancy_checkup_answers():
    user = User(
        addr="278201234567",
        state=StateData(name="pregnancy_checkup_answers"),
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

    assert len(reply.content) < 160
    assert user.state.name == "pregnancy_checkup_answers"
    assert reply.content == "\n".join(
        [
            "\n"
            "1. More than once a month\n"
            "2. Once a month\n"
            "3. Once every  2 to 3 months\n"
            "4. Once every  4 to 5 months\n"
            "5. Once every 6 to 9 months\n"
            "6. Never\n"
            "7. Skip"
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

    assert len(reply.content) < 160
    assert user.state.name == "education_highest_level"
    assert reply.content == "\n".join(
        [
            "13/13 \n"
            "\n"
            "Which answer best describes your highest level of education?\n"
            "1. Next"
        ]
    )


@pytest.mark.asyncio
async def test_education_highest_level_answers():
    user = User(
        addr="278201234567",
        state=StateData(name="education_highest_level_answers"),
        session_id=1,
        answers={},
    )
    app = Application(user)
    msg = Message(
        content="",
        to_addr="278201234567",
        from_addr="27820001003",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.USSD,
        session_event=Message.SESSION_EVENT.NEW,
    )
    [reply] = await app.process_message(msg)

    assert len(reply.content) < 160
    assert user.state.name == "education_highest_level_answers"
    assert reply.content == "\n".join(
        [
            "\n"
            "1. Less than Grade 7\n"
            "2. Between Grades 7-12\n"
            "3. Matric\n"
            "4. Diploma\n"
            "5. University degree or higher\n"
            "6. Skip"
        ]
    )
