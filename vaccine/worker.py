import asyncio
import importlib
import logging
from json import JSONDecodeError
from typing import Callable
from urllib.parse import urljoin

import aiohttp
import redis.asyncio as aioredis
import sentry_sdk
from aio_pika import Connection, ExchangeType, IncomingMessage, connect_robust
from aio_pika import Message as AMQPMessage
from aio_pika.message import DeliveryMode
from redis.exceptions import LockNotOwnedError

from vaccine import config
from vaccine.models import Answer, Event, Message, User
from vaccine.utils import DECODE_MESSAGE_EXCEPTIONS, HTTP_EXCEPTIONS, log_timing

logging.basicConfig(level=config.LOG_LEVEL.upper())
logger = logging.getLogger(__name__)


class Worker:
    def __init__(self):
        modname, clsname = config.APPLICATION_CLASS.rsplit(".", maxsplit=1)
        module = importlib.import_module(modname)
        self.ApplicationClass = getattr(module, clsname)

    async def setup(self):
        self.connection = await connect_robust(config.AMQP_URL)
        self.channel = await self.connection.channel()
        await self.channel.set_qos(prefetch_count=config.CONCURRENCY)
        self.exchange = await self.channel.declare_exchange(
            "vumi", type=ExchangeType.DIRECT, durable=True, auto_delete=False
        )

        self.redis = aioredis.from_url(
            config.REDIS_URL, encoding="utf-8", decode_responses=True
        )

        self.inbound_queue = await self.setup_consume(
            f"{config.TRANSPORT_NAME}.inbound", self.process_message
        )
        self.event_queue = await self.setup_consume(
            f"{config.TRANSPORT_NAME}.event", self.process_event
        )

        if (
            config.ANSWER_API_URL
            and config.ANSWER_API_TOKEN
            and config.ANSWER_RESOURCE_ID
        ):
            self.answer_worker = AnswerWorker(
                connection=self.connection,
                url=config.ANSWER_API_URL,
                token=config.ANSWER_API_TOKEN,
                resource_id=config.ANSWER_RESOURCE_ID,
            )
            await self.answer_worker.setup()
        else:
            self.answer_worker = None

    async def setup_consume(self, routing_key: str, callback: Callable):
        queue = await self.channel.declare_queue(
            routing_key, durable=True, auto_delete=False
        )
        await queue.bind(self.exchange, routing_key)
        await queue.consume(callback)
        return queue

    async def teardown(self):
        await self.connection.close()
        await self.redis.close()
        if self.answer_worker:
            await self.answer_worker.teardown()

    async def process_message(self, amqp_msg: IncomingMessage):
        try:
            msg = Message.from_json(amqp_msg.body.decode("utf-8"))
        except DECODE_MESSAGE_EXCEPTIONS:
            logger.exception(f"Invalid message body {amqp_msg.body!r}")
            amqp_msg.reject(requeue=False)
            return

        msg_id = msg.message_id
        async with amqp_msg.process(requeue=True):
            try:
                async with self.redis.lock(
                    f"userlock.{msg.from_addr}", timeout=config.USER_LOCK_TIMEOUT
                ):
                    logger.debug(f"Processing inbound message {msg}")

                    async with log_timing(f"{msg_id} Got user", logger):
                        user_data = await self.redis.get(f"user.{msg.from_addr}")
                        user = User.get_or_create(msg.from_addr, user_data)
                    async with log_timing(f"{msg_id} Processed message", logger):
                        app = self.ApplicationClass(user, self)
                        messages = await app.process_message(msg)
                    async with log_timing(f"{msg_id} Published responses", logger):
                        for outbound in messages:
                            await self.publish_message(outbound)
                    async with log_timing(f"{msg_id} Published answers", logger):
                        if self.answer_worker:
                            for answer in app.answer_events:
                                await self.publish_answer(answer)
                    async with log_timing(f"{msg_id} Saved user", logger):
                        await self.redis.setex(
                            f"user.{msg.from_addr}", config.TTL, user.to_json()
                        )
            except LockNotOwnedError:
                # There's nothing we can do if a lock is no longer owned when we're
                # done processing, so log it and carry on
                logger.exception("")

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
        except DECODE_MESSAGE_EXCEPTIONS:
            logger.exception(f"Invalid event body {amqp_msg.body!r}")
            amqp_msg.reject(requeue=False)
            return

        async with amqp_msg.process(requeue=True):
            logger.debug(f"Processing event {event}")


