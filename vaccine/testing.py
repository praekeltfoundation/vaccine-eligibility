import socket
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Any, Callable, List, Optional, Type

from aio_pika import IncomingMessage
from sanic import Sanic
from sanic.server import AsyncioServer

from vaccine.base_application import BaseApplication
from vaccine.models import Answer, Message, User
from vaccine.worker import Worker


class AppTester:
    DEFAULT_USER_ADDRESS = "27820001001"
    DEFAULT_CHANNEL_ADDRESS = "27820001002"
    DEFAULT_TRANSPORT_NAME = "test_transport"
    DEFAULT_TRANSPORT_TYPE = Message.TRANSPORT_TYPE.HTTP_API
    DEFAULT_SESSION_ID = 1

    def __init__(self, app_class: Type[BaseApplication]):
        self.user = User(addr=self.DEFAULT_USER_ADDRESS)
        self.fake_worker = FakeWorker()
        self.application = app_class(self.user, self.fake_worker)

    def setup_state(self, name: str):
        """
        Sets the current state that the user is in
        """
        self.user.state.name = name

    def setup_answer(self, answer_name: str, answer_value: str):
        """
        Sets an answer for the user
        """
        self.user.answers[answer_name] = answer_value

    def setup_user_address(self, address: str):
        """
        Sets an address for the user
        """
        self.user.addr = address

    async def user_input(
        self,
        content: Optional[str] = None,
        session=Message.SESSION_EVENT.RESUME,
        transport_metadata: Optional[dict] = None,
    ):
        """
        User input into the application
        """
        self.application.messages = []
        message = Message(
            to_addr=self.DEFAULT_CHANNEL_ADDRESS,
            from_addr=self.user.addr,
            transport_name=self.DEFAULT_TRANSPORT_NAME,
            transport_type=self.DEFAULT_TRANSPORT_TYPE,
            content=content,
            session_event=session,
            transport_metadata=transport_metadata or {},
        )
        if session in (Message.SESSION_EVENT.RESUME, Message.SESSION_EVENT.CLOSE):
            self.user.session_id = self.DEFAULT_SESSION_ID
        await self.application.process_message(message)

    def assert_state(self, name: Optional[str]):
        """
        Asserts that the current user state matches `name`
        """
        assert (
            self.user.state.name == name
        ), f"User is in state {self.user.state.name}, not in {name}"

    def assert_answer(self, answer_name: str, answer_value: str):
        """
        Assert that a user's answer matches the given value
        """
        assert answer_name in self.user.answers, f"{answer_name} not in user answers"
        assert (
            self.user.answers[answer_name] == answer_value
        ), f"{answer_name} is {self.user.answers[answer_name]}, not {answer_value}"

    def assert_no_answer(self, answer_name: str):
        """
        Assert that the user does not have a value stored for the answer
        """
        assert (
            self.user.answers.get(answer_name) is None
        ), f"{answer_name} has a value {self.user.answers[answer_name]}"

    def assert_metadata(self, metadata_name: str, metadata_value: Any):
        """
        Assert that a user's metadata matches the given value
        """
        assert (
            metadata_name in self.user.metadata
        ), f"{metadata_name} not in user metadata"

        actual_value = self.user.metadata[metadata_name]
        assert (
            self.user.metadata[metadata_name] == metadata_value
        ), f"{metadata_name} is {actual_value}, not {metadata_value}"

    def assert_num_messages(self, num: int):
        """
        Assert that the application sent a specific number of messages. Useful for if
        we don't want to test the content of the messages
        """
        assert (
            len(self.application.messages) == num
        ), f"{len(self.application.messages)} messages sent, not {num}"

    def assert_message(
        self,
        content: Optional[str] = None,
        session: Optional[Message.SESSION_EVENT] = None,
        buttons: Optional[List[str]] = None,
        button: Optional[str] = None,
        list_items: Optional[List[str]] = None,
        header: Optional[str] = None,
        max_length: Optional[int] = None,
    ):
        """
        Asserts that the application sent a single message, with the provided parameters
        """
        self.assert_num_messages(1)
        [message] = self.application.messages
        if content is not None:
            assert (
                message.content == content
            ), f"Message content is {message.content}, not {content}"
        if session is not None:
            assert (
                message.session_event == session
            ), f"Message session is {message.session_event}, not {session}"
        if buttons is not None:
            btns = message.helper_metadata.get("buttons")
            assert btns == buttons, f"Buttons are {btns}, not {buttons}"
        if button is not None:
            btn = message.helper_metadata.get("button")
            assert btn == button, f"Button is {btn}, not {button}"
        if list_items is not None:
            items = message.helper_metadata.get("sections", [])
            assert items != [], "No list sections found"
            labels = [i["id"] for i in items[0].get("rows", [])]
            assert labels == list_items, f"List Items are {labels}, not {list_items}"
        if header is not None:
            hdr = message.helper_metadata.get("header")
            assert hdr == header, f"Header is {hdr}, not {header}"
        if max_length is not None:
            assert (
                len(str(message.content)) <= max_length
            ), f"Message length is over {max_length}"


class FakeWorker(Worker):
    def __init__(self):
        self.inbound_messages: List[IncomingMessage] = []
        self.outbound_messages: List[Message] = []
        self.events: List[IncomingMessage] = []
        self.answers: List[Answer] = []

    async def setup(self):
        pass

    async def setup_consume(self, routing_key: str, callback: Callable):
        pass

    async def teardown(self):
        pass

    async def process_message(self, amqp_msg: IncomingMessage):
        self.inbound_messages.append(amqp_msg)

    async def publish_message(self, msg: Message):
        self.outbound_messages.append(msg)

    async def publish_answer(self, answer: Answer):
        self.answers.append(answer)

    async def process_event(self, amqp_msg: IncomingMessage):
        self.events.append(amqp_msg)


@dataclass
class TState:
    requests: list = field(default_factory=list)
    errors: int = 0
    errormax: int = 0
    banner: bool = False


def unused_port():
    """
    Find an unused port by temporarily binding a socket to it.

    Unfortunately, Sanic.create_server() replaces port 0 with its default port
    8080. If we want to bind to an arbitrary unused port, we need to find an
    unused one to pass in explicitly. This potentially has a race condition in
    it, so let's hope we don't hit that.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@dataclass
class MockServer:
    app: Sanic
    server: AsyncioServer
    host: str
    port: int
    tstate: Optional[TState] = None


@asynccontextmanager
async def run_sanic(app):
    """
    Run a sanic app as a context manager. Best used in pytest fixtures.
    """
    Sanic.test_mode = True
    port = unused_port()
    server = await app.create_server(return_asyncio_server=True, port=port)
    if hasattr(server, "startup"):
        # This was introduced between 21.6 and 21.12
        await server.startup()
    await server.start_serving()
    [sock] = server.server.sockets
    host, port = sock.getsockname()
    yield MockServer(app, server, host, port)
    await server.close()
