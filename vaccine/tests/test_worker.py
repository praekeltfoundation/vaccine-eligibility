import json
import logging
from asyncio import sleep
from io import StringIO

import aioredis
import pytest
from aio_pika import DeliveryMode, Exchange
from aio_pika import Message as AMQPMessage
from aio_pika import Queue

from vaccine import config
from vaccine.models import Event, Message
from vaccine.worker import Worker, logger


@pytest.fixture
async def worker():
    worker = Worker()
    await worker.setup()
    yield worker
    await worker.teardown()


@pytest.fixture
async def redis():
    redis = await aioredis.create_redis_pool(config.REDIS_URL)
    yield redis
    redis.close()
    await redis.wait_closed()


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
        user_data = await redis.get("user.27820001002", encoding="utf-8")
        if user_data is None:
            await sleep(0.1)
    await redis.delete("user.27820001002")

    assert json.loads(user_data)["addr"] == "27820001002"

    assert "Processing inbound message" in log_stream.getvalue()
    assert repr(msg) in log_stream.getvalue()
    await get_amqp_message(ob_queue)


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
