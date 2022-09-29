import json
import logging
from asyncio import Future, sleep
from datetime import datetime, timezone
from io import StringIO

import pytest
import redis.asyncio as aioredis
from aio_pika import DeliveryMode, Exchange
from aio_pika import Message as AMQPMessage
from aio_pika import Queue, connect_robust
from sanic import Sanic, response

from vaccine.models import Answer, Event, Message, StateData, User
from vaccine.testing import TState, run_sanic
from vaccine.worker import AnswerWorker, Worker, config, logger


@pytest.fixture(autouse=True)
async def cleanup():
    """
    Ensure that we always cleanup redis and amqp
    """
    redis = aioredis.from_url(config.REDIS_URL, encoding="utf-8", decode_responses=True)
    for key in await redis.keys("user*"):
        await redis.delete(key)
    await redis.close()

    connection = await connect_robust(config.AMQP_URL)
    async with connection:
        channel = await connection.channel()
        for routing_key in [
            f"{config.TRANSPORT_NAME}.inbound",
            f"{config.TRANSPORT_NAME}.outbound",
            f"{config.TRANSPORT_NAME}.event",
            f"{config.TRANSPORT_NAME}.answer",
        ]:
            queue = await channel.declare_queue(
                routing_key, durable=True, auto_delete=False
            )
            while True:
                message = await queue.get(fail=False)
                if message is None:
                    break
                message.ack()


@pytest.fixture
async def worker():
    worker = Worker()
    await worker.setup()
    yield worker
    await worker.teardown()


@pytest.fixture
async def redis():
    redis = aioredis.from_url(config.REDIS_URL, encoding="utf-8", decode_responses=True)
    yield redis
    await redis.close()


async def send_inbound_amqp_message(exchange: Exchange, queue: str, message: bytes):
    await exchange.publish(
        AMQPMessage(
            message,
            delivery_mode=DeliveryMode.PERSISTENT,
            content_type="application/json",
            content_encoding="UTF-8",
        ),
        routing_key=queue,
    )


async def get_amqp_message(queue: Queue):
    message = await queue.get(timeout=1)
    assert message is not None
    await message.ack()
    return message


@pytest.mark.asyncio
async def test_worker_invalid_inbound(worker: Worker):
    """
    Should throw away invalid messages
    """
    log_stream = StringIO()
    logger.addHandler(logging.StreamHandler(log_stream))
    logger.setLevel(logging.DEBUG)
    await send_inbound_amqp_message(worker.exchange, "whatsapp.inbound", b"invalid")
    assert "Invalid message body b'invalid'" in log_stream.getvalue()
    assert "JSONDecodeError" in log_stream.getvalue()


@pytest.mark.asyncio
async def test_worker_invalid_event(worker: Worker):
    """
    Should throw away invalid events
    """
    log_stream = StringIO()
    logger.addHandler(logging.StreamHandler(log_stream))
    await send_inbound_amqp_message(worker.exchange, "whatsapp.event", b"invalid")
    assert "Invalid event body b'invalid'" in log_stream.getvalue()
    assert "JSONDecodeError" in log_stream.getvalue()


