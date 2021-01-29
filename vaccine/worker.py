import logging
from asyncio import get_event_loop
from json import JSONDecodeError
from typing import Callable

from aio_pika import ExchangeType, IncomingMessage, connect_robust

from vaccine import config
from vaccine.models import Event, Message

logging.basicConfig(level=config.LOG_LEVEL.upper())
logger = logging.getLogger(__name__)


class Worker:
    async def setup(self):
        self.connection = await connect_robust(config.AMQP_URL)
        self.channel = await self.connection.channel()
        await self.channel.set_qos(prefetch_count=config.CONCURRENCY)
        self.exchange = await self.channel.declare_exchange(
            "vumi", type=ExchangeType.DIRECT, durable=True, auto_delete=False
        )

        self.inbound_queue = await self.setup_consume(
            f"{config.TRANSPORT_NAME}.inbound", self.process_message
        )
        self.event_queue = await self.setup_consume(
            f"{config.TRANSPORT_NAME}.event", self.process_event
        )

    async def setup_consume(self, routing_key: str, callback: Callable):
        queue = await self.channel.declare_queue(
            routing_key, durable=True, auto_delete=False
        )
        await queue.bind(self.exchange, routing_key)
        await queue.consume(callback)
        return queue

    async def teardown(self):
        await self.connection.close()

    async def process_message(self, amqp_msg: IncomingMessage):
        try:
            msg = Message.from_json(amqp_msg.body.decode("utf-8"))
        except (UnicodeDecodeError, JSONDecodeError, TypeError, KeyError, ValueError):
            print("invalid message body")
            logger.exception(f"Invalid message body {amqp_msg.body!r}")
            await amqp_msg.reject(requeue=False)
            return

        async with amqp_msg.process(requeue=True):
            logger.debug(f"Processing inbound message {msg}")

    async def process_event(self, amqp_msg: IncomingMessage):
        try:
            event = Event.from_json(amqp_msg.body.decode("utf-8"))
        except (UnicodeDecodeError, JSONDecodeError, TypeError, KeyError, ValueError):
            logger.exception(f"Invalid event body {amqp_msg.body!r}")
            await amqp_msg.reject(requeue=False)
            return

        async with amqp_msg.process(requeue=True):
            logger.debug(f"Processing event {event}")


if __name__ == "__main__":  # pragma: no cover
    worker = Worker()
    loop = get_event_loop()
    loop.run_until_complete(worker.setup())
    logger.info("Worker running")
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        loop.run_until_complete(worker.teardown())
