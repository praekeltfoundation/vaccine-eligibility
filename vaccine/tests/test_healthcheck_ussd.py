import pytest
from sanic import Sanic, response

from vaccine.healthcheck_ussd import Application, config
from vaccine.models import Message, StateData, User


@pytest.fixture
async def eventstore_mock(sanic_client):
    Sanic.test_mode = True
    app = Sanic("mock_eventstore")
    app.requests = []
    app.userprofile_errormax = 0
    app.userprofile_errors = 0
    app.start_errormax = 0
    app.start_errors = 0

    @app.route("/api/v2/healthcheckuserprofile/27820001001/", methods=["GET"])
    @app.route("/api/v2/healthcheckuserprofile/27820001004/", methods=["GET"])
    def valid_userprofile(request):
        app.requests.append(request)
        if app.userprofile_errormax:
            if app.userprofile_errors < app.userprofile_errormax:
                app.userprofile_errors += 1
                return response.json({}, status=500)
        return response.json(
            {
                "province": "ZA-WC",
                "city": "Cape Town",
                "city_location": "+12.34-56.78/",
                "age": "18-40",
                "data": {"age_years": "35", "preexisting_condition": "no"},
            },
            status=200,
        )

    @app.route("/api/v2/healthcheckuserprofile/27820001003/", methods=["GET"])
    def userprofile_doesnotexist(request):
        app.requests.append(request)
        if app.userprofile_errormax:
            if app.userprofile_errors < app.userprofile_errormax:
                app.userprofile_errors += 1
                return response.json({}, status=500)
        return response.json({}, status=404)

    @app.route("/api/v2/covid19triagestart/", methods=["POST"])
    def valid_triagestart(request):
        app.requests.append(request)
        if app.start_errormax:
            if app.start_errors < app.start_errormax:
                app.start_errors += 1
                return response.json({}, status=500)
        return response.json({})

    client = await sanic_client(app)
    url = config.EVENTSTORE_API_URL
    config.EVENTSTORE_API_URL = f"http://{client.host}:{client.port}"
    yield client
    config.EVENTSTORE_API_URL = url


@pytest.fixture
async def turn_mock(sanic_client):
    Sanic.test_mode = True
    app = Sanic("mock_turn")
    app.requests = []
    app.errors = 0
    app.errormax = 0

    @app.route("/v1/contacts/27820001001/profile", methods=["GET"])
    def valid_userprofile(request):
        app.requests.append(request)
        if app.errormax:
            if app.errors < app.errormax:
                app.errors += 1
                return response.json({}, status=500)
        return response.json({"fields": {"confirmed_contact": True}}, status=200)

    @app.route("/v1/contacts/27820001003/profile", methods=["GET"])
    @app.route("/v1/contacts/27820001004/profile", methods=["GET"])
    def not_confirmed_contact(request):
        app.requests.append(request)
        if app.errormax:
            if app.errors < app.errormax:
                app.errors += 1
                return response.json({}, status=500)
        return response.json({"fields": {"confirmed_contact": False}}, status=200)

    client = await sanic_client(app)
    url = config.TURN_API_URL
    config.TURN_API_URL = f"http://{client.host}:{client.port}"
    yield client
    config.TURN_API_URL = url


