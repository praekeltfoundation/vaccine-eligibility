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
    app.triage_errormax = 0
    app.triage_errors = 0

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

    @app.route("/api/v3/covid19triage/", methods=["POST"])
    def valid_triage(request):
        app.requests.append(request)
        if app.triage_errormax:
            if app.triage_errors < app.triage_errormax:
                app.triage_errors += 1
                return response.json({}, status=500)
        return response.json({})

    client = await sanic_client(app)
    url = config.EVENTSTORE_API_URL
    config.EVENTSTORE_API_URL = f"http://{client.host}:{client.port}"
    yield client
    config.EVENTSTORE_API_URL = url


@pytest.fixture
async def google_api_mock(sanic_client):
    Sanic.test_mode = True
    app = Sanic("mock_google_api")
    app.requests = []
    app.api_errormax = 0
    app.api_errors = 0
    app.status = "OK"

    @app.route("/maps/api/place/autocomplete/json", methods=["GET"])
    def valid_city(request):
        app.requests.append(request)
        if app.api_errormax:
            if app.api_errors < app.api_errormax:
                app.api_errors += 1
                return response.json({}, status=500)
        if app.status == "OK":
            data = {
                "status": "OK",
                "predictions": [
                    {
                        "description": "Cape Town, South Africa",
                        "place_id": "ChIJD7fiBh9u5kcRYJSMaMOCCwQ",
                    }
                ],
            }
        else:
            data = {"status": app.status}
        return response.json(data, status=200)

    @app.route("/maps/api/place/details/json", methods=["GET"])
    def details_lookup(request):
        app.requests.append(request)
        if app.api_errormax:
            if app.api_errors < app.api_errormax:
                app.api_errors += 1
                return response.json({}, status=500)
        if app.status == "OK":
            data = {
                "status": "OK",
                "result": {
                    "geometry": {"location": {"lat": -3.866_651, "lng": 51.195_827}}
                },
            }
        else:
            data = {"status": app.status}
        return response.json(data, status=200)

    client = await sanic_client(app)
    config.GOOGLE_PLACES_KEY = "TEST-KEY"
    url = config.GOOGLE_PLACES_URL
    config.GOOGLE_PLACES_URL = f"http://{client.host}:{client.port}"
    yield client
    config.GOOGLE_PLACES_URL = url


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


@pytest.fixture
async def rapidpro_mock(sanic_client):
    Sanic.test_mode = True
    app = Sanic("mock_rapidpro")
    app.requests = []
    app.errors = 0
    app.errormax = 0

    @app.route("/api/v2/flow_starts.json", methods=["POST"])
    def start_flow(request):
        app.requests.append(request)
        if app.errormax:
            if app.errors < app.errormax:
                app.errors += 1
                return response.json({}, status=500)
        return response.json({}, status=200)

    client = await sanic_client(app)
    url = config.RAPIDPRO_URL
    config.RAPIDPRO_URL = f"http://{client.host}:{client.port}"
    config.RAPIDPRO_TOKEN = "testtoken"
    config.RAPIDPRO_PRIVACY_POLICY_SMS_FLOW = "flow-uuid"
    yield client
    config.RAPIDPRO_URL = url


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

    assert reply.content == "\n".join(
        [
            "Confirm that you're responsible for your medical care & "
            "treatment. This service only provides info.",
            "",
            "Reply",
            "1. YES",
            "2. NO",
            "3. MORE INFO",
        ]
    )

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
            "Please use numbers from list. Confirm that u're responsible for "
            "ur medical care & treatment. This service only provides info.",
            "",
            "Reply",
            "1. YES",
            "2. NO",
            "3. MORE INFO",
        ]
    )


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

    assert reply.content == "\n".join(
        [
            "It's not a substitute for professional medical "
            "advice/diagnosis/treatment. Get a qualified health provider's advice "
            "about your medical condition/care.",
            "1. Next",
        ]
    )

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
            "It's not a substitute for professional medical "
            "advice/diagnosis/treatment. Get a qualified health provider's advice "
            "about your medical condition/care.",
            "1. Next",
        ]
    )


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
    assert reply.content == "\n".join(
        [
            "You confirm that you shouldn't disregard/delay seeking medical "
            "advice about treatment/care because of this service. Rely on info at your "
            "own risk.",
            "1. Next",
        ]
    )

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
            "You confirm that you shouldn't disregard/delay seeking medical "
            "advice about treatment/care because of this service. Rely on info at your "
            "own risk.",
            "1. Next",
        ]
    )


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
    assert u.state.name == "state_privacy_policy"


