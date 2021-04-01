import logging
from asyncio import get_event_loop
from json import JSONDecodeError
from typing import Callable

import aioredis
from aio_pika import ExchangeType, IncomingMessage
from aio_pika import Message as AMQPMessage
from aio_pika import connect_robust
from aio_pika.message import DeliveryMode

from vaccine import config
from vaccine.application import Application
from vaccine.models import Answer, Event, Message, User

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

        self.redis = await aioredis.create_redis_pool(config.REDIS_URL)

    async def setup_consume(self, routing_key: str, callback: Callable):
        queue = await self.channel.declare_queue(
            routing_key, durable=True, auto_delete=False
        )
        await queue.bind(self.exchange, routing_key)
        await queue.consume(callback)
        return queue

    async def teardown(self):
        await self.connection.close()
        self.redis.close()
        await self.redis.wait_closed()

    async def process_message(self, amqp_msg: IncomingMessage):
        try:
            msg = Message.from_json(amqp_msg.body.decode("utf-8"))
        except (UnicodeDecodeError, JSONDecodeError, TypeError, KeyError, ValueError):
            logger.exception(f"Invalid message body {amqp_msg.body!r}")
            await amqp_msg.reject(requeue=False)
            return

        async with amqp_msg.process(requeue=True):
            logger.debug(f"Processing inbound message {msg}")
            user_data = await self.redis.get(f"user.{msg.from_addr}", encoding="utf-8")
            user = User.get_or_create(msg.from_addr, user_data)
            app = Application(user)
            for outbound in await app.process_message(msg):
                await self.publish_message(outbound)
            for answer in app.answer_events:
                await self.publish_answer(answer)
            await self.redis.setex(f"user.{msg.from_addr}", config.TTL, user.to_json())

    async def publish_message(self, msg: Message):
        await self.exchange.publish(
            AMQPMessage(
                msg.to_json().encode("utf-8"),
                delivery_mode=DeliveryMode.PERSISTENT,
                content_type="application/json",
                content_encoding="UTF-8",
            ),
            routing_key=f"{config.TRANSPORT_NAME}.outbound",
        )

    async def publish_answer(self, answer: Answer):
        await self.exchange.publish(
            AMQPMessage(
                answer.to_json().encode("utf-8"),
                delivery_mode=DeliveryMode.PERSISTENT,
                content_type="application/json",
                content_encoding="UTF-8",
            ),
            routing_key=f"{config.TRANSPORT_NAME}.answer",
        )

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