@pytest.mark.asyncio
async def test_state_welcome_confirmed_contact(eventstore_mock, turn_mock):
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
    assert reply.content == "\n".join(
        [
            "The National Department of Health thanks you for contributing to the "
            "health of all citizens. Stop the spread of COVID-19",
            "",
            "Reply",
            "1. START",
        ]
    )
    assert u.state.name == "state_welcome"

    assert [r.path for r in eventstore_mock.app.requests] == [
        "/api/v2/healthcheckuserprofile/27820001001/",
        "/api/v2/covid19triagestart/",
    ]
    assert [r.path for r in turn_mock.app.requests] == [
        "/v1/contacts/27820001001/profile"
    ]
    assert u.answers["confirmed_contact"] == "yes"

    app.messages = []
    msg = Message(
        content="invalid",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert reply.content == "\n".join(
        [
            "The National Department of Health thanks you for contributing to the "
            "health of all citizens. Stop the spread of COVID-19",
            "",
            "Reply",
            "1. START",
        ]
    )


@pytest.mark.asyncio
async def test_state_welcome_new_contact(eventstore_mock, turn_mock):
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
            "The National Department of Health thanks you for contributing to the "
            "health of all citizens. Stop the spread of COVID-19",
            "",
            "Reply",
            "1. START",
        ]
    )
    assert u.state.name == "state_welcome"

    assert [r.path for r in eventstore_mock.app.requests] == [
        "/api/v2/healthcheckuserprofile/27820001003/",
        "/api/v2/covid19triagestart/",
    ]
    assert [r.path for r in turn_mock.app.requests] == [
        "/v1/contacts/27820001003/profile"
    ]
    assert u.answers["confirmed_contact"] == "no"
    assert u.answers["returning_user"] == "no"

    app.messages = []
    msg = Message(
        content="invalid",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert reply.content == "\n".join(
        ["This service works best when you select numbers from the list", "1. START"]
    )


@pytest.mark.asyncio
async def test_state_welcome_returning_contact(eventstore_mock, turn_mock):
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
    assert reply.content == "\n".join(
        [
            "Welcome back to HealthCheck, your weekly COVID-19 Risk Assesment tool. "
            "Let's see how you are feeling today.",
            "",
            "Reply",
            "1. START",
        ]
    )
    assert u.state.name == "state_welcome"

    assert [r.path for r in eventstore_mock.app.requests] == [
        "/api/v2/healthcheckuserprofile/27820001004/",
        "/api/v2/covid19triagestart/",
    ]
    assert [r.path for r in turn_mock.app.requests] == [
        "/v1/contacts/27820001004/profile"
    ]

    assert u.answers["confirmed_contact"] == "no"
    assert u.answers["returning_user"] == "yes"

    app.messages = []
    msg = Message(
        content="invalid",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert reply.content == "\n".join(
        ["This service works best when you select numbers from the list", "1. START"]
    )


@pytest.mark.asyncio
async def test_state_welcome_temporary_errors(eventstore_mock, turn_mock):
    eventstore_mock.app.userprofile_errormax = 1
    eventstore_mock.app.start_errormax = 1
    turn_mock.app.errormax = 1
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

    assert len(eventstore_mock.app.requests) == 4
    assert len(turn_mock.app.requests) == 2


@pytest.mark.asyncio
async def test_state_welcome_userprofile_error(eventstore_mock):
    eventstore_mock.app.userprofile_errormax = 3
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

    assert len(eventstore_mock.app.requests) == 3
    assert u.state.name == "state_start"
    assert (
        reply.content == "Sorry, something went wrong. We have been notified. Please "
        "try again later"
    )


@pytest.mark.asyncio
async def test_state_welcome_start_error(eventstore_mock):
    eventstore_mock.app.start_errormax = 3
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

    assert len(eventstore_mock.app.requests) == 4
    assert u.state.name == "state_start"
    assert (
        reply.content == "Sorry, something went wrong. We have been notified. Please "
        "try again later"
    )


@pytest.mark.asyncio
async def test_state_welcome_turn_error(eventstore_mock, turn_mock):
    turn_mock.app.errormax = 3
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

    assert len(turn_mock.app.requests) == 3
    assert u.state.name == "state_start"
    assert (
        reply.content == "Sorry, something went wrong. We have been notified. Please "
        "try again later"
    )


@pytest.mark.asyncio
async def test_state_terms_new_contact():
    u = User(addr="27820001003", state=StateData(name="state_welcome"), session_id=1)
    app = Application(u)
    msg = Message(
        content="start",
        to_addr="27820001002",
        from_addr="27820001003",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert u.state.name == "state_terms"

    app.messages = []
    msg = Message(
        content="invalid",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160


@pytest.mark.asyncio
async def test_state_more_info_pg1():
    u = User(addr="27820001003", state=StateData(name="state_terms"), session_id=1)
    app = Application(u)
    msg = Message(
        content="more info",
        to_addr="27820001002",
        from_addr="27820001003",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert u.state.name == "state_more_info_pg1"

    app.messages = []
    msg = Message(
        content="invalid",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160


@pytest.mark.asyncio
async def test_state_more_info_pg2():
    u = User(
        addr="27820001003", state=StateData(name="state_more_info_pg1"), session_id=1
    )
    app = Application(u)
    msg = Message(
        content="next",
        to_addr="27820001002",
        from_addr="27820001003",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert u.state.name == "state_more_info_pg2"

    app.messages = []
    msg = Message(
        content="invalid",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160


@pytest.mark.asyncio
async def test_state_terms_returning_user():
    u = User(
        addr="27820001003",
        state=StateData(name="state_welcome"),
        session_id=1,
        answers={"returning_user": "yes"},
    )
    app = Application(u)
    msg = Message(
        content="start",
        to_addr="27820001002",
        from_addr="27820001003",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert u.state.name == "state_province"


@pytest.mark.asyncio
async def test_state_terms_confirmed_contact():
    u = User(
        addr="27820001003",
        state=StateData(name="state_welcome"),
        session_id=1,
        answers={"returning_user": "yes", "confirmed_contact": "yes"},
    )
    app = Application(u)
    msg = Message(
        content="start",
        to_addr="27820001002",
        from_addr="27820001003",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert u.state.name == "state_fever"


@pytest.mark.asyncio
async def test_state_end():
    u = User(addr="27820001003", state=StateData(name="state_terms"), session_id=1)
    app = Application(u)
    msg = Message(
        content="no",
        to_addr="27820001002",
        from_addr="27820001003",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert (
        reply.content
        == "You can return to this service at any time. Remember, if you think you "
        "have COVID-19 STAY HOME, avoid contact with other people and self-isolate."
    )
    assert u.state.name == "state_start"


@pytest.mark.asyncio
async def test_state_end_confirmed_contact():
    u = User(
        addr="27820001003",
        state=StateData(name="state_terms"),
        session_id=1,
        answers={"confirmed_contact": "yes"},
    )
    app = Application(u)
    msg = Message(
        content="no",
        to_addr="27820001002",
        from_addr="27820001003",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert (
        reply.content
        == "You can return to this service at any time. Remember, if you think you "
        "have COVID-19 STAY HOME, avoid contact with other people and self-quarantine."
    )
    assert u.state.name == "state_start"


@pytest.mark.asyncio
async def test_state_province():
    u = User(addr="27820001003", state=StateData(name="state_terms"), session_id=1)
    app = Application(u)
    msg = Message(
        content="yes",
        to_addr="27820001002",
        from_addr="27820001003",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert u.state.name == "state_province"

    app.messages = []
    msg = Message(
        content="invalid",
        to_addr="27820001002",
        from_addr="27820001003",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert u.state.name == "state_province"


@pytest.mark.asyncio
async def test_state_city():
    u = User(
        addr="27820001003",
        state=StateData(name="state_terms"),
        session_id=1,
        answers={"state_province": "ZA-WC"},
    )
    app = Application(u)
    msg = Message(
        content="yes",
        to_addr="27820001002",
        from_addr="27820001003",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert u.state.name == "state_city"

    app.messages = []
    msg = Message(
        content="    ",
        to_addr="27820001002",
        from_addr="27820001003",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert u.state.name == "state_city"
