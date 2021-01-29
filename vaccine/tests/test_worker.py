import logging
from io import StringIO

import pytest
from aio_pika import DeliveryMode, Exchange
from aio_pika import Message as AMQPMessage

from vaccine.models import Event, Message
from vaccine.worker import Worker, logger


@pytest.fixture
async def worker():
    worker = Worker()
    await worker.setup()
    yield worker
    await worker.teardown()


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
async def test_worker_valid_inbound(worker: Worker):
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
    await send_inbound_amqp_message(
        worker.exchange, "whatsapp.inbound", msg.to_json().encode("utf-8")
    )
    assert "Processing inbound message" in log_stream.getvalue()
    assert repr(msg) in log_stream.getvalue()


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
