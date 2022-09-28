import json

import pytest
from sanic import Sanic, response

from mqr import config
from mqr.baseline_ussd import Application
from vaccine.models import Message, StateData, User
from vaccine.testing import TState, run_sanic


def get_rapidpro_contact(
    urn, mqr_consent="Accepted", mqr_arm="RCM_SMS", midline_started=""
):
    return {
        "uuid": "b733e997-b0b4-4d4d-a3ad-0546e1644aa9",
        "name": "",
        "language": "zul",
        "groups": [],
        "fields": {
            "mqr_consent": mqr_consent,
            "mqr_arm": mqr_arm,
            "midline_survey_completed": midline_started,
        },
        "blocked": False,
        "stopped": False,
        "created_on": "2015-11-11T08:30:24.922024+00:00",
        "modified_on": "2015-11-11T08:30:25.525936+00:00",
        "urns": [urn],
    }


@pytest.fixture
async def rapidpro_mock():
    Sanic.test_mode = True
    app = Sanic("mock_rapidpro")
    tstate = TState()

    @app.route("/api/v2/contacts.json", methods=["GET"])
    def get_contact(request):
        tstate.requests.append(request)
        if tstate.errormax:
            if tstate.errors < tstate.errormax:
                tstate.errors += 1
                return response.json({}, status=500)

        contacts = []
        urn = request.args.get("urn")
        if urn == "whatsapp:27820001003":
            contacts = [get_rapidpro_contact(urn)]

        if urn == "whatsapp:27820001004":
            contacts = [get_rapidpro_contact(urn, "Declined", "BCM")]

        if urn == "whatsapp:27820001006":
            contacts = [get_rapidpro_contact(urn, midline_started="False")]

        return response.json(
            {
                "results": contacts,
                "next": None,
            },
            status=200,
        )

    @app.route("/api/v2/flow_starts.json", methods=["POST"])
    def start_flow(request):
        tstate.requests.append(request)
        return response.json({}, status=200)

    async with run_sanic(app) as server:
        url = config.RAPIDPRO_URL
        config.RAPIDPRO_URL = f"http://{server.host}:{server.port}"
        config.RAPIDPRO_TOKEN = "testtoken"
        server.tstate = tstate
        yield server
        config.RAPIDPRO_URL = url


@pytest.fixture
async def eventstore_mock():
    Sanic.test_mode = True
    app = Sanic("mock_eventstore")
    tstate = TState()
    tstate.not_found_errormax = 0
    tstate.not_found_errors = 0

    @app.route("/api/v1/mqrbaselinesurvey/", methods=["POST"])
    def valid_baseline_survey(request):
        tstate.requests.append(request)
        if tstate.errormax:
            if tstate.errors < tstate.errormax:
                tstate.errors += 1
                return response.json({}, status=500)
        return response.json({})

    @app.route("/api/v1/mqrbaselinesurvey/27820001003/", methods=["GET"])
    def get_baseline_survey_not_found(request):
        tstate.requests.append(request)
        if tstate.not_found_errormax:
            if tstate.not_found_errors < tstate.not_found_errormax:
                tstate.not_found_errors += 1
                return response.json({}, status=500)
        return response.json({"detail": "Not found."}, status=404)

    @app.route("/api/v1/mqrbaselinesurvey/27820001004/", methods=["GET"])
    def get_baseline_survey_found(request):
        tstate.requests.append(request)
        return response.json({"msisdn": "27820001004"})

    async with run_sanic(app) as server:
        url = config.EVENTSTORE_API_URL
        config.EVENTSTORE_API_URL = f"http://{server.host}:{server.port}"
        server.tstate = tstate
        yield server
        config.EVENTSTORE_API_URL = url


@pytest.mark.asyncio
async def test_state_survey_start(rapidpro_mock, eventstore_mock):
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

    assert [r.path for r in rapidpro_mock.tstate.requests] == ["/api/v2/contacts.json"]
    assert [r.path for r in eventstore_mock.tstate.requests] == [
        "/api/v1/mqrbaselinesurvey/27820001003/"
    ]


@pytest.mark.asyncio
async def test_state_survey_start_midline(rapidpro_mock):
    u = User(addr="27820001006", state=StateData())
    app = Application(u)
    msg = Message(
        content=None,
        to_addr="27820001002",
        from_addr="27820001006",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
        session_event=Message.SESSION_EVENT.NEW,
    )
    [reply] = await app.process_message(msg)
    assert len(reply.content) < 140
    assert reply.content == "\n".join(
        [
            "1/16",
            "",
            "Do you eat fruits at least once a day?",
            "1. Yes",
            "2. No",
            "3. Skip",
        ]
    )

    assert [r.path for r in rapidpro_mock.tstate.requests] == ["/api/v2/contacts.json"]


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
    assert reply.content == "\n".join(
        [
            "You have dialed the wrong number.",
            "",
            "Dial *134*550*2# when you're at a clinic to register on MomConnect or "
            "dial *134*550*7# to update details",
        ]
    )

    assert [r.path for r in rapidpro_mock.tstate.requests] == ["/api/v2/contacts.json"]


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
    assert len(reply.content) < 160
    assert reply.content == "\n".join(
        [
            "You have dialed the wrong number.",
            "",
            "Dial *134*550*2# when you're at a clinic to register on MomConnect or "
            "dial *134*550*7# to update details",
        ]
    )

    assert [r.path for r in rapidpro_mock.tstate.requests] == ["/api/v2/contacts.json"]