class AnswerWorker:
    def __init__(self, connection: Connection, url: str, token: str, resource_id: str):
        self.connection = connection
        self.answers: list[IncomingMessage] = []
        self.session = aiohttp.ClientSession(
            raise_for_status=False,
            timeout=aiohttp.ClientTimeout(total=10),
            connector=aiohttp.TCPConnector(limit=1),
            headers={
                "Authorization": f"Token {token}",
                "Content-Type": "application/vnd.api+json",
            },
        )
        self.url = url
        self.token = token
        self.resource_id = resource_id

    async def setup(self):
        self.channel = await self.connection.channel()
        await self.channel.set_qos(prefetch_count=config.ANSWER_BATCH_SIZE)
        self.exchange = await self.channel.declare_exchange(
            "vumi", type=ExchangeType.DIRECT, durable=True, auto_delete=False
        )
        self.answer_queue = await self.setup_consume(
            f"{config.TRANSPORT_NAME}.answer", self.process_answer
        )
        self.periodic_task = asyncio.create_task(self._periodic_loop())

    async def setup_consume(self, routing_key: str, callback: Callable):
        queue = await self.channel.declare_queue(
            routing_key, durable=True, auto_delete=False
        )
        await queue.bind(self.exchange, routing_key)
        await queue.consume(callback)
        return queue

    async def teardown(self):
        self.periodic_task.cancel()
        await self.channel.close()

    async def process_answer(self, amqp_msg: IncomingMessage):
        try:
            Answer.from_json(amqp_msg.body.decode("utf-8"))
        except DECODE_MESSAGE_EXCEPTIONS:
            logger.exception(f"Invalid answer body {amqp_msg.body!r}")
            amqp_msg.reject(requeue=False)
            return
        self.answers.append(amqp_msg)

    async def _periodic_loop(self):
        while True:
            await asyncio.sleep(config.ANSWER_BATCH_TIME)
            await self._push_results()

    async def _submit_answers(
        self, answers: list[Answer]
    ) -> aiohttp.client.ClientResponse:
        data = {
            "data": {
                "type": "responses",
                "id": self.resource_id,
                "attributes": {
                    "responses": [
                        [
                            a.timestamp.isoformat(),
                            a.row_id,
                            a.address,
                            a.session_id,
                            a.question,
                            a.response,
                            a.response_metadata,
                        ]
                        for a in answers
                    ]
                },
            }
        }
        response = await self.session.post(
            url=urljoin(
                self.url, f"flow-results/packages/{self.resource_id}/responses/"
            ),
            json=data,
        )
        response_data = await response.text()
        sentry_sdk.set_context(
            "answer_api", {"request_data": data, "response_data": response_data}
        )
        return response

    async def _push_results(self):
        msgs, self.answers = self.answers, []
        answers: list[Answer] = []
        processed = []
        for msg in msgs:
            answers.append(Answer.from_json(msg.body.decode("utf-8")))
        if not answers:
            return
        try:
            response = await self._submit_answers(answers)
            # If there is a 400 response, then we send one by one to figure out which
            # answer has an issue, and nack it
            if response.status == 400:
                for msg in msgs:
                    answer = Answer.from_json(msg.body.decode("utf-8"))
                    response = await self._submit_answers([answer])
                    if response.status == 400:
                        # If this is a duplicate submission, then ignore error
                        try:
                            response_body = await response.json()
                            if (
                                response_body["data"]["attributes"]["responses"][0]
                                == "row_id is not unique for flow question"
                            ):
                                msg.ack()
                                processed.append(msg)
                                continue
                        except (TypeError, KeyError, IndexError, JSONDecodeError):
                            pass
                        msg.nack(requeue=False)
                        processed.append(msg)
                    response.raise_for_status()
                    msg.ack()
                    processed.append(msg)
            else:
                response.raise_for_status()
                for m in msgs:
                    m.ack()
        except HTTP_EXCEPTIONS:
            logger.exception("Error sending results to flow results server")
            self.answers.extend(m for m in msgs if m not in processed)
            return


if __name__ == "__main__":  # pragma: no cover
    worker = Worker()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(worker.setup())
    logger.info("Worker running")
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        loop.run_until_complete(worker.teardown())