@pytest.mark.asyncio
async def test_worker_valid_inbound(worker: Worker, redis: aioredis.Redis):
    """
    Should process message
    """
    log_stream = StringIO()
    logger.addHandler(logging.StreamHandler(log_stream))
    logger.setLevel(logging.DEBUG)
    msg = Message(
        to_addr="27820001001",
        from_addr="27820001002",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    ob_queue = await worker.channel.declare_queue("whatsapp.outbound", durable=True)
    await ob_queue.bind(worker.exchange, "whatsapp.outbound")

    await send_inbound_amqp_message(
        worker.exchange, "whatsapp.inbound", msg.to_json().encode("utf-8")
    )

    # Setting the user data is the last action performed, so wait up to 1s for it to
    # complete
    user_data = None
    for _ in range(10):
        user_data = await redis.get("user.27820001002")
        if user_data is None:
            await sleep(0.1)  # pragma: no cover
    await redis.delete("user.27820001002")

    assert json.loads(user_data or "")["addr"] == "27820001002"

    assert "Processing inbound message" in log_stream.getvalue()
    assert repr(msg) in log_stream.getvalue()
    await get_amqp_message(ob_queue)


@pytest.mark.asyncio
async def test_worker_valid_answer(worker: Worker, redis: aioredis.Redis):
    """
    If the application generates an answer, should put it on the queue
    """
    msg = Message(
        to_addr="27820001001",
        from_addr="27820001002",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
        content="1",
    )
    ob_queue = await worker.channel.declare_queue("whatsapp.outbound", durable=True)
    await ob_queue.bind(worker.exchange, "whatsapp.outbound")
    ans_queue = await worker.channel.declare_queue("whatsapp.answer", durable=True)
    await ans_queue.bind(worker.exchange, "whatsapp.answer")
    worker.answer_worker = "not none"

    user = User(
        addr="27820001002", state=StateData(name="state_occupation"), session_id="1"
    )
    await redis.set("user.27820001002", user.to_json())

    await send_inbound_amqp_message(
        worker.exchange, "whatsapp.inbound", msg.to_json().encode("utf-8")
    )

    # Setting the user data is the last action performed, so wait up to 1s for it to
    # complete
    user_data = None
    for _ in range(10):
        user_data = await redis.get("user.27820001002")
        if user_data is None:
            await sleep(0.1)  # pragma: no cover
    await redis.delete("user.27820001002")

    await get_amqp_message(ob_queue)
    answer = await get_amqp_message(ans_queue)
    answer = Answer.from_json(answer.body.decode())
    assert answer.question == "state_occupation"
    assert answer.response == "hcw"
    worker.answer_worker = None


@pytest.mark.asyncio
async def test_setup_answer_worker():
    """
    If the required config fields are set, then the answer worker should be set up
    """
    config.ANSWER_API_URL = "http://example.org"
    config.ANSWER_API_TOKEN = "testtoken"
    config.ANSWER_RESOURCE_ID = "96ac814d-b9b4-48ae-bcef-997a724cdacf"
    config.ANSWER_BATCH_TIME = 0.1
    worker = Worker()
    await worker.setup()
    assert worker.answer_worker is not None
    await worker.teardown()
    config.ANSWER_API_URL = None
    config.ANSWER_API_TOKEN = None
    config.ANSWER_BATCH_TIME = 5
    config.ANSWER_RESOURCE_ID = None


@pytest.mark.asyncio
async def test_worker_valid_event(worker: Worker):
    """
    Should process event
    """
    log_stream = StringIO()
    logger.addHandler(logging.StreamHandler(log_stream))
    logger.setLevel(logging.DEBUG)
    event = Event(
        user_message_id="message-id",
        event_type=Event.EVENT_TYPE.ACK,
        sent_message_id="message-id",
    )
    await send_inbound_amqp_message(
        worker.exchange, "whatsapp.event", event.to_json().encode("utf-8")
    )
    assert "Processing event" in log_stream.getvalue()
    assert repr(event) in log_stream.getvalue()


@pytest.fixture
async def flow_results_mock_server():
    Sanic.test_mode = True
    app = Sanic("mock_whatsapp")
    tstate = TState()
    tstate.future = Future()

    @app.route("flow-results/packages/invalid/responses", methods=["POST"])
    async def invalid(request):
        tstate.future.set_result(request)
        return response.json({}, status=500)

    @app.route("flow-results/packages/usererror/responses", methods=["POST"])
    async def user_error(request):
        tstate.requests.append(request)
        for a in request.json["data"]["attributes"]["responses"]:
            if a[5] is None:
                return response.json({}, status=400)
        return response.json({})

    @app.route("flow-results/packages/duplicate/responses", methods=["POST"])
    async def duplicate(request):
        tstate.requests.append(request)
        return response.json(
            {
                "data": {
                    "attributes": {
                        "responses": ["row_id is not unique for flow question"]
                    }
                }
            },
            status=400,
        )

    @app.route("flow-results/packages/<flow_id:uuid>/responses", methods=["POST"])
    async def messages(request, flow_id):
        tstate.future.set_result(request)
        return response.json({})

    async with run_sanic(app) as server:
        server.tstate = tstate
        yield server


@pytest.fixture
async def connection():
    connection = await connect_robust(config.AMQP_URL)
    yield connection
    await connection.close()


@pytest.fixture
async def answer_worker(connection, flow_results_mock_server):
    url = f"http://{flow_results_mock_server.host}:{flow_results_mock_server.port}"
    config.ANSWER_BATCH_TIME = 0.1
    worker = AnswerWorker(
        connection=connection,
        url=url,
        token="testtoken",
        resource_id="96ac814d-b9b4-48ae-bcef-997a724cdacf",
    )
    await worker.setup()
    yield worker
    await worker.teardown()
    config.ANSWER_BATCH_TIME = 5


@pytest.mark.asyncio
async def test_answer_worker_push_results(answer_worker, flow_results_mock_server):
    """
    If there are any results, should push results to the configured API endpoint
    """
    await send_inbound_amqp_message(
        answer_worker.exchange,
        "whatsapp.answer",
        Answer(
            question="question",
            response="response",
            address="27820001001",
            session_id="session_id",
            row_id="1",
            timestamp=datetime(2021, 2, 3, 4, 5, 6, tzinfo=timezone.utc),
        )
        .to_json()
        .encode(),
    )

    request = await flow_results_mock_server.tstate.future
    assert request.json["data"]["attributes"]["responses"] == [
        [
            "2021-02-03T04:05:06+00:00",
            "1",
            "27820001001",
            "session_id",
            "question",
            "response",
            {},
        ]
    ]

    # Allow answers to be acked
    await sleep(0.1)


@pytest.mark.asyncio
async def test_answer_worker_push_results_server_down(
    answer_worker, flow_results_mock_server
):
    """
    If the server is down, then we should log the error and carry on
    """
    log_stream = StringIO()
    logger.addHandler(logging.StreamHandler(log_stream))
    logger.setLevel(logging.DEBUG)
    answer_worker.resource_id = "invalid"
    await send_inbound_amqp_message(
        answer_worker.exchange,
        "whatsapp.answer",
        Answer(
            question="question",
            response="response",
            address="27820001001",
            session_id="session_id",
            row_id="1",
            timestamp=datetime(2021, 2, 3, 4, 5, 6, tzinfo=timezone.utc),
        )
        .to_json()
        .encode(),
    )

    await flow_results_mock_server.tstate.future
    # wait for worker to log error
    await sleep(0.1)
    assert "Error sending results to flow results server" in log_stream.getvalue()

    assert len(answer_worker.answers) == 1

    for msg in answer_worker.answers:
        msg.ack()


@pytest.mark.asyncio
async def test_answer_worker_push_results_user_error(
    answer_worker, flow_results_mock_server
):
    """
    If there is a 400 response, then submit each answer separately, and log and nack the
    one that is an issue
    """
    log_stream = StringIO()
    logger.addHandler(logging.StreamHandler(log_stream))
    logger.setLevel(logging.DEBUG)
    answer_worker.resource_id = "usererror"
    await send_inbound_amqp_message(
        answer_worker.exchange,
        "whatsapp.answer",
        Answer(
            question="question",
            response="answer",
            address="27820001001",
            session_id="session_id",
            row_id="1",
            timestamp=datetime(2021, 2, 3, 4, 5, 6, tzinfo=timezone.utc),
        )
        .to_json()
        .encode(),
    )
    await send_inbound_amqp_message(
        answer_worker.exchange,
        "whatsapp.answer",
        Answer(
            question="question",
            response=None,
            address="27820001001",
            session_id="session_id",
            row_id="1",
            timestamp=datetime(2021, 2, 3, 4, 5, 6, tzinfo=timezone.utc),
        )
        .to_json()
        .encode(),
    )

    # wait for worker to log error
    for _ in range(10):
        if len(flow_results_mock_server.tstate.requests) == 3:
            break
        await sleep(0.1)
    assert "Error sending results to flow results server" in log_stream.getvalue()

    assert len(answer_worker.answers) == 0


@pytest.mark.asyncio
async def test_answer_worker_push_results_duplicate(
    answer_worker, flow_results_mock_server
):
    """
    If there is a 400 response, then submit each answer separately, and if it's a
    duplicate submission error, ignore it.
    """
    log_stream = StringIO()
    logger.addHandler(logging.StreamHandler(log_stream))
    logger.setLevel(logging.DEBUG)
    answer_worker.resource_id = "duplicate"
    await send_inbound_amqp_message(
        answer_worker.exchange,
        "whatsapp.answer",
        Answer(
            question="question",
            response="answer",
            address="27820001001",
            session_id="session_id",
            row_id="1",
            timestamp=datetime(2021, 2, 3, 4, 5, 6, tzinfo=timezone.utc),
        )
        .to_json()
        .encode(),
    )

    # wait for worker to log error
    for _ in range(10):
        if len(flow_results_mock_server.tstate.requests) == 2:
            break
        await sleep(0.1)
    assert log_stream.getvalue() == ""
    assert len(answer_worker.answers) == 0


@pytest.mark.asyncio
async def test_answer_worker_invalid_message_body(answer_worker):
    """
    If the server is down, then we should log the error and carry on
    """
    log_stream = StringIO()
    logger.addHandler(logging.StreamHandler(log_stream))
    logger.setLevel(logging.DEBUG)
    config.ANSWER_RESOURCE_ID = "invalid"
    await send_inbound_amqp_message(answer_worker.exchange, "whatsapp.answer", b"{}")

    # wait for worker to log error
    await sleep(0.1)
    assert "Invalid answer body" in log_stream.getvalue()

    assert len(answer_worker.answers) == 0


@pytest.mark.asyncio
async def test_answer_worker_empty_response(answer_worker):
    """
    If the response is none the answer should be ignored
    """
    await send_inbound_amqp_message(
        answer_worker.exchange,
        "whatsapp.answer",
        Answer(
            question="question",
            response=None,
            address="27820001001",
            session_id="session_id",
            row_id="1",
            timestamp=datetime(2021, 2, 3, 4, 5, 6, tzinfo=timezone.utc),
        )
        .to_json()
        .encode(),
    )

    # wait for worker to log error
    await sleep(0.1)
    assert len(answer_worker.answers) == 0