@pytest.mark.asyncio
async def test_state_start_temporary_errors(rapidpro_mock):
    rapidpro_mock.tstate.errormax = 3
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

    assert reply.content == (
        "Sorry, something went wrong. We have been notified. Please try again later"
    )

    assert len(rapidpro_mock.tstate.requests) == 3


@pytest.mark.asyncio
async def test_state_check_existing_result_temporary_errors(eventstore_mock):
    eventstore_mock.tstate.not_found_errormax = 3
    u = User(addr="27820001003", state=StateData(name="state_check_existing_result"))
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

    assert reply.content == (
        "Sorry, something went wrong. We have been notified. Please try again later"
    )

    assert len(eventstore_mock.tstate.requests) == 3


@pytest.mark.asyncio
async def test_state_check_existing_result_found(eventstore_mock):
    u = User(addr="27820001004", state=StateData(name="state_check_existing_result"))
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
            "Thanks, you have already completed this survey.",
            "",
            "You will get your weekly message soon.",
        ]
    )
    assert u.state.name == "state_start"

    assert [r.path for r in eventstore_mock.tstate.requests] == [
        "/api/v1/mqrbaselinesurvey/27820001004/"
    ]


@pytest.mark.asyncio
async def test_state_breastfeed():
    user = User(
        addr="278201234567",
        state=StateData(name="state_breastfeed"),
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
    assert user.state.name == "state_breastfeed"


@pytest.mark.asyncio
async def test_state_breastfeed_valid():
    user = User(addr="27820001003", state=StateData("state_breastfeed"))
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
async def test_state_breastfeed_period_invalid():
    user = User(
        addr="278201234567",
        state=StateData(name="state_breastfeed_period"),
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
    assert user.state.name == "state_breastfeed_period"
    assert reply.content == "\n".join(
        [
            "Please use numbers from list.",
            "1. 0-3 months",
            "2. 4-5 months",
            "3. For 6 months",
            "4. Longer than 6 months",
            "5. I don't want to only breastfeed",
            "6. I don't know",
            "7. Skip",
        ]
    )


@pytest.mark.asyncio
async def test_state_breastfeed_period_valid():
    user = User(
        addr="278201234567",
        state=StateData(name="state_breastfeed_period"),
        session_id=1,
        answers={},
    )
    app = Application(user)
    msg = Message(
        content="1",
        to_addr="278201234567",
        from_addr="27820001003",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.USSD,
    )
    [reply] = await app.process_message(msg)

    assert len(reply.content) < 160
    assert user.state.name == "state_vaccine_importance_question"


@pytest.mark.asyncio
async def test_state_vegetables():
    user = User(addr="27820001003", state=StateData("state_vegetables"))
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
        "Since becoming pregnant, do you eat vegetables at least once a day?\n"
        "1. Yes\n"
        "2. No\n"
        "3. Skip"
    )


@pytest.mark.asyncio
async def test_state_fruit():
    user = User(addr="27820001003", state=StateData("state_fruit"))
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
        "Since becoming pregnant, do you eat fruit at least once a day?\n"
        "1. Yes\n"
        "2. No\n"
        "3. Skip"
    )


@pytest.mark.asyncio
async def test_state_dairy():
    user = User(addr="27820001003", state=StateData("state_dairy"))
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
        "least once a day?\n"
        "1. Yes\n"
        "2. No\n"
        "3. Skip"
    )


@pytest.mark.asyncio
async def test_state_liver_frequency():
    user = User(addr="27820001003", state=StateData("state_liver_frequency"))
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
async def test_state_danger_sign1():
    user = User(addr="27820001003", state=StateData("state_danger_sign1"))
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
        "1. Weight gain of 4-5 kilograms\n"
        "2. Vaginal bleeding\n"
        "3. Nose bleeds\n"
        "4. Skip"
    )