@pytest.mark.asyncio
async def test_state_privacy_policy(rapidpro_mock):
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
    assert u.state.name == "state_privacy_policy"
    assert reply.content == "\n".join(
        [
            "Your personal information is protected under POPIA and in "
            "accordance with the provisions of the HealthCheck Privacy "
            "Notice sent to you by SMS.",
            "1. Accept",
        ]
    )

    assert [r.path for r in rapidpro_mock.app.requests] == ["/api/v2/flow_starts.json"]
    assert [r.json for r in rapidpro_mock.app.requests] == [
        {"flow": "flow-uuid", "urns": ["tel:27820001003"]}
    ]


@pytest.mark.asyncio
async def test_state_privacy_policy_confirmed_contact():
    u = User(
        addr="27820001003",
        state=StateData(name="state_privacy_policy"),
        session_id=1,
        answers={"state_privacy_policy_accepted": True, "confirmed_contact": "yes"},
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
async def test_state_privacy_policy_non_confirmed_contact():
    u = User(
        addr="27820001003",
        state=StateData(name="state_privacy_policy"),
        session_id=1,
        answers={"state_privacy_policy_accepted": True, "confirmed_contact": "no"},
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
    u = User(
        addr="27820001003", state=StateData(name="state_privacy_policy"), session_id=1
    )
    app = Application(u)
    msg = Message(
        content="accept",
        to_addr="27820001002",
        from_addr="27820001003",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert u.state.name == "state_province"
    assert reply.content == "\n".join(
        [
            "Select your province",
            "",
            "Reply:",
            "1. EASTERN CAPE",
            "2. FREE STATE",
            "3. GAUTENG",
            "4. KWAZULU NATAL",
            "5. LIMPOPO",
            "6. MPUMALANGA",
            "7. NORTH WEST",
            "8. NORTHERN CAPE",
            "9. WESTERN CAPE",
        ]
    )

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
    assert reply.content == "\n".join(
        [
            "Select your province",
            "",
            "Reply:",
            "1. EASTERN CAPE",
            "2. FREE STATE",
            "3. GAUTENG",
            "4. KWAZULU NATAL",
            "5. LIMPOPO",
            "6. MPUMALANGA",
            "7. NORTH WEST",
            "8. NORTHERN CAPE",
            "9. WESTERN CAPE",
        ]
    )


@pytest.mark.asyncio
async def test_state_city():
    u = User(
        addr="27820001003",
        state=StateData(name="state_privacy_policy"),
        session_id=1,
        answers={"state_province": "ZA-WC"},
    )
    app = Application(u)
    msg = Message(
        content="accept",
        to_addr="27820001002",
        from_addr="27820001003",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert u.state.name == "state_city"
    assert reply.content == (
        "Please TYPE the name of your Suburb, Township, Town or " "Village (or nearest)"
    )

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
    assert reply.content == (
        "Please TYPE the name of your Suburb, Township, Town or " "Village (or nearest)"
    )


@pytest.mark.asyncio
async def test_state_city_skip():
    u = User(
        addr="27820001003",
        state=StateData(name="state_privacy_policy"),
        session_id=1,
        answers={
            "state_province": "ZA-WC",
            "state_city": "Cape Town",
            "city_location": "+1+1/",
        },
    )
    app = Application(u)
    msg = Message(
        content="accept",
        to_addr="27820001002",
        from_addr="27820001003",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert u.state.name == "state_age"


@pytest.mark.asyncio
async def test_state_city_skip_confirmed_contact():
    u = User(
        addr="27820001003",
        state=StateData(name="state_age_years"),
        session_id=1,
        answers={
            "state_province": "ZA-WC",
            "state_city": "Cape Town",
            "city_location": "+1+1/",
            "confirmed_contact": "yes",
        },
    )
    app = Application(u)
    msg = Message(
        content="19",
        to_addr="27820001002",
        from_addr="27820001003",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert u.state.name == "state_tracing"


@pytest.mark.asyncio
async def test_state_confirm_city(google_api_mock):
    u = User(
        addr="27820001003",
        state=StateData(name="state_city"),
        session_id=1,
        answers={"google_session_token": "123"},
    )
    app = Application(u)

    msg = Message(
        content="cape town",
        to_addr="27820001002",
        from_addr="27820001003",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert u.state.name == "state_confirm_city"
    assert reply.content == "\n".join(
        [
            "Please confirm the address below based on info you shared:",
            "Cape Town, South Africa",
            "",
            "Reply",
            "1. Yes",
            "2. No",
        ]
    )

    assert [r.path for r in google_api_mock.app.requests] == [
        "/maps/api/place/autocomplete/json"
    ]

    assert u.answers["place_id"] == "ChIJD7fiBh9u5kcRYJSMaMOCCwQ"
    assert u.answers["state_city"] == "Cape Town, South Africa"

    app.messages = []
    msg = Message(
        content="no",
        to_addr="27820001002",
        from_addr="27820001003",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert u.state.name == "state_city"


@pytest.mark.asyncio
async def test_state_city_no_results(google_api_mock):
    google_api_mock.app.status = "NO_RESULT"
    u = User(
        addr="27820001003",
        state=StateData(name="state_city"),
        session_id=1,
        answers={"google_session_token": "123"},
    )
    app = Application(u)

    msg = Message(
        content="cape town",
        to_addr="27820001002",
        from_addr="27820001003",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert u.state.name == "state_city"


@pytest.mark.asyncio
async def test_state_city_error(google_api_mock):
    google_api_mock.app.api_errormax = 3
    u = User(
        addr="27820001003",
        state=StateData(name="state_city"),
        session_id=1,
        answers={"google_session_token": "123"},
    )
    app = Application(u)

    msg = Message(
        content="cape town",
        to_addr="27820001002",
        from_addr="27820001003",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert (
        reply.content
        == "Sorry, something went wrong. We have been notified. Please try again later"
    )


@pytest.mark.asyncio
async def test_state_city_temporary_error(google_api_mock):
    google_api_mock.app.api_errormax = 1
    u = User(
        addr="27820001003",
        state=StateData(name="state_city"),
        session_id=1,
        answers={"google_session_token": "123"},
    )
    app = Application(u)

    msg = Message(
        content="cape town",
        to_addr="27820001002",
        from_addr="27820001003",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    await app.process_message(msg)
    assert u.state.name == "state_confirm_city"


@pytest.mark.asyncio
async def test_state_place_details_lookup(google_api_mock):
    u = User(
        addr="27820001003",
        state=StateData(name="state_confirm_city"),
        session_id=1,
        answers={
            "state_city": "Cape Town",
            "google_session_token": "123",
            "place_id": "ChIJD7fiBh9u5kcRYJSMaMOCCwQ",
            "confirmed_contact": "no",
        },
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
    assert u.state.name == "state_age"

    assert [r.path for r in google_api_mock.app.requests] == [
        "/maps/api/place/details/json"
    ]

    assert u.answers["city_location"] == "-03.866651+051.195827/"


@pytest.mark.asyncio
async def test_state_place_details_lookup_invalid_response(google_api_mock):
    google_api_mock.app.status = "ERROR"
    u = User(
        addr="27820001003",
        state=StateData(name="state_confirm_city"),
        session_id=1,
        answers={
            "state_city": "Cape Town",
            "google_session_token": "123",
            "place_id": "ChIJD7fiBh9u5kcRYJSMaMOCCwQ",
            "confirmed_contact": "no",
        },
    )
    app = Application(u)

    msg = Message(
        content="yes",
        to_addr="27820001002",
        from_addr="27820001003",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    await app.process_message(msg)
    assert u.state.name == "state_city"


@pytest.mark.asyncio
async def test_state_place_details_lookup_error(google_api_mock):
    google_api_mock.app.api_errormax = 3
    u = User(
        addr="27820001003",
        state=StateData(name="state_confirm_city"),
        session_id=1,
        answers={
            "state_city": "Cape Town",
            "google_session_token": "123",
            "place_id": "ChIJD7fiBh9u5kcRYJSMaMOCCwQ",
            "confirmed_contact": "no",
        },
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
    assert (
        reply.content
        == "Sorry, something went wrong. We have been notified. Please try again later"
    )


@pytest.mark.asyncio
async def test_state_place_details_lookup_temporary_error(google_api_mock):
    google_api_mock.app.api_errormax = 1
    u = User(
        addr="27820001003",
        state=StateData(name="state_confirm_city"),
        session_id=1,
        answers={
            "state_city": "Cape Town",
            "google_session_token": "123",
            "place_id": "ChIJD7fiBh9u5kcRYJSMaMOCCwQ",
            "confirmed_contact": "no",
        },
    )
    app = Application(u)

    msg = Message(
        content="yes",
        to_addr="27820001002",
        from_addr="27820001003",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    await app.process_message(msg)
    assert u.state.name == "state_age"


@pytest.mark.asyncio
async def test_state_place_details_lookup_confirmed_contact(google_api_mock):
    u = User(
        addr="27820001003",
        state=StateData(name="state_confirm_city"),
        session_id=1,
        answers={
            "state_city": "Cape Town",
            "google_session_token": "123",
            "place_id": "ChIJD7fiBh9u5kcRYJSMaMOCCwQ",
            "confirmed_contact": "yes",
        },
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
    assert u.state.name == "state_tracing"

    assert [r.path for r in google_api_mock.app.requests] == [
        "/maps/api/place/details/json"
    ]

    assert u.answers["city_location"] == "-03.866651+051.195827/"


@pytest.mark.asyncio
async def test_state_age():
    u = User(addr="27820001003", state=StateData(name="state_age"), session_id=1)
    app = Application(u)

    msg = Message(
        content="invalid",
        to_addr="27820001002",
        from_addr="27820001003",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert u.state.name == "state_age"

    assert reply.content == "\n".join(
        [
            "Please use numbers from list.",
            "",
            "How old are you?",
            "1. <18",
            "2. 18-39",
            "3. 40-65",
            "4. >65",
        ]
    )

    app.messages = []
    msg = Message(
        content="1",
        to_addr="27820001002",
        from_addr="27820001003",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert u.state.name == "state_fever"

    assert reply.content == "\n".join(
        [
            "Do you feel very hot or cold? Are you sweating or shivering? "
            "When you touch your forehead, does it feel hot?",
            "",
            "Reply",
            "1. Yes",
            "2. No",
        ]
    )


@pytest.mark.asyncio
async def test_state_fever():
    u = User(addr="27820001003", state=StateData(name="state_fever"), session_id=1)
    app = Application(u)

    msg = Message(
        content="invalid",
        to_addr="27820001002",
        from_addr="27820001003",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert u.state.name == "state_fever"

    assert reply.content == "\n".join(
        [
            "Please use numbers from list. Do you feel very hot or cold? Are you "
            + "sweating or shivering? When you touch your forehead, does it feel hot?",
            "",
            "Reply",
            "1. Yes",
            "2. No",
        ]
    )

    app.messages = []
    msg = Message(
        content="1",
        to_addr="27820001002",
        from_addr="27820001003",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert u.state.name == "state_cough"
    assert reply.content == "\n".join(
        ["Do you have a cough that recently started?", "", "Reply", "1. Yes", "2. No"]
    )


@pytest.mark.asyncio
async def test_state_cough():
    u = User(addr="27820001003", state=StateData(name="state_cough"), session_id=1)
    app = Application(u)

    msg = Message(
        content="invalid",
        to_addr="27820001002",
        from_addr="27820001003",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert u.state.name == "state_cough"

    assert reply.content == "\n".join(
        [
            "Please use numbers from list.",
            "Do you have a cough that recently started?",
            "",
            "Reply",
            "1. Yes",
            "2. No",
        ]
    )

    app.messages = []
    msg = Message(
        content="1",
        to_addr="27820001002",
        from_addr="27820001003",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert u.state.name == "state_sore_throat"
    assert reply.content == "\n".join(
        [
            "Do you have a sore throat, or pain when swallowing?",
            "",
            "Reply",
            "1. Yes",
            "2. No",
        ]
    )


@pytest.mark.asyncio
async def test_state_cough_confirmed_contact():
    u = User(
        addr="27820001003",
        state=StateData(name="state_fever"),
        session_id=1,
        answers={"confirmed_contact": "yes"},
    )
    app = Application(u)

    msg = Message(
        content="1",
        to_addr="27820001002",
        from_addr="27820001003",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert u.state.name == "state_cough"

    assert reply.content == "\n".join(
        [
            "Do you have a cough that recently started in the last week?",
            "",
            "Reply",
            "1. Yes",
            "2. No",
        ]
    )

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
    assert u.state.name == "state_cough"

    assert reply.content == "\n".join(
        [
            "This service works best when you select numbers from the list.",
            "",
            "Do you have a cough that recently started in the last week?",
            "",
            "Reply",
            "1. Yes",
            "2. No",
        ]
    )


@pytest.mark.asyncio
async def test_state_sore_throat():
    u = User(
        addr="27820001003", state=StateData(name="state_sore_throat"), session_id=1
    )
    app = Application(u)

    msg = Message(
        content="invalid",
        to_addr="27820001002",
        from_addr="27820001003",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert u.state.name == "state_sore_throat"

    assert reply.content == "\n".join(
        [
            "Please use numbers from list.",
            "Do you have a sore throat, or pain when swallowing?",
            "",
            "Reply",
            "1. Yes",
            "2. No",
        ]
    )

    app.messages = []
    msg = Message(
        content="1",
        to_addr="27820001002",
        from_addr="27820001003",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert u.state.name == "state_breathing"
    assert reply.content == "\n".join(
        [
            "Do you have breathlessness or a difficulty breathing, that you've "
            "noticed recently?",
            "Reply",
            "1. Yes",
            "2. No",
        ]
    )


@pytest.mark.asyncio
async def test_state_breathing():
    u = User(addr="27820001003", state=StateData(name="state_breathing"), session_id=1)
    app = Application(u)

    msg = Message(
        content="invalid",
        to_addr="27820001002",
        from_addr="27820001003",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert u.state.name == "state_breathing"

    assert reply.content == "\n".join(
        [
            "Please use numbers from list. Do you have breathlessness or a "
            "difficulty breathing, that you've noticed recently?",
            "Reply",
            "1. Yes",
            "2. No",
        ]
    )

    app.messages = []
    msg = Message(
        content="1",
        to_addr="27820001002",
        from_addr="27820001003",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert u.state.name == "state_exposure"
    assert reply.content == "\n".join(
        [
            "Have you been in close contact to someone confirmed to be "
            "infected with COVID19?",
            "",
            "Reply",
            "1. Yes",
            "2. No",
            "3. NOT SURE",
        ]
    )


@pytest.mark.asyncio
async def test_state_breathing_confirmed_contact():
    u = User(
        addr="27820001003",
        state=StateData(name="state_sore_throat"),
        session_id=1,
        answers={"confirmed_contact": "yes"},
    )
    app = Application(u)

    msg = Message(
        content="1",
        to_addr="27820001002",
        from_addr="27820001003",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert u.state.name == "state_breathing"

    assert reply.content == "\n".join(
        [
            "Do you have shortness of breath while resting or difficulty "
            "breathing, that you've noticed recently?",
            "",
            "Reply",
            "1. Yes",
            "2. No",
        ]
    )
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
    assert u.state.name == "state_breathing"

    assert reply.content == "\n".join(
        [
            "Please use numbers from list.",
            "",
            "Do you have shortness of breath while resting or difficulty "
            "breathing, that you've noticed recently?",
            "",
            "Reply",
            "1. Yes",
            "2. No",
        ]
    )


@pytest.mark.asyncio
async def test_state_taste_and_smell():
    u = User(
        addr="27820001003", state=StateData(name="state_taste_and_smell"), session_id=1
    )
    app = Application(u)

    msg = Message(
        content="invalid",
        to_addr="27820001002",
        from_addr="27820001003",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) <= 160
    assert u.state.name == "state_taste_and_smell"

    assert reply.content == "\n".join(
        [
            "This service works best when you select numbers from the list.",
            "Have you noticed any recent changes in your ability to taste or "
            "smell things?",
            "",
            "Reply",
            "1. Yes",
            "2. No",
        ]
    )

    app.messages = []
    msg = Message(
        content="1",
        to_addr="27820001002",
        from_addr="27820001003",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert u.state.name == "state_preexisting_conditions"


@pytest.mark.asyncio
async def test_state_preexisting_conditions():
    u = User(
        addr="27820001003", state=StateData(name="state_taste_and_smell"), session_id=1
    )
    app = Application(u)

    msg = Message(
        content="1",
        to_addr="27820001002",
        from_addr="27820001003",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) <= 160
    assert u.state.name == "state_preexisting_conditions"

    assert reply.content == "\n".join(
        [
            "Have you been diagnosed with either Obesity, Diabetes, "
            "Hypertension or Cardiovascular disease?",
            "",
            "Reply",
            "1. YES",
            "2. NO",
            "3. NOT SURE",
        ]
    )

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
    assert u.state.name == "state_preexisting_conditions"

    assert reply.content == "\n".join(
        [
            "Please use numbers from list.",
            "",
            "Have you been diagnosed with either Obesity, Diabetes, "
            "Hypertension or Cardiovascular disease?",
            "",
            "Reply",
            "1. YES",
            "2. NO",
            "3. NOT SURE",
        ]
    )


@pytest.mark.asyncio
async def test_state_preexisting_conditions_skip():
    u = User(
        addr="27820001003",
        state=StateData(name="state_taste_and_smell"),
        session_id=1,
        answers={"state_preexisting_conditions": "yes"},
    )
    app = Application(u)

    msg = Message(
        content="1",
        to_addr="27820001002",
        from_addr="27820001003",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) <= 160
    assert u.state.name == "state_age_years"


@pytest.mark.asyncio
async def test_state_exposure():
    u = User(addr="27820001003", state=StateData(name="state_exposure"), session_id=1)
    app = Application(u)

    msg = Message(
        content="invalid",
        to_addr="27820001002",
        from_addr="27820001003",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert u.state.name == "state_exposure"

    assert reply.content == "\n".join(
        [
            "Please use numbers from list. Have u been in contact with someone"
            " with COVID19 or been where COVID19 patients are treated?",
            "",
            "Reply",
            "1. Yes",
            "2. No",
            "3. NOT SURE",
        ]
    )

    app.messages = []
    msg = Message(
        content="1",
        to_addr="27820001002",
        from_addr="27820001003",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert u.state.name == "state_tracing"
    assert reply.content == "\n".join(
        [
            "Please confirm that the information you shared is correct & that the "
            "National Department of Health can contact you if necessary?",
            "",
            "Reply",
            "1. YES",
            "2. NO",
            "3. RESTART",
        ]
    )


@pytest.mark.asyncio
async def test_state_age_skip(google_api_mock):
    u = User(
        addr="27820001003",
        state=StateData(name="state_confirm_city"),
        session_id=1,
        answers={
            "state_age": "<18",
            "state_city": "Cape Town",
            "google_session_token": "123",
            "place_id": "ChIJD7fiBh9u5kcRYJSMaMOCCwQ",
        },
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
    assert u.state.name == "state_fever"


@pytest.mark.asyncio
async def test_state_age_years():
    u = User(addr="27820001003", state=StateData(name="state_age_years"), session_id=1)
    app = Application(u)

    msg = Message(
        content="invalid",
        to_addr="27820001002",
        from_addr="27820001003",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert u.state.name == "state_age_years"

    assert reply.content == "Please TYPE your age in years (eg. 35)"

    app.messages = []
    msg = Message(
        content="19",
        to_addr="27820001002",
        from_addr="27820001003",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert u.state.name == "state_province"
    assert u.answers["state_age"] == "18-40"


@pytest.mark.asyncio
async def test_state_age_years_error():
    u = User(addr="27820001003", state=StateData(name="state_age_years"), session_id=1)
    app = Application(u)

    msg = Message(
        content="-1",
        to_addr="27820001002",
        from_addr="27820001003",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert u.state.name == "state_age_years"
    assert reply.content == "Please TYPE your age in years (eg. 35)"


@pytest.mark.asyncio
async def test_state_age_years_le18():
    u = User(addr="27820001003", state=StateData(name="state_age_years"), session_id=1)
    app = Application(u)

    msg = Message(
        content="7",
        to_addr="27820001002",
        from_addr="27820001003",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    await app.process_message(msg)
    assert u.answers["state_age"] == "<18"


@pytest.mark.asyncio
async def test_state_age_years_40t65():
    u = User(addr="27820001003", state=StateData(name="state_age_years"), session_id=1)
    app = Application(u)

    msg = Message(
        content="53",
        to_addr="27820001002",
        from_addr="27820001003",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    await app.process_message(msg)
    assert u.answers["state_age"] == "40-65"


@pytest.mark.asyncio
async def test_state_age_years_gt65():
    u = User(addr="27820001003", state=StateData(name="state_age_years"), session_id=1)
    app = Application(u)

    msg = Message(
        content="68",
        to_addr="27820001002",
        from_addr="27820001003",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    await app.process_message(msg)
    assert u.answers["state_age"] == ">65"


@pytest.mark.asyncio
async def test_state_age_years_gt150():
    u = User(addr="27820001003", state=StateData(name="state_age_years"), session_id=1)
    app = Application(u)

    msg = Message(
        content="188",
        to_addr="27820001002",
        from_addr="27820001003",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 160
    assert u.state.name == "state_age_years"
    assert reply.content == "Please TYPE your age in years (eg. 35)"


@pytest.mark.asyncio
async def test_state_age_years_skip():
    u = User(
        addr="27820001003",
        state=StateData(name="state_preexisting_conditions"),
        session_id=1,
        answers={"state_age": "<18", "state_age_years": "17"},
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
    assert u.state.name == "state_province"


@pytest.mark.asyncio
async def test_state_tracing(eventstore_mock):
    def get_user(answers={}):
        return User(
            addr="27820001003",
            state=StateData(name="state_tracing"),
            session_id=1,
            answers=answers,
        )

    def get_message(content):
        return Message(
            content=content,
            to_addr="27820001002",
            from_addr="27820001003",
            transport_name="whatsapp",
            transport_type=Message.TRANSPORT_TYPE.HTTP_API,
        )

    u = get_user()
    app = Application(u)
    msg = Message(
        content="invalid",
        to_addr="27820001002",
        from_addr="27820001003",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) <= 160
    assert u.state.name == "state_tracing"

    assert reply.content == "\n".join(
        [
            "Please reply with numbers",
            "Is the information you shared correct & can the National Department "
            "of Health contact you if necessary?",
            "",
            "Reply",
            "1. YES",
            "2. NO",
            "3. RESTART",
        ]
    )

    app.messages = []
    [reply] = await app.process_message(get_message("yes"))
    assert len(reply.content) < 160

    assert (
        reply.content
        == "Complete this HealthCheck again in 7 days or sooner if you feel "
        "ill or you come into contact with someone infected with COVID-19"
    )
    assert reply.session_event == Message.SESSION_EVENT.CLOSE

    assert u.state.name == "state_start"

    assert [r.path for r in eventstore_mock.app.requests] == ["/api/v3/covid19triage/"]

    app = Application(get_user({"state_exposure": "yes"}))
    [reply] = await app.process_message(get_message("yes"))
    assert len(reply.content) < 160
    assert (
        reply.content == "We recommend you SELF-QUARANTINE for the next 10 days and do "
        "this HealthCheck daily to monitor your symptoms. Stay/sleep "
        "alone in a room with good air flow."
    )

    app = Application(get_user({"state_fever": "yes", "state_exposure": "yes"}))
    [reply] = await app.process_message(get_message("yes"))
    assert len(reply.content) < 160
    assert (
        reply.content
        == "You may be ELIGIBLE FOR COVID-19 TESTING. Go to a testing center "
        "or Call 0800029999 or visit your healthcare practitioner for "
        "info on what to do & how to test."
    )

    app = Application(get_user({}))
    [reply] = await app.process_message(get_message("no"))
    assert len(reply.content) <= 160

    assert reply.content == (
        "You will not be contacted. If you think you have COVID-19 please STAY "
        "HOME, avoid contact with other people in your community and self-quarantine."
        "\n1. START OVER"
    )

    app = Application(get_user({"state_exposure": "yes"}))
    [reply] = await app.process_message(get_message("no"))
    assert len(reply.content) <= 160

    assert reply.content == (
        "You won't be contacted. SELF-QUARANTINE for 10 days, do this HealthCheck "
        "daily to monitor symptoms. Stay/sleep alone in a room with good air flow."
        "\n1. START OVER"
    )

    app = Application(get_user({"state_fever": "yes", "state_exposure": "yes"}))
    [reply] = await app.process_message(get_message("no"))
    assert len(reply.content) <= 160

    assert reply.content == (
        "You will not be contacted. You may be ELIGIBLE FOR COVID-19 "
        "TESTING. Go to a testing center or Call 0800029999 or your "
        "healthcare practitioner for info."
    )

    eventstore_mock.app.triage_errormax = 3
    app = Application(get_user())
    [reply] = await app.process_message(get_message("yes"))
    assert (
        reply.content
        == "Sorry, something went wrong. We have been notified. Please try again later"
    )


@pytest.mark.asyncio
async def test_state_tracing_confirmed_contact(eventstore_mock):
    def get_user(answers={}):
        answers["confirmed_contact"] = "yes"
        return User(
            addr="27820001003",
            state=StateData(name="state_tracing"),
            session_id=1,
            answers=answers,
        )

    def get_message(content):
        return Message(
            content=content,
            to_addr="27820001002",
            from_addr="27820001003",
            transport_name="whatsapp",
            transport_type=Message.TRANSPORT_TYPE.HTTP_API,
        )

    u = get_user()
    app = Application(u)
    msg = Message(
        content="invalid",
        to_addr="27820001002",
        from_addr="27820001003",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) <= 160
    assert u.state.name == "state_tracing"

    assert reply.content == "\n".join(
        [
            "Please use numbers from the list.",
            "",
            "Finally, please confirm that the information you shared is "
            "ACCURATE to the best of your knowledge?",
            "",
            "Reply",
            "1. YES",
            "2. NO",
        ]
    )

    app = Application(get_user({"state_fever": "yes", "state_exposure": "yes"}))
    [reply] = await app.process_message(get_message("yes"))
    assert len(reply.content) < 160
    assert (
        reply.content
        == "You may be ELIGIBLE FOR COVID-19 TESTING. Go to a testing center "
        "or Call 0800029999 or visit your healthcare practitioner for "
        "info on what to do & how to test."
    )

    app = Application(get_user({"state_exposure": "yes"}))
    [reply] = await app.process_message(get_message("yes"))
    assert len(reply.content) < 160
    assert (
        reply.content == "We recommend you SELF-QUARANTINE for the next 10 days and do "
        "this HealthCheck daily to monitor your symptoms. Stay/sleep "
        "alone in a room with good air flow."
    )


@pytest.mark.asyncio
async def test_state_tracing_restart(eventstore_mock):
    u = User(
        addr="27820001003",
        state=StateData(name="state_tracing"),
        session_id=1,
        answers={},
    )
    app = Application(u)
    msg = Message(
        content="restart",
        to_addr="27820001002",
        from_addr="27820001003",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) <= 160
    assert u.state.name == "state_start"


def test_calculate_risk():
    def get_user(answers={}):
        return User(
            addr="27820001003",
            state=StateData(name="state_terms"),
            session_id=1,
            answers=answers,
        )

    app = Application(get_user({}))
    test = app.calculate_risk()
    assert test == "low"

    app = Application(get_user({"state_exposure": "yes"}))
    test = app.calculate_risk()
    assert test == "moderate"

    app = Application(get_user({"state_fever": "yes"}))
    test = app.calculate_risk()
    assert test == "moderate"

    app = Application(get_user({"state_fever": "yes", "state_exposure": "yes"}))
    test = app.calculate_risk()
    assert test == "high"

    app = Application(
        get_user({"state_cough": "yes", "state_fever": "yes", "state_exposure": "yes"})
    )
    test = app.calculate_risk()
    assert test == "high"

    app = Application(
        get_user({"state_cough": "yes", "state_fever": "yes", "state_age": ">65"})
    )
    test = app.calculate_risk()
    assert test == "high"

    app = Application(get_user({"state_cough": "yes", "state_fever": "yes"}))
    test = app.calculate_risk()
    assert test == "moderate"

    app = Application(
        get_user({"state_cough": "yes", "state_fever": "yes", "state_breathing": "yes"})
    )
    test = app.calculate_risk()
    assert test == "high"

    app = Application(get_user({"confirmed_contact": "yes"}))
    test = app.calculate_risk()
    assert test == "moderate"

    app = Application(get_user({"confirmed_contact": "yes", "state_fever": "yes"}))
    test = app.calculate_risk()
    assert test == "high"

    app = Application(
        get_user(
            {
                "confirmed_contact": "yes",
                "state_province": "ZA-WC",
                "state_age_years": "34",
            }
        )
    )
    test = app.calculate_risk()
    assert test == "moderate"

    app = Application(
        get_user(
            {
                "confirmed_contact": "yes",
                "state_province": "ZA-WC",
                "state_age_years": "56",
                "state_fever": "yes",
            }
        )
    )
    test = app.calculate_risk()
    assert test == "high"

    app = Application(
        get_user(
            {
                "confirmed_contact": "yes",
                "state_province": "ZA-WC",
                "state_age_years": "34",
                "state_preexisting_conditions": "yes",
                "state_fever": "yes",
            }
        )
    )
    test = app.calculate_risk()
    assert test == "high"


def test_format_location():
    u = User(
        addr="27820001003",
        state=StateData(name="state_tracing"),
        session_id=1,
        answers={},
    )
    app = Application(u)
    location = app.format_location(-3.866_651_000_00, 51.195_827_000_00)
    assert location == "-03.866651+051.195827/"
    location = app.format_location(-3.0, 51.195_827_000_00)
    assert location == "-03+051.195827/"