@pytest.mark.asyncio
async def test_state_danger_sign2():
    user = User(addr="27820001003", state=StateData("state_danger_sign2"))
    app = Application(user)
    msg = Message(
        content=None,
        to_addr="27820001002",
        from_addr="27820001003",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
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
async def test_state_marital_status():
    user = User(addr="27820001003", state=StateData("state_marital_status"))
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
async def test_state_vaccine_importance_question():
    user = User(
        addr="278201234567",
        state=StateData(name="state_vaccine_importance_question"),
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
    assert user.state.name == "state_vaccine_importance_question"
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
async def test_state_vaccine_importance():
    user = User(
        addr="278201234567",
        state=StateData(name="state_vaccine_importance"),
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
    assert user.state.name == "state_vaccine_importance"
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
async def test_state_vaccine_benefits_question():
    user = User(
        addr="278201234567",
        state=StateData(name="state_vaccine_benefits_question"),
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
    assert user.state.name == "state_vaccine_benefits_question"
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
async def test_state_vaccine_benefits():
    user = User(
        addr="278201234567",
        state=StateData(name="state_vaccine_benefits"),
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
    assert user.state.name == "state_vaccine_benefits"
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
async def test_state_clinic_visit_frequency_question():
    user = User(
        addr="278201234567",
        state=StateData(name="state_clinic_visit_frequency_question"),
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
    assert user.state.name == "state_clinic_visit_frequency_question"
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
async def test_state_clinic_visit_frequency():
    user = User(
        addr="278201234567",
        state=StateData(name="state_clinic_visit_frequency"),
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
    assert user.state.name == "state_clinic_visit_frequency"
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
async def test_state_education_level_question():
    user = User(
        addr="278201234567",
        state=StateData(name="state_education_level_question"),
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
    assert user.state.name == "state_education_level_question"
    assert reply.content == "\n".join(
        [
            "13/13 \n"
            "\n"
            "Which answer best describes your highest level of education?\n"
            "1. Next"
        ]
    )


@pytest.mark.asyncio
async def test_state_education_level_question_valid():
    user = User(
        addr="278201234567",
        state=StateData(name="state_education_level_question"),
        session_id=1,
        answers={},
    )
    app = Application(user)
    msg = Message(
        content="1",
        to_addr="278201234567",
        from_addr="27820001003",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.USSD,
    )
    [reply] = await app.process_message(msg)

    assert len(reply.content) < 160
    assert user.state.name == "state_education_level"


@pytest.mark.asyncio
async def test_state_education_level():
    user = User(
        addr="278201234567",
        state=StateData(name="state_education_level"),
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
    assert user.state.name == "state_education_level"
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


@pytest.mark.asyncio
async def test_state_education_level_submit(rapidpro_mock, eventstore_mock):
    user = User(
        addr="278201234567",
        state=StateData(name="state_education_level"),
        session_id=1,
        answers={
            "state_breastfeed": "yes",
            "state_breastfeed_period": "0_3_months",
            "state_vaccine_importance": "strongly_agree",
            "state_vaccine_benefits": "strongly_agree",
            "state_clinic_visit_frequency": "more_than_once_a_month",
            "state_vegetables": "yes",
            "state_fruit": "yes",
            "state_dairy": "yes",
            "state_liver_frequency": "2_3_times_week",
            "state_danger_sign1": "weight_gain",
            "state_danger_sign2": "swollen_feet_legs",
            "state_marital_status": "never_married",
        },
    )
    app = Application(user)
    msg = Message(
        content="1",
        to_addr="278201234567",
        from_addr="27820001003",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.USSD,
    )
    [reply] = await app.process_message(msg)

    assert len(reply.content) <= 160
    assert user.state.name == "state_start"

    assert reply.content == "\n".join(
        [
            "Thank you for answering. You'll get your R5 airtime in the next 24 hours "
            "& your first message will be sent soon",
            "Dial *134*550*7# (free) to update your details",
        ]
    )

    assert [r.path for r in eventstore_mock.tstate.requests] == [
        "/api/v1/mqrbaselinesurvey/"
    ]

    request = eventstore_mock.tstate.requests[0]
    assert json.loads(request.body.decode("utf-8")) == {
        "msisdn": "27820001003",
        "breastfeed": "yes",
        "breastfeed_period": "0_3_months",
        "vaccine_importance": "strongly_agree",
        "vaccine_benefits": "strongly_agree",
        "clinic_visit_frequency": "more_than_once_a_month",
        "vegetables": "yes",
        "fruit": "yes",
        "dairy": "yes",
        "liver_frequency": "2_3_times_week",
        "danger_sign1": "weight_gain",
        "danger_sign2": "swollen_feet_legs",
        "marital_status": "never_married",
        "education_level": "less_grade_7",
    }

    assert [r.path for r in rapidpro_mock.tstate.requests] == [
        "/api/v2/flow_starts.json"
    ]
    request = rapidpro_mock.tstate.requests[0]
    assert json.loads(request.body.decode("utf-8")) == {
        "flow": config.RAPIDPRO_BASELINE_SURVEY_COMPLETE_FLOW,
        "urns": ["whatsapp:27820001003"],
    }
